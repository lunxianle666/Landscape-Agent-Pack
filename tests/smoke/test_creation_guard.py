import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'guards'))
import creation_guard as g

EXPECTED={'type':'AcDbCircle','center':[1500.,250.,0.],'radius':100.}
ENTITY={'handle':'A','layer':'0',**EXPECTED}
class DecisionTests(unittest.TestCase):
    def test_false_error_requires_matching_new_handle(self):
        r=g.classify({}, {'A':ENTITY},EXPECTED,True)
        self.assertEqual(r['status'],'SUCCESS_WITH_FALSE_ERROR');self.assertFalse(r['repeat_creation_allowed'])
    def test_existing_lookalike_is_not_new_creation(self):
        r=g.classify({'A':ENTITY},{'A':ENTITY},EXPECTED,True)
        self.assertEqual(r['status'],'FAIL_NO_ENTITY_CREATED')
    def test_wrong_geometry_is_not_success(self):
        r=g.classify({}, {'A':{**ENTITY,'radius':101}},EXPECTED,True)
        self.assertEqual(r['status'],'REVIEW_REQUIRED')
    def test_multiple_entities_require_review(self):
        self.assertEqual(g.classify({}, {'A':ENTITY,'B':{**ENTITY,'handle':'B'}},EXPECTED,True)['status'],'REVIEW_REQUIRED')
    def test_change_to_existing_entity_is_not_success(self):
        before={'B':{**ENTITY,'handle':'B'}};after={'A':ENTITY,'B':{**ENTITY,'handle':'B','radius':200}}
        self.assertEqual(g.classify(before,after,EXPECTED,True)['status'],'REVIEW_REQUIRED')
    def test_transport_timeout_with_no_entity_is_uncertain(self):
        self.assertEqual(g.classify({}, {},EXPECTED,True,True)['status'],'REVIEW_REQUIRED')
class Reply:
    isError=True;content=[]
    def model_dump(self,**kw):return {'isError':True}
class Session:
    def __init__(self):self.calls=0
    async def call_tool(self,*a,**kw):self.calls+=1;return Reply()
class Doc:
    _oleobj_=object()
class RetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_repeat_id_cannot_create_duplicate(self):
        session=Session();doc=Doc();args={'cx':1500,'cy':250,'radius':100}
        with patch.object(g,'active_is',return_value=True),patch.object(g,'snapshot',side_effect=[{}, {'A':ENTITY}]):
            first=await g.guarded_create(session,None,doc,'entity_create_circle',args,operation_id='create-1')
            second=await g.guarded_create(session,None,doc,'entity_create_circle',args,operation_id='create-1')
        self.assertEqual(first['status'],'SUCCESS_WITH_FALSE_ERROR');self.assertEqual(session.calls,1)
        self.assertTrue(second['duplicate_blocked']);self.assertEqual(second['mutation_calls'],0)
    async def test_changed_target_prevents_mutation(self):
        session=Session()
        with patch.object(g,'active_is',return_value=False):
            with self.assertRaises(RuntimeError):await g.guarded_create(session,None,Doc(),'entity_create_circle',{'cx':1500,'cy':250,'radius':100},operation_id='changed')
        self.assertEqual(session.calls,0)
if __name__=='__main__':unittest.main()
