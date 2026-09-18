"""Release-time generator; never use to repair an installed integrity failure."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];version='v0.1.0-beta';files=[]
for p in sorted(root.rglob('*')):
    rel=p.relative_to(root).as_posix()
    if not p.is_file() or rel in {'manifest.json','SHA256SUMS.txt'} or any(x in {'.git','__pycache__','outputs'} for x in p.relative_to(root).parts):continue
    files.append(dict(relative_path=rel,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),file_type=p.suffix.lstrip('.') or 'text',critical=True,release_version=version))
m=dict(schema_version=1,release_version=version,files=files,required_directories=sorted({str(Path(e['relative_path']).parent).replace('\\','/') for e in files}-{'.'}))
(root/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
(root/'SHA256SUMS.txt').write_text(''.join(f"{e['sha256']}  {e['relative_path']}\n" for e in files)+hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()+'  manifest.json\n',encoding='utf-8')
