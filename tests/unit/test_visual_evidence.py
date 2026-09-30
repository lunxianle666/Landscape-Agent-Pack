import hashlib
import tempfile
import unittest
from pathlib import Path
from landscape_agent_pack.cad.visual_qa import visual_qa_reviewed


class VisualEvidenceTests(unittest.TestCase):
    def test_tampered_evidence_and_failed_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'reviewed.png'
            path.write_bytes(b'reviewed evidence')
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            row = {'artifact': str(path), 'image': str(path),
                   'artifact_sha256': digest, 'image_sha256': digest}
            args = dict(task_id='review', evidence=[row], reviewer='actual reviewer',
                        observations={'nonempty': True, 'no_clipping': False})
            self.assertEqual(visual_qa_reviewed(**args).status, 'FAIL')
            path.write_bytes(b'changed after inspection')
            with self.assertRaises(ValueError): visual_qa_reviewed(**args)

    def test_missing_review_cannot_pass(self):
        with self.assertRaises(ValueError):
            visual_qa_reviewed(task_id='missing', evidence=[], reviewer='', observations={})

    def test_warning_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'image'; path.write_bytes(b'evidence')
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            result = visual_qa_reviewed(task_id='partial', reviewer='actual reviewer',
                evidence=[{'artifact':str(path),'image':str(path),
                           'artifact_sha256':digest,'image_sha256':digest}],
                observations={'nonempty':True}, warnings=['Annotation loss'])
            self.assertEqual(result.output['visual_status'], 'VISUAL_PASS_WITH_WARNINGS')
