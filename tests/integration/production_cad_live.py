"""Read-only production-source acceptance using isolated CAD and SKP copies.

This tests native reference geometry; it does not promise CAD annotation or
Hatch semantics in SketchUp. No accepted Bridge core is changed.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import traceback

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import ezdxf
import numpy as np
from ezdxf import bbox
from landscape_agent_pack.bridge.client import RingoClient
from landscape_agent_pack.bridge.contracts import BridgeRequest
from landscape_agent_pack.bridge.validation import compare_persistence
from landscape_agent_pack.cad.core import connect,DocumentSession
from landscape_agent_pack.cad.geometry_qa import analyze_dxf,GeometryProfile
from landscape_agent_pack.cad.plot import PlotRequest,plot_pdf
from landscape_agent_pack.cad.pdf_qa import inspect_pdf,PDFProfile
from landscape_agent_pack.result import Result


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def samples(entity):
    kind=entity.dxftype()
    if kind=='LINE':
        a=np.array(entity.dxf.start); b=np.array(entity.dxf.end)
        return [tuple(a+(b-a)*t) for t in (0,.25,.5,.75,1)]
    if kind in {'CIRCLE','ARC'}:
        if kind=='CIRCLE': start,end=0,360
        else:
            start,end=entity.dxf.start_angle,entity.dxf.end_angle
            end=start+(end-start)%360
        ocs=entity.ocs(); c=entity.dxf.center; r=entity.dxf.radius
        # Fixed dense sampling is reported as sampling, never a global bound.
        return [tuple(ocs.to_wcs((c.x+r*math.cos(t),c.y+r*math.sin(t),c.z)))
                for t in np.linspace(math.radians(start),math.radians(end),97)]
    return []


def source_geometry(doc):
    rows=[]; omitted=[]; widths=[]
    def expand(entity,identity,depth=0):
        if depth>16: raise ValueError('CAD block nesting exceeds 16')
        kind=entity.dxftype()
        if kind=='INSERT':
            for i,child in enumerate(entity.virtual_entities()): expand(child,identity+'/'+str(i),depth+1)
        elif kind=='LWPOLYLINE':
            if entity.dxf.const_width or any(v[2] or v[3] for v in entity.get_points('xyseb')):
                widths.append({'handle':identity,'width':entity.dxf.const_width,'layer':entity.dxf.layer})
            for i,child in enumerate(entity.virtual_entities()): expand(child,identity+'/'+str(i),depth+1)
        elif kind in {'LINE','CIRCLE','ARC'}:
            rows.append({'handle':identity,'type':kind,'layer':entity.dxf.layer,'points':samples(entity)})
        else:
            omitted.append({'handle':identity,'type':kind,'layer':entity.dxf.layer})
    for entity in doc.modelspace(): expand(entity,str(entity.dxf.handle))
    return rows,omitted,widths


def measure_geometry(snapshot,rows,tolerance=1.0):
    a=np.array([e['a'] for e in snapshot['edges']],dtype=float)
    b=np.array([e['b'] for e in snapshot['edges']],dtype=float)
    if not len(a): raise ValueError('Native imported reference has no edges')
    vector=b-a; squared=np.sum(vector*vector,axis=1)
    records=[]
    for row in rows:
        distances=[]
        for p in row['points']:
            point=np.array(p)
            t=np.clip(np.sum((point-a)*vector,axis=1)/np.maximum(squared,1e-30),0,1)
            distances.append(float(np.sqrt(np.min(np.sum((a+t[:,None]*vector-point)**2,axis=1)))))
        error=max(distances)
        records.append({k:row[k] for k in ('handle','type','layer')} | {'sample_count':len(distances),'maximum_distance_mm':error,
                       'status':'SUPPORTED' if error<=tolerance else 'PARTIALLY_SUPPORTED'})
    return {'method':'One-way source samples to all native world-space edge segments',
            'limitation':'Overlapping edges can cover a missing coincident entity; not entity bijection, topology or a global Hausdorff proof',
            'tolerance_mm':tolerance,'sample_count':sum(r['sample_count'] for r in records),
            'maximum_sample_distance_mm':max(r['maximum_distance_mm'] for r in records),
            'outside_tolerance':[r for r in records if r['status']!='SUPPORTED'],'records':records}


def measure_widths(snapshot,doc):
    """Test contour conversion, preserving raw centerline mismatch evidence."""
    a=np.array([e['a'] for e in snapshot['edges']],dtype=float)
    b=np.array([e['b'] for e in snapshot['edges']],dtype=float)
    vector=b-a; length2=np.sum(vector*vector,axis=1)
    def distance(point):
        t=np.clip(np.sum((point-a)*vector,axis=1)/np.maximum(length2,1e-30),0,1)
        return float(np.sqrt(np.min(np.sum((a+t[:,None]*vector-point)**2,axis=1))))
    records=[]
    for entity in doc.modelspace().query('LWPOLYLINE'):
        width=entity.dxf.const_width
        if not width: continue
        errors=[]; unsupported=False
        for child in entity.virtual_entities():
            if child.dxftype()!='LINE': unsupported=True; continue
            start=np.array(child.dxf.start); end=np.array(child.dxf.end); v=end-start
            norm=np.array([-v[1],v[0],0]); magnitude=np.linalg.norm(norm)
            if not magnitude: unsupported=True; continue
            norm/=magnitude
            for t in (.25,.5,.75):
                for sign in (-1,1): errors.append(distance(start+t*v+sign*width*.5*norm))
        records.append({'handle':entity.dxf.handle,'width_mm':width,'half_width_mm':width/2,
                        'boundary_samples':len(errors),'maximum_boundary_error_mm':max(errors) if errors else None,
                        'status':'PARTIALLY_SUPPORTED' if errors and not unsupported and max(errors)<=.1 else 'UNSUPPORTED'})
    return records


def run(workspace,template,config=None):
    run=Path(workspace).resolve(strict=True)
    audit=json.loads((run/'source-audit.json').read_text(encoding='utf-8'))
    source=Path(audit['source']); original=sha(source)
    if original != audit['source_sha256'] or sha(run/'source.dwg') != original:
        raise ValueError('Production input differs from frozen source audit')
    result=Result(run.name,'Production CAD native reference acceptance',input=audit)
    client=RingoClient(config,timeout=60)
    session=None
    def literal(path): return json.dumps(str(path).replace('\\','/'),ensure_ascii=False)
    def ruby(code,mutation=False,transaction=None):
        info=client.data('model.get_info')
        return client.ruby(code,model_id=info['model_id'],mutation=mutation,transaction=transaction)
    def check(id,value,status='PASS'): result.add(id,id,True,status,actual=value)
    try:
        dxf=ezdxf.readfile(run/'source.dxf')
        rows,omitted,widths=source_geometry(dxf)
        box=bbox.extents(dxf.modelspace())
        profile=GeometryProfile(expected_entity_count=audit['snapshot']['entities'],
            allowed_bbox=(box.extmin.x-.01,box.extmin.y-.01,box.extmax.x+.01,box.extmax.y+.01))
        qa=analyze_dxf(run/'source.dxf',profile,task_id=run.name)
        qa.write(run/'geometry-qa.json',run/'geometry-qa.md')
        # Preserve any source QA defect, still inspect import/persistence to localize it.
        check('SOURCE_GEOMETRY_QA',qa.to_dict(),'PASS' if qa.exit_code==0 else 'FAIL')
        app=connect(); session=DocumentSession.open(app,run/'source.dwg',workspace_root=run)
        check('DWG_DISK_REOPEN',session.snapshot())
        plot=plot_pdf(session,PlotRequest(str(run/'production.pdf'),paper='A2',area='extents'))
        plot.write(run/'plot.json',run/'plot.md')
        check('PDF_PLOT',plot.to_dict(),'PASS' if plot.exit_code==0 else 'FAIL')
        pdf=inspect_pdf(run/'production.pdf',PDFProfile('A2','landscape',require_vectors=True))
        pdf.write(run/'pdf-qa.json',run/'pdf-qa.md')
        check('PDF_QA',pdf.to_dict(),'PASS' if pdf.exit_code==0 else 'FAIL')
        session.save_as(run/'plot-settings-copy.dwg',format='dwg'); session.close(); session=None
        shutil.copy2(template,run/'startup.skp')
        info=client.data('model.get_info')
        if info['modified'] or '/runs/' not in info['path'].replace('\\','/'):
            raise ValueError('Current SU is not a clean owned test model')
        ruby('Sketchup.open_file('+literal(run/'startup.skp')+')',True,False)
        req=BridgeRequest(str(run),str(run/'source.dwg'),'dwg','mm',4,'mm',str(run/'startup.skp'),str(run/'production.skp'),original).validate()
        request_file=run/'request.json'
        with request_file.open('x',encoding='utf-8') as f: json.dump(req.to_dict(),f,ensure_ascii=False,indent=2)
        for module in ('native_import.rb','sketchup_session.rb','persistence.rb'):
            ruby('load '+literal(ROOT/'landscape_agent_pack/bridge'/module))
        check('BRIDGE_IDENTITY',client.call('bridge.status')['instance'])
        check('NATIVE_IMPORT',ruby('LandscapeAgentPack::NativeImport.run('+literal(request_file)+')',True))
        check('SNAPSHOT_BEFORE',ruby('LandscapeAgentPack::SketchupSession.write_snapshot('+literal(run/'before.json')+')'))
        before=json.loads((run/'before.json').read_text(encoding='utf-8'))
        check('SU_UNITS',before['model_units_code'],'PASS' if before['model_units_code']==2 else 'FAIL')
        measured=measure_geometry(before,rows)
        width_records=measure_widths(before,dxf)
        wide_handles={r['handle'] for r in width_records}
        ordinary_outliers=[r for r in measured['outside_tolerance'] if r['handle'].split('/')[0] not in wide_handles]
        measured['width_contour_diagnostic']=width_records
        measured['annotation_or_other_unsupported']=omitted
        measured['wide_polyline_semantics_partial']=widths
        (run/'geometry-comparison.json').write_text(json.dumps(measured,ensure_ascii=False,indent=2),encoding='utf-8')
        check('COORDINATE_SAMPLES',{'samples':measured['sample_count'],'max_mm':measured['maximum_sample_distance_mm'],
                                 'outside_tolerance':measured['outside_tolerance']},
              'FAIL' if ordinary_outliers else ('WARN' if measured['outside_tolerance'] else 'PASS'))
        if width_records:
            check('WIDTH_CONTOURS',width_records,'FAIL' if any(r['status']=='UNSUPPORTED' for r in width_records) else 'WARN')
        if omitted or widths:
            result.add('ENTITY_SUPPORT','Annotation/width semantics',True,'WARN',actual={'omitted':dict(Counter(e['type'] for e in omitted)),'wide_polylines':len(widths)})
        check('SAVE',ruby('LandscapeAgentPack::Persistence.save('+literal(run/'startup.skp')+','+literal(run/'production.skp')+')',True,False))
        check('CLOSE',ruby('LandscapeAgentPack::Persistence.close_saved('+literal(run/'production.skp')+')',True,False))
        check('REOPEN',ruby('LandscapeAgentPack::Persistence.reopen('+literal(run/'production.skp')+')',True,False))
        check('SNAPSHOT_AFTER',ruby('LandscapeAgentPack::SketchupSession.write_snapshot('+literal(run/'after.json')+','+literal(run/'production.skp')+')'))
        after=json.loads((run/'after.json').read_text(encoding='utf-8'))
        check('PERSISTENCE',compare_persistence(before,after))
        ruby('load '+literal(Path(__file__).parent/'production_types.rb'))
        check('SU_ENTITY_TYPES',ruby('LAPProductionTypes.write('+literal(run/'su-types.json')+')'))
        check('SOURCE_HASH_UNCHANGED',sha(source),'PASS' if sha(source)==original else 'FAIL')
        # Explicit top/axon views, without changing saved CAD or design geometry.
        for name,eye,up in [('top',[0,0,100000],[0,1,0]),('axon',[80000,-100000,130000],[0,0,1])]:
            ruby("m=Sketchup.active_model; b=m.bounds; c=b.center; m.active_view.camera=Sketchup::Camera.new(c+Geom::Vector3d.new("+','.join(map(str,eye))+"),c,Geom::Vector3d.new("+','.join(map(str,up))+"),false); m.active_view.zoom_extents; true")
            info=client.data('model.get_info')
            client.data('view.export',{'path':str(run/(name+'.png')),'width':1800,'height':1200,'model_id':info['model_id']},mutation=True)
        import pymupdf
        with pymupdf.open(run/'production.pdf') as pdfdoc:
            pdfdoc[0].get_pixmap(matrix=pymupdf.Matrix(2,2)).save(str(run/'pdf.png'))
        result.output={'skp':str(run/'production.skp'),'skp_sha256':sha(run/'production.skp'),'native_edges':after['edge_count'],
                       'bbox_mm':after['bbox_mm'],'source_expanded_geometry':dict(Counter(r['type'] for r in rows))}
    except Exception as exc:
        check('STOPPED',str(exc),'FAIL'); result.errors.append(str(exc))
        (run/'traceback.txt').write_text(traceback.format_exc(),encoding='utf-8')
    finally:
        (run/'rpc-history.json').write_text(json.dumps(client.history,indent=2),encoding='utf-8')
        client.close()
        if session is not None: result.warnings.append('Owned CAD document remains open for inspection')
        result.write(run/'production-result.json',run/'production-result.md')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('workspace',type=Path); p.add_argument('template',type=Path); p.add_argument('--config',type=Path)
    args=p.parse_args(); r=run(args.workspace,args.template,args.config)
    print(json.dumps({'status':r.status,'errors':r.errors,'output':r.output},ensure_ascii=False))
    raise SystemExit(r.exit_code)
