"""Real CAD native import, save, clean model replacement, reopen and readback."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from landscape_agent_pack.bridge.client import RingoClient
from landscape_agent_pack.bridge.contracts import BridgeRequest
from landscape_agent_pack.bridge.errors import BridgeError
from landscape_agent_pack.bridge.validation import check_fixture, compare_persistence
from landscape_agent_pack.result import Result


def run(workspace, config=None):
    workspace = Path(workspace).resolve(strict=True)
    facts = json.loads((workspace / 'fixture-source.json').read_text(encoding='utf-8'))
    output = workspace / '真实桥接模型.skp'
    request = BridgeRequest(str(workspace),facts['dwg'],'dwg','mm',4,'mm',
                            str(workspace/'startup.skp'),str(output),facts['sha256']['dwg'],
                            expected_layers=tuple(facts['layers'])).validate()
    request_file = workspace/'request.json'
    with request_file.open('x',encoding='utf-8') as f:
        json.dump(request.to_dict(),f,ensure_ascii=False,indent=2)
    result = Result(workspace.name,'Phase 4 real CAD to SketchUp persistence',input=request.to_dict())
    client = RingoClient(config,timeout=30)
    def check(id,fn):
        value=fn()
        result.add(id,id,True,'PASS',actual=value)
        return value
    def ruby(code,mutation=False,transaction=None):
        info=client.data('model.get_info')  # model IDs are session scoped
        return client.ruby(code,model_id=info['model_id'],mutation=mutation,transaction=transaction)
    def literal(path):
        return json.dumps(str(path).replace('\\','/'),ensure_ascii=False)
    try:
        client.connect()
        status=check('BRIDGE',lambda:client.call('bridge.status'))
        result.environment=status
        result.software_version=status['sketchup_version']
        assert status['instance']['profile_id'] == client.hello['instance']['profile_id']
        assert status['instance']['port'] == client.port and status['capabilities']['ruby']
        info=client.data('model.get_info')
        assert Path(info['path']).resolve() == Path(request.startup_model).resolve()
        assert not info['modified'] and not info['active_path']
        for name in ('native_import.rb','sketchup_session.rb','persistence.rb'):
            ruby('load '+literal(ROOT/'landscape_agent_pack'/'bridge'/name))
        check('NATIVE_IMPORT',lambda:ruby('LandscapeAgentPack::NativeImport.run('+literal(request_file)+')',True))
        before=check('SNAPSHOT_BEFORE',lambda:ruby('LandscapeAgentPack::SketchupSession.snapshot'))
        (workspace/'before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
        check('GEOMETRY',lambda:check_fixture(before,facts,request))
        check('SAVE',lambda:ruby('LandscapeAgentPack::Persistence.save('+literal(request.startup_model)+','+literal(output)+')',True,False))
        # Save/Close/Open cannot run inside the default Ruby mutation transaction.
        check('CLOSE',lambda:ruby('LandscapeAgentPack::Persistence.close_saved('+literal(output)+')',True,False))
        check('REOPEN',lambda:ruby('LandscapeAgentPack::Persistence.reopen('+literal(output)+')',True,False))
        after=check('SNAPSHOT_AFTER',lambda:ruby('LandscapeAgentPack::SketchupSession.snapshot('+literal(output)+')'))
        (workspace/'after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
        check('GEOMETRY_AFTER',lambda:check_fixture(after,facts,request))
        check('PERSISTENCE',lambda:compare_persistence(before,after))
        # Actual closed TCP endpoint, with no replacement server.
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0)); port=probe.getsockname()[1]
            offline=RingoClient(config,connect_timeout=.2); offline.port=port
            started=time.monotonic()
            try:
                offline.connect()
                raise AssertionError('Offline bridge unexpectedly connected')
            except OSError:
                result.add('BRIDGE_NOT_STARTED','Refused endpoint',True,'PASS',actual={'elapsed_s':time.monotonic()-started})
            finally:
                offline.close()
        try:
            client.call('ruby.eval',{'code':42})
            raise AssertionError('Invalid Ruby input accepted')
        except BridgeError as exc:
            assert '-32602' in str(exc)
            result.add('INVALID_INPUT','Real server schema rejection',True,'PASS',actual=str(exc))
        try:
            client.call('model.get_info',deadline_ms=0)
            raise AssertionError('Expired deadline accepted')
        except BridgeError as exc:
            assert '-32003' in str(exc)
            result.add('TIMEOUT','Expired request rejected by real server',True,'PASS',actual=str(exc))
        slow=RingoClient(config,timeout=30)
        slow.connect()
        info=slow.data('model.get_info')
        slow.timeout=.3
        started=time.monotonic()
        try:
            slow.ruby('sleep(0.8); true',model_id=info['model_id'])
            raise AssertionError('Client timeout did not fire')
        except TimeoutError:
            result.add('CLIENT_TIMEOUT','Real slow Ruby read bounded by client',True,'PASS',actual={'elapsed_s':time.monotonic()-started})
        finally:
            slow.close()
        time.sleep(.8)  # Actual Ruby operation finishes; no mutation replay.
        check('TIMEOUT_RECOVERY',lambda:client.data('model.get_info'))
        digest=hashlib.sha256(Path(facts['dwg']).read_bytes()).hexdigest()
        assert digest == facts['sha256']['dwg']
        result.add('SOURCE_UNCHANGED','Source SHA256',True,'PASS',actual=digest)
        result.output={'skp':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
    except Exception as exc:
        result.add('STOPPED','Live acceptance stopped',True,'FAIL',actual=str(exc))
        result.errors.append(str(exc))
        (workspace/'traceback.txt').write_text(traceback.format_exc(),encoding='utf-8')
    finally:
        (workspace/'rpc-history.json').write_text(json.dumps(client.history,indent=2),encoding='utf-8')
        client.close()
        result.write(workspace/'phase4-result.json',workspace/'phase4-result.md')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('workspace',type=Path)
    parser.add_argument('--config',type=Path)
    args=parser.parse_args()
    result=run(args.workspace,args.config)
    print(json.dumps({'status':result.status,'errors':result.errors,'output':result.output},ensure_ascii=False))
    raise SystemExit(result.exit_code)
