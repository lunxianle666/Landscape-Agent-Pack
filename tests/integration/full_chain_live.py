"""Single source: real CAD build/reopen -> geometry QA -> PDF -> SU persistence."""
import argparse
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path(__file__).parent))
from bridge_fixture_cad import build
from bridge_live import run as bridge_run
from landscape_agent_pack.cad.core import connect, DocumentSession
from landscape_agent_pack.cad.geometry_qa import GeometryProfile, analyze_dxf
from landscape_agent_pack.cad.plot import PlotRequest, plot_pdf
from landscape_agent_pack.cad.pdf_qa import PDFProfile, inspect_pdf
from landscape_agent_pack.bridge.client import RingoClient
from landscape_agent_pack.result import Result


def main(startup,config=None):
    run=ROOT/'runs'/('全链路-'+uuid.uuid4().hex[:12])
    run.mkdir(parents=True, exist_ok=False)
    startup=Path(startup).resolve(strict=True)
    import shutil
    shutil.copy2(startup,run/'startup.skp')
    result=Result(run.name,'Single source full chain regression')
    session=None
    try:
        facts=build(run)
        result.add('CAD_BUILD','Real AutoCAD fixture',True,'PASS',actual=facts)
        app=connect()
        session=DocumentSession.open(app,facts['dwg'],workspace_root=run)
        snapshot=session.snapshot()
        if snapshot['entities'] != 8 or snapshot['insunits'] != 4:
            raise RuntimeError('DWG disk reopen differs')
        result.add('DWG_REOPEN','Disk DWG count and units',True,'PASS',actual=snapshot)
        geometry=analyze_dxf(facts['dxf'],GeometryProfile(expected_entity_count=8,required_layers=tuple(facts['layers']),closed_layers=('L-HARDSCAPE',)))
        geometry.write(run/'geometry-result.json',run/'geometry-result.md')
        result.add('CAD_QA','Geometry QA',True,'PASS' if geometry.exit_code == 0 else 'FAIL',actual=geometry.status)
        plot=plot_pdf(session,PlotRequest(str(run/'fixture.pdf'),paper='A4',area='extents'))
        plot.write(run/'plot-result.json',run/'plot-result.md')
        if plot.exit_code:
            raise RuntimeError('PDF plot failed')
        pdf=inspect_pdf(run/'fixture.pdf',PDFProfile('A4','landscape',require_vectors=True))
        pdf.write(run/'pdf-result.json',run/'pdf-result.md')
        if pdf.exit_code:
            raise RuntimeError('Objective PDF QA failed')
        result.add('PLOT_PDF','Actual AutoCAD PDF and QA',True,'PASS',actual=pdf.metrics)
        # Plot configuration is not persisted into the hashed input CAD.
        session.save_as(run/'plot-configured-copy.dwg',format='dwg')
        session.close()
        session=None
        client=RingoClient(config)
        try:
            info=client.data('model.get_info')
            if info['modified'] or '/runs/' not in info['path'].replace('\\','/'):
                raise RuntimeError('Current SU model is not an owned saved test model')
            path=json.dumps(str(run/'startup.skp').replace('\\','/'),ensure_ascii=False)
            client.ruby('Sketchup.open_file('+path+')',model_id=info['model_id'],mutation=True,transaction=False)
        finally:
            client.close()
        bridge=bridge_run(run,config)
        result.add('CAD_TO_SU','Native bridge save/reopen/readback',True,'PASS' if bridge.exit_code == 0 else 'FAIL',actual=bridge.to_dict())
        result.add('VISUAL_DESIGN_REVIEW','Formal visual design judgement outside fixture scope',False,'NOT_EXECUTED')
    except Exception as exc:
        result.add('STOPPED','Regression stopped',True,'FAIL',actual=str(exc))
        result.errors.append(str(exc))
    finally:
        if session is not None:
            result.warnings.append('Owned CAD document remains open for inspection')
        result.write(run/'full-chain-result.json',run/'full-chain-result.md')
    print(json.dumps({'status':result.status,'run':str(run),'errors':result.errors},ensure_ascii=False))
    return result.exit_code


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('startup',type=Path)
    parser.add_argument('--config',type=Path)
    args=parser.parse_args()
    raise SystemExit(main(args.startup,args.config))
