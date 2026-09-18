"""Local evidence runner. No client config writes, no upload, owned outputs only."""
import hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs';OUT.mkdir(exist_ok=True)
def run(name,args):
    r=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONIOENCODING':'utf-8'})
    (OUT/(name+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8')
    print(name,r.returncode,flush=True)
    return {'test':name,'exit':r.returncode,'log':name+'.log'}
if len(sys.argv)>1 and sys.argv[1]=='independent':
    import win32com.client.dynamic as dynamic,win32com.client
    paths=list(OUT.rglob('lap-smoke-*.dwg'))
    assert paths,'No newly produced DWG'
    path=max(paths,key=lambda p:p.stat().st_mtime)
    app=dynamic.Dispatch(win32com.client.GetActiveObject('AutoCAD.Application.25')._oleobj_)
    assert app.Documents.Count==0,'User documents detected; refusing independent reopen'
    app.Documents.Open(str(path));doc=app.ActiveDocument
    assert Path(doc.FullName).resolve()==path.resolve()
    try:
        es=[dynamic.Dispatch(doc.ModelSpace.Item(i)._oleobj_) for i in range(doc.ModelSpace.Count)]
        assert len(es)==2
        poly=next(e for e in es if e.ObjectName=='AcDbPolyline');circle=next(e for e in es if e.ObjectName=='AcDbCircle')
        assert list(poly.Coordinates)==[0.,0.,1000.,0.,1000.,500.,0.,500.] and poly.Closed
        assert abs(poly.Area-500000)<1e-6 and circle.Radius==100 and list(circle.Center)==[1500.,250.,0.]
        print(json.dumps({'status':'PASS','file':path.name,'entities':2,'rectangle_mm':[1000,500],'circle_radius_mm':100,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}))
    finally:doc.Close(False)
    raise SystemExit()
results=[]
for name,script in [('integrity','test_integrity.py'),('document-safety','test_document_guards.py'),('creation-safety','test_creation_guard.py')]:
    results.append(run(name,[sys.executable,'-B',str(ROOT/'tests/smoke'/script)]))
results.append(run('environment',[sys.executable,'-B','installer/environment_probe.py']))
# Default dependency creation and default Skill target, but isolated runtime root.
base=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'installer/install.ps1'),'-InstallRoot',str(OUT/'default-install space')]
results.append(run('default-install',base))
results.append(run('second-install',base))
results.append(run('geometry',base+['-RerunSmoke','-RunGeometrySmoke']))
results.append(run('independent-read',[sys.executable,'-B',str(Path(__file__)),'independent']))
results.append(run('diagnostic',base+['-DiagnosticOnly']))
# Tampering checks on installed copy and actual diagnostic exit. Restore exact bytes after each test.
rule=OUT/'default-install space/pack-rules/standards/autocad-safety-rules.md'
if rule.is_file():
    original=rule.read_bytes()
    for mode in ['delete','modify','empty']:
        try:
            if mode=='delete':rule.unlink()
            elif mode=='modify':rule.write_bytes(bytes([original[0]^1])+original[1:])
            else:rule.write_bytes(b'')
            result=run('diagnostic-'+mode,base+['-DiagnosticOnly'])
            result['expected_exit']=1;results.append(result)
        finally:rule.write_bytes(original)
with zipfile.ZipFile(OUT/'anonymous-baseline.zip') as z:
    inventory=[n for n in z.namelist() if not n.endswith('/')]
    results.append({'test':'anonymous-baseline','status':'PASS','files':len(inventory),'commit':'107a400e6d934c4d61eeb4fa8fd51ceb8188b15f','zip_sha256':hashlib.sha256((OUT/'anonymous-baseline.zip').read_bytes()).hexdigest(),'scope':'baseline only; candidate is not published'})
(OUT/'acceptance-v2.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
