"""Failure-only transport tests; real SketchUp acceptance lives in integration/."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from landscape_agent_pack.bridge.client import RingoClient
from landscape_agent_pack.bridge.contracts import BridgeRequest
from landscape_agent_pack.bridge.errors import BridgeError, OutcomeUnknown
from landscape_agent_pack.bridge.validation import compare_persistence


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ))
        for name in ("SKETCHUP_MCP_CONFIG", "SKETCHUP_PORT", "SKETCHUP_TOKEN"):
            os.environ.pop(name, None)

    def test_port_override_does_not_require_port_in_config_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.json'
            path.write_text(json.dumps({'token': 'x' * 32}), encoding='utf-8')
            os.environ['SKETCHUP_PORT'] = '12345'
            self.assertEqual(RingoClient(path).port, 12345)

    def test_persistence_rejects_missing_records_before_zip_comparison(self):
        snapshot={'edges':[], 'edge_count':1}
        with self.assertRaises(ValueError):
            compare_persistence(snapshot,snapshot)

    def test_contract_hash_paths_overwrite_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'source.dwg'; source.write_bytes(b'contract test only')
            startup=root/'startup.skp'; startup.write_bytes(b'contract test only')
            request=BridgeRequest(str(root),str(source),'dwg','mm',4,'mm',str(startup),str(root/'out.skp'),hashlib.sha256(source.read_bytes()).hexdigest())
            request.validate()
            for changed in (replace(request,source_sha256='0'*64),replace(request,output_skp=str(root.parent/'out.skp')),
                            replace(request,curve_tolerance_mm=float('nan')),replace(request,bbox_tolerance_mm=float('inf')),
                            replace(request,source_insunits=0)):
                with self.assertRaises(ValueError): changed.validate()
            (root/'out.skp').write_bytes(b'preserve')
            with self.assertRaises(FileExistsError): request.validate()
            self.assertEqual((root/'out.skp').read_bytes(),b'preserve')

    def failure_transport(self,mode,mutation):
        with tempfile.TemporaryDirectory() as tmp, socket.socket() as server:
            server.bind(('127.0.0.1',0)); server.listen(1)
            token='private-test-value-'+'x'*40
            config=Path(tmp)/'config.json'
            config.write_text(json.dumps({'port':server.getsockname()[1],'token':token}))
            requests=[]
            def serve():
                conn,_=server.accept()
                with conn,conn.makefile('rb') as f:
                    hello=json.loads(f.readline()); requests.append(hello['method'])
                    conn.sendall((json.dumps({'jsonrpc':'2.0','id':hello['id'],'result':{'protocol':3,'capabilities':{}}})+'\n').encode())
                    request=json.loads(f.readline()); requests.append(request['method'])
                    if mode=='timeout': time.sleep(.2)
                    elif mode == 'non_object':
                        conn.sendall(b'[]\n')
                    elif mode == 'invalid_error':
                        reply = {'jsonrpc': '2.0', 'id': request['id'], 'error': None}
                        conn.sendall((json.dumps(reply) + '\n').encode())
                    elif mode=='mismatch': conn.sendall(b'{"jsonrpc":"2.0","id":"wrong","result":true}\n')
            thread=threading.Thread(target=serve); thread.start()
            c=RingoClient(config,timeout=.06)
            try:
                expected=OutcomeUnknown if mutation else (TimeoutError if mode=='timeout' else BridgeError)
                with self.assertRaises(expected): c.call('ruby.eval',{'code':'test'},mutation=mutation)
                self.assertNotIn(token,json.dumps(c.history))
                self.assertIsNone(c.sock)
                self.assertEqual(c.history[-1]['outcome'], 'unknown' if mutation else 'failed')
            finally:
                c.close(); thread.join(1)
            self.assertEqual(requests,['bridge.hello','ruby.eval'])

    def test_read_timeout_bounded(self): self.failure_transport('timeout',False)
    def test_mutation_timeout_unknown_without_replay(self): self.failure_transport('timeout',True)
    def test_mismatched_response_rejected(self): self.failure_transport('mismatch',False)
    def test_mutation_response_mismatch_unknown(self): self.failure_transport('mismatch',True)

    def test_malformed_rpc_frames_mark_submitted_mutations_unknown(self):
        for mode in ('non_object', 'invalid_error'):
            with self.subTest(mode=mode):
                self.failure_transport(mode, True)

    def test_persistence_accepts_reversed_edges_but_rejects_invalid_coordinates_and_bounds(self):
        before = {'edge_count': 1, 'edges': [{'tag': 'L-SITE', 'a': [0, 0, 0], 'b': [10, 0, 0]}],
                  'edges_by_tag': {'L-SITE': 1}, 'tags': ['L-SITE'], 'reference_transform': [],
                  'reference_markers': {}, 'root_entities': [], 'model_units_code': 2,
                  'curves': [], 'bbox_mm': [0, 0, 0, 10, 0, 0]}
        after = deepcopy(before)
        after['edges'][0]['a'], after['edges'][0]['b'] = after['edges'][0]['b'], after['edges'][0]['a']
        self.assertEqual(compare_persistence(before, after)['maximum_edge_coordinate_change_mm'], 0)
        for invalid in (float('nan'), float('inf')):
            after['edges'][0]['a'][0] = invalid
            with self.assertRaisesRegex(ValueError, 'Invalid coordinates'):
                compare_persistence(before, after)
        after = deepcopy(before)
        after['bbox_mm'][3] = 20
        with self.assertRaisesRegex(ValueError, 'Bounds changed'):
            compare_persistence(before, after)

    def test_offline_and_invalid_configuration(self):
        with tempfile.TemporaryDirectory() as tmp, socket.socket() as closed:
            closed.bind(('127.0.0.1',0))
            path=Path(tmp)/'config.json'
            config={'port':closed.getsockname()[1],'token':'x'*32}
            path.write_text(json.dumps(config))
            c=RingoClient(path,connect_timeout=.05)
            with self.assertRaises(OSError): c.connect()
            self.assertIsNone(c.sock)
            config['host']='example.com'; path.write_text(json.dumps(config))
            with self.assertRaises(ValueError): RingoClient(path)
            with self.assertRaises(ValueError): RingoClient(path,timeout=float('nan'))
