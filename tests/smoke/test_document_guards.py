import unittest
from unittest.mock import patch
import smoke_test as smoke

class Doc:
    def __init__(self,name,app=None):self.Name=name;self.closed=0;self.app=app
    def Close(self,save):
        self.closed+=1
        self.app.docs.remove(self)
        raise RuntimeError('RPC false failure after actual close')
class Collection:
    def __init__(self,app):self.app=app
    @property
    def Count(self):return len(self.app.docs)
    def Item(self,i):return self.app.docs[i]
class App:
    def __init__(self):self.docs=[];self.Documents=Collection(self)

class GuardTests(unittest.TestCase):
    def test_refuses_changed_active_document(self):
        app=App();app.ActiveDocument=Doc('user-drawing')
        with self.assertRaises(RuntimeError):smoke.owned(app,'owned-test')
    def test_false_close_error_never_closes_user_document(self):
        app=App();user=Doc('user-drawing',app);test=Doc('owned-test',app);app.docs=[user,test]
        with patch.object(smoke.time,'sleep'):smoke.close_owned(app,'owned-test')
        self.assertEqual(test.closed,1);self.assertEqual(user.closed,0);self.assertEqual(app.docs,[user])
    def test_unknown_owned_name_is_noop(self):
        app=App();user=Doc('user-drawing',app);app.docs=[user]
        smoke.close_owned(app,'missing-test');self.assertEqual(user.closed,0)
if __name__=='__main__':unittest.main()
