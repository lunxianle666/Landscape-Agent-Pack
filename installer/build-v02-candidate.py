"""Deterministic manifest-only ZIP; no publication, no overwrite, independent QA."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main(destination):
    destination=Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    if manifest['release_version'] != 'v0.2.0-rc1':
        raise ValueError('Expected explicitly generated v0.2.0-rc1 manifest')
    spec=importlib.util.spec_from_file_location('verify',ROOT/'installer/verify-rules.py')
    verifier=importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
    errors=verifier.verify(ROOT)
    if errors:
        raise ValueError('\n'.join(errors))
    name='Landscape-Agent-Pack-'+manifest['release_version']
    archive=destination/(name+'.zip')
    paths=sorted([e['relative_path'] for e in manifest['files']]+['manifest.json','SHA256SUMS.txt'])
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as zipped:
        for rel in paths:
            entry=zipfile.ZipInfo(name+'/'+rel,date_time=(2026,9,30,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED
            entry.external_attr=0o100644 << 16
            zipped.writestr(entry,(ROOT/rel).read_bytes())
    with tempfile.TemporaryDirectory() as temp:
        with zipfile.ZipFile(archive) as zipped:
            if zipped.testzip() is not None:
                raise ValueError('ZIP CRC failure')
            zipped.extractall(temp)
        extracted=Path(temp)/name
        errors=verifier.verify(extracted)
        if errors:
            raise ValueError('\n'.join(errors))
        safety=extracted/'standards/autocad-safety-rules.md'
        original=safety.read_bytes()
        safety.write_bytes(original+b'\nchanged\n')
        if not verifier.verify(extracted):
            raise ValueError('Tampering was accepted')
        safety.write_bytes(original)
        safety.unlink()
        if not verifier.verify(extracted):
            raise ValueError('Missing critical file was accepted')
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    Path(str(archive)+'.sha256').write_text(digest+'  '+archive.name+'\n',encoding='ascii')
    evidence={'status':'PASS','version':manifest['release_version'],'files':len(paths),
              'sha256':digest,'extracted_integrity':'PASS','tamper':'REJECTED',
              'missing_critical':'REJECTED','publication':'NOT_PERFORMED'}
    (destination/'package-result.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(evidence))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('destination',type=Path)
    main(parser.parse_args().destination)
