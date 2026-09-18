import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('verify',ROOT/'installer/verify-rules.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'中文 space';shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('outputs','__pycache__','.git'))
    def tearDown(self):self.tmp.cleanup()
    def test_clean(self):self.assertEqual(v.verify(self.root),[])
    def test_deleted(self):(self.root/'standards/autocad-safety-rules.md').unlink();self.assertTrue(v.verify(self.root))
    def test_one_character(self):
        p=self.root/'standards/autocad-safety-rules.md';b=p.read_bytes();p.write_bytes(bytes([b[0]^1])+b[1:]);self.assertTrue(v.verify(self.root))
    def test_empty(self):(self.root/'standards/autocad-safety-rules.md').write_bytes(b'');self.assertTrue(v.verify(self.root))
    def test_unrelated(self):(self.root/'unrelated.txt').write_text('extra');self.assertEqual(v.verify(self.root),[])
    def test_manifest_missing(self):(self.root/'manifest.json').unlink();self.assertTrue(v.verify(self.root))
    def test_manifest_corrupt(self):(self.root/'manifest.json').write_text('{');self.assertTrue(v.verify(self.root))
    def test_manifest_rule_omitted(self):
        p=self.root/'manifest.json';m=json.loads(p.read_text());m['files']=[e for e in m['files'] if e['relative_path']!='standards/autocad-safety-rules.md'];p.write_text(json.dumps(m));self.assertTrue(v.verify(self.root))
if __name__=='__main__':unittest.main()
