"""Explicit release-time generator over tracked files; never repair an install."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def build(root, version):
    root=Path(root).resolve(strict=True)
    listed=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode('utf-8').split('\0')
    files=[]
    for rel in sorted(set(listed)-{'','manifest.json','SHA256SUMS.txt'}):
        path=root/rel
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError(f'Missing or unsafe tracked release file: {rel}')
        files.append({'relative_path':rel,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                      'file_type':path.suffix.lstrip('.') or 'text','critical':True,'release_version':version})
    manifest={'schema_version':1,'release_version':version,'files':files,
              'required_directories':sorted({Path(e['relative_path']).parent.as_posix() for e in files}-{'.'})}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (root/'SHA256SUMS.txt').write_text(''.join(f"{e['sha256']}  {e['relative_path']}\n" for e in files)+
                                    hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()+'  manifest.json\n',encoding='utf-8')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--version',required=True)
    args=parser.parse_args()
    manifest=build(args.root,args.version)
    print(json.dumps({'version':args.version,'files':len(manifest['files'])}))
