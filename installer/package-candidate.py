"""Package only manifest-listed files; independently extract and validate."""
import hashlib,importlib.util,json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'outputs';out.mkdir(exist_ok=True)
m=json.loads((root/'manifest.json').read_text());name='Landscape-Agent-Pack-'+m['release_version'];dest=out/(name+'.zip')
spec=importlib.util.spec_from_file_location('verify',root/'installer/verify-rules.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
source_fail=v.verify(root)
if source_fail:raise SystemExit('\n'.join(source_fail))
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for rel in [e['relative_path'] for e in m['files']]+['manifest.json','SHA256SUMS.txt']:
        z.write(root/rel,name+'/'+rel)
extract=out/'candidate-extracted'
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    z.extractall(extract)
fail=v.verify(extract/name)
evidence={'status':'FAIL' if fail else 'PASS','zip_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'manifest_files':len(m['files']),'zip_files':len(m['files'])+2,'errors':fail}
(out/'candidate-package.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
Path(str(dest)+'.sha256').write_text(evidence['zip_sha256']+'  '+dest.name+'\n',encoding='ascii')
print(json.dumps(evidence));raise SystemExit(bool(fail))
