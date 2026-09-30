"""Exercise the real fixture entry and cleanup with isolated document doubles."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'integration'))
import bridge_fixture_cad as fixture
from landscape_agent_pack.cad.core import OwnershipError


class Document:
    def __init__(self, app, name='Drawing1.dwg', path='', paperspace=0):
        self.app = app
        self.Name, self.FullName = name, path
        self.ModelSpace = type('Space', (), {'Count': 0})()
        self.PaperSpace = type('Space', (), {'Count': paperspace})()
        self._oleobj_ = object()
        self.close_calls = []
        self.dirty = False

    def Close(self, save):
        self.close_calls.append(save)
        self.app.Documents.items.remove(self)


class Documents:
    def __init__(self): self.items = []
    @property
    def Count(self): return len(self.items)
    def Item(self, index): return self.items[index]


class App:
    def __init__(self):
        self.Documents = Documents()
        self.ActiveDocument = None

    def add(self, **kwargs):
        doc = Document(self, **kwargs)
        self.Documents.items.append(doc)
        self.ActiveDocument = doc
        return doc


class Session:
    def __init__(self, app, doc):
        self.app, self.document_object = app, doc
        self.opened_by_automation = True
        self.dirty = False
        self.operations = []

    def refresh(self):
        if self.app.ActiveDocument is not self.document_object:
            raise OwnershipError('Active document switched')
        self.dirty = self.document_object.dirty

    def save_as(self, path, *, format):
        self.operations.append('save-' + format)
        self.document_object.Name = Path(path).name
        self.document_object.FullName = str(path)
        self.document_object.dirty = False

    def close(self):
        self.refresh()
        self.document_object.Close(False)
        self.opened_by_automation = False
        self.operations.append('close')


class FixtureOwnershipTests(unittest.TestCase):
    def blocked_build(self, **kwargs):
        app = App(); old = app.add(**kwargs)
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(fixture, 'connect', return_value=app) as connect, \
                 patch.object(fixture.DocumentSession, 'create') as create:
                with self.assertRaises(OwnershipError): fixture.build(Path(directory))
                connect.assert_called_once_with(allow_launch=True)
                create.assert_not_called()
            audit = json.loads((Path(directory)/'ownership-audit.json').read_text())
            self.assertTrue(audit['baseline_survived'])
            self.assertFalse(audit['creation_recorded'])
        self.assertEqual(old.close_calls, [])
        self.assertIs(app.Documents.Item(0), old)

    def test_A_existing_paperspace_document_survives(self):
        self.blocked_build(paperspace=3)

    def test_B_existing_unsaved_blank_document_survives(self):
        self.blocked_build()

    def test_C_existing_saved_document_survives(self):
        self.blocked_build(name='user.dwg', path='user.dwg')

    def owned_scope(self, app):
        scope = fixture.FixtureDocuments(app)
        def created(*args, **kwargs): return Session(app, app.add())
        with patch.object(fixture.DocumentSession, 'create', side_effect=created):
            session = scope.create(Path('.'))
        return scope, session

    def test_D_owned_create_use_save_close(self):
        app = App(); scope, session = self.owned_scope(app)
        owned = session.document_object
        owned.ModelSpace.Count = 8
        session.save_as('fixture.dwg', format='dwg')
        scope.close_owned(); audit = scope.cleanup()
        self.assertEqual(session.operations, ['save-dwg', 'close'])
        self.assertEqual(owned.close_calls, [False])
        self.assertTrue(audit['owned_document_closed'])
        self.assertEqual(audit['cleanup_warnings'], [])

    def test_E_mixed_documents_preserve_baseline_reference(self):
        app = App(); old = app.add(paperspace=3)
        # Teardown tested independently; production build still refuses this baseline.
        scope, session = self.owned_scope(app)
        owned = session.document_object
        scope.close_owned(); audit = scope.cleanup()
        self.assertEqual(owned.close_calls, [False])
        self.assertEqual(old.close_calls, [])
        self.assertIs(app.Documents.Item(0), old)
        self.assertTrue(audit['baseline_survived'])

    def test_F_build_failure_cleans_only_recorded_owned_document(self):
        app = App(); owned = None; other = None
        def create(*args, **kwargs):
            nonlocal owned, other
            owned = app.add(); session = Session(app, owned)
            def fail():
                nonlocal other
                other = app.add(paperspace=3)
                app.ActiveDocument = owned
                raise RuntimeError('injected build failure')
            session.set_units_mm = fail
            return session
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(fixture, 'connect', return_value=app), \
                 patch.object(fixture.DocumentSession, 'create', side_effect=create):
                with self.assertRaisesRegex(RuntimeError, 'injected build failure'):
                    fixture.build(Path(directory))
            audit = json.loads((Path(directory)/'ownership-audit.json').read_text())
            self.assertTrue(audit['owned_document_closed'])
        self.assertEqual(owned.close_calls, [False])
        self.assertEqual(other.close_calls, [])
        self.assertIs(app.Documents.Item(0), other)

    def test_dirty_failure_retains_owned_and_baseline(self):
        app = App(); old = app.add(); scope, session = self.owned_scope(app)
        session.document_object.dirty = True
        audit = scope.cleanup()
        self.assertTrue(audit['cleanup_warnings'])
        self.assertTrue(audit['baseline_survived'])
        self.assertEqual(old.close_calls, [])
        self.assertEqual(session.document_object.close_calls, [])

    def test_changed_reference_never_closes_user_document(self):
        app = App(); old = app.add(); scope, session = self.owned_scope(app)
        owned = session.document_object
        session.document_object = old
        audit = scope.cleanup()
        self.assertTrue(audit['cleanup_warnings'])
        self.assertEqual(old.close_calls, [])
        self.assertEqual(owned.close_calls, [])

    def test_factory_cannot_adopt_baseline_document(self):
        app = App(); old = app.add(); scope = fixture.FixtureDocuments(app)
        with patch.object(fixture.DocumentSession, 'create', return_value=Session(app, old)):
            with self.assertRaises(OwnershipError): scope.create(Path('.'))
        self.assertTrue(scope.cleanup()['cleanup_warnings'])
        self.assertEqual(old.close_calls, [])

    def test_baseline_replacement_with_same_name_detected(self):
        app = App(); old = app.add(); scope = fixture.FixtureDocuments(app)
        app.Documents.items.remove(old); app.add()
        self.assertFalse(scope.cleanup()['baseline_survived'])
        self.assertEqual(old.close_calls, [])


if __name__ == '__main__': unittest.main()
