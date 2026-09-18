"""Fail-closed manifest validation. Read-only; never regenerate on failure."""
import argparse, hashlib, json, re
from pathlib import Path, PurePosixPath
RULES = {'AGENT_CONTEXT.md','standards/landscape-workflow.md','standards/autocad-safety-rules.md','guards/README.md','docs/LIMITATIONS.md','docs/THREE_STEP_CHECK_CN.md'}

def verify(root, packed=False):
    root = Path(root).resolve()
    failures = []
    try:
        m = json.loads((root/'manifest.json').read_text(encoding='utf-8-sig'))
        assert m['schema_version'] == 1 and m['release_version']
        assert isinstance(m['files'],list) and m['files']
        seen = set()
        for e in m['files']:
            rel = e['relative_path']; p = PurePosixPath(rel)
            assert rel and '\\' not in rel and not p.is_absolute() and '..' not in p.parts and ':' not in rel and rel not in seen
            assert re.fullmatch('[0-9a-fA-F]{64}',e['sha256'])
            assert isinstance(e['critical'],bool) and e['file_type'] and e['release_version']==m['release_version']
            seen.add(rel)
        required = RULES if packed else RULES | {'installer/install.ps1','installer/verify-rules.py','skills/sketchup-from-cad-landscape/SKILL.md','config/codex.toml.example','config/trae-mcp.json.example'}
        assert required <= {e['relative_path'] for e in m['files'] if e['critical']}, 'mandatory critical entries absent'
        assert isinstance(m['required_directories'],list)
        parents={str(PurePosixPath(e['relative_path']).parent) for e in m['files']} - {'.'}
        assert parents <= set(m['required_directories']), 'required directory inventory incomplete'
        for rel in m['required_directories']:
            p = PurePosixPath(rel)
            assert rel and not p.is_absolute() and '..' not in p.parts and ':' not in rel
            if not (root/rel).is_dir(): failures.append(rel+': required directory missing')
    except (OSError,ValueError,KeyError,TypeError,AssertionError) as ex:
        return ['manifest.json: missing or invalid manifest: '+str(ex)]
    for e in m['files']:
        rel=e['relative_path']; path=root/rel
        try:
            if path.is_symlink() or not path.resolve().is_relative_to(root): raise ValueError('linked/escaped file')
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if digest.lower()!=e['sha256'].lower(): failures.append(f'{rel}: SHA-256 mismatch; expected {e["sha256"]}; actual {digest}')
        except (OSError,ValueError) as ex: failures.append(rel+': missing/unreadable: '+str(ex))
    return failures

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--packed',action='store_true');a=p.parse_args()
    failures=verify(a.root,a.packed)
    for f in failures: print('FAIL: '+f)
    print('FINAL: '+('FAIL' if failures else 'PASS'))
    raise SystemExit(bool(failures))
