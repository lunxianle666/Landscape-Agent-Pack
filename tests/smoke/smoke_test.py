"""MCP discovery smoke; optional geometry touches a uniquely owned temporary DWG only."""
import argparse,asyncio,json,os,sys,time,uuid,hashlib
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'guards'))
from creation_guard import guarded_create

records=[]
def record(name,status,**data):
    row={'name':name,'status':status,**data};records.append(row);print(name+': '+status,flush=True)

def dump_result(r):return r.model_dump(mode='json',exclude_none=True)

def retry_read(fn):
    last=None
    for _ in range(20):
        try:return fn()
        except Exception as e:last=e;time.sleep(.25)
    raise last

def doc_list(app):return retry_read(lambda:[app.Documents.Item(i) for i in range(app.Documents.Count)])
def identity(d):return retry_read(lambda:str(d.Name))
def summary(d):return retry_read(lambda:{'name':str(d.Name),'path':str(d.FullName),'saved':bool(d.Saved),'count':int(d.ModelSpace.Count)})
def owned(app,name):
    d=retry_read(lambda:app.ActiveDocument)
    if identity(d)!=name:raise RuntimeError('Active drawing changed; refusing mutation')
    return d

def verify(d):
    n=retry_read(lambda:int(d.ModelSpace.Count));assert n==2,('entities',n)
    import win32com.client.dynamic as dynamic
    ents=[dynamic.Dispatch(d.ModelSpace.Item(i)._oleobj_) for i in range(n)];types=[str(e.ObjectName) for e in ents]
    poly=next(e for e in ents if e.ObjectName=='AcDbPolyline');circle=next(e for e in ents if e.ObjectName=='AcDbCircle')
    coords=list(poly.Coordinates);expected=[0.,0.,1000.,0.,1000.,500.,0.,500.]
    assert bool(poly.Closed) and len(coords)==8 and max(abs(a-b) for a,b in zip(coords,expected))<1e-7
    assert abs(poly.Area-500000)<1e-6 and abs(poly.Length-3000)<1e-6
    assert abs(circle.Radius-100)<1e-7 and max(abs(a-b) for a,b in zip(circle.Center,[1500,250,0]))<1e-7
    assert int(d.GetVariable('INSUNITS'))==4
    return {'count':n,'types':types,'rectangle_coordinates':coords,'rectangle_area_mm2':float(poly.Area),'rectangle_perimeter_mm':float(poly.Length),'circle_center':list(circle.Center),'circle_diameter_mm':float(circle.Radius)*2,'insunits':4}

def close_owned(app,name):
    # Reacquire only the same document; never close the next active document on false error.
    for _ in range(20):
        matches=[d for d in doc_list(app) if identity(d)==name]
        if not matches:return
        try:matches[0].Close(False)
        except Exception:pass
        time.sleep(.3)
    if any(identity(d)==name for d in doc_list(app)):raise RuntimeError('Owned test drawing still open')

async def autocad(args,out):
    import pythoncom,win32com.client
    pythoncom.CoInitialize();app=None;before=[];prior=None;names=set();myname=None;reopen_name=None
    try:
        app=win32com.client.dynamic.Dispatch(win32com.client.GetActiveObject(args.progid)._oleobj_);before=[summary(d) for d in doc_list(app)];names={x['name'] for x in before}
        try:prior=app.ActiveDocument
        except Exception:pass
        record('COM_GetActiveObject','PASS',version=str(app.Version),existing_documents=len(before))
    except Exception as e:record('COM_GetActiveObject','FAIL',error=str(e));return
    if args.geometry and before:
        record('Geometry_Preflight','FAIL',reason='Existing documents detected. Close them yourself after saving; RC geometry requires an empty document collection. No mutation performed.')
        return
    draw=out/'smoke-drawings';draw.mkdir(exist_ok=True);dest=draw/('lap-smoke-'+uuid.uuid4().hex+'.dwg')
    env={**os.environ,'AUTOCAD_MCP_BACKEND':'com','CAD_PROGID':args.progid,'DISCOVERY_MODE':'search','ALLOWED_PATHS':str(draw),'PYTHONIOENCODING':'utf-8'}
    params=StdioServerParameters(command=args.mcp_exe,args=[],env=env)
    try:
        with (out/'autocad-server-stderr.log').open('w',encoding='utf-8') as err:
            async with stdio_client(params,errlog=err) as (read,write):
                async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=40)) as session:
                    init=await asyncio.wait_for(session.initialize(),45);record('MCP_handshake','PASS',server=dump_result(init))
                    tools=await session.list_tools();advertised=[t.name for t in tools.tools]
                    assert set(advertised)=={'search_tools','call_tool'},advertised
                    record('Discovery_Mode','PASS',advertised_tools=advertised)
                    found=await session.call_tool('search_tools',{'query':'CIRCLE','limit':3});assert not found.isError
                    record('Discovery_Search','PASS',result=dump_result(found))
                    async def call(name,values):
                        r=await session.call_tool('call_tool',{'name':name,'arguments':values});record('MCP_'+name,'FAIL' if r.isError else 'PASS',result=dump_result(r));return r
                    r=await call('system_status',{});assert not r.isError
                    if not args.geometry:record('Geometry','SKIPPED',reason='Use --geometry / -RunGeometrySmoke for isolated mutation test');return
                    # A failed create is never blindly repeated.
                    r=await call('drawing_new',{'bootstrap':False})
                    d=retry_read(lambda:app.ActiveDocument);myname=identity(d)
                    if myname in names:myname=None;raise RuntimeError('No newly owned document confirmed')
                    assert len(doc_list(app))==len(before)+1
                    owned(app,myname).SetVariable('INSUNITS',4)
                    for tool,values,operation in [
                        ('entity_create_polyline',{'points':[[0,0],[1000,0],[1000,500],[0,500]],'closed':True},'smoke-rectangle'),
                        ('entity_create_circle',{'cx':1500,'cy':250,'radius':100},'smoke-circle')]:
                        target=owned(app,myname)
                        verdict=await guarded_create(session,app,target,tool,values,operation_id=operation)
                        record('Guard_'+tool,verdict['status'],verification=verdict)
                        assert verdict['status'] in ['SUCCESS','SUCCESS_WITH_FALSE_ERROR'],verdict
                        count=int(target.ModelSpace.Count)
                        replay=await guarded_create(session,app,target,tool,values,operation_id=operation)
                        assert replay['duplicate_blocked'] and replay['mutation_calls']==0 and int(target.ModelSpace.Count)==count
                        record('Repeat_Prevention_'+tool,'PASS')
                    original_geometry=verify(owned(app,myname));record('Geometry_InMemory','PASS',**original_geometry)
                    save_doc=owned(app,myname);r=await call('drawing_save',{'path':str(dest)});assert dest.is_file()
                    assert Path(str(save_doc.FullName)).resolve()==dest.resolve()
                    myname=identity(save_doc)
                    assert dest.read_bytes()[:6]==b'AC1032';record('DWG_Save','PASS',format='AC1032',bytes=dest.stat().st_size)
                    owned(app,myname)
                    closed=await session.call_tool('call_tool',{'name':'drawing_close','arguments':{'save':False}})
                    for _ in range(12):
                        if all(identity(x)!=myname for x in doc_list(app)):break
                        await asyncio.sleep(.25)
                    assert all(identity(x)!=myname for x in doc_list(app)),'MCP close did not close owned test drawing'
                    record('MCP_drawing_close','SUCCESS_WITH_FALSE_ERROR' if closed.isError else 'PASS',result=dump_result(closed),repeat_close_allowed=False)
                    myname=None
                    # The reopen path is the unique file created in this run only.
                    r=await call('drawing_open',{'path':str(dest)})
                    d=retry_read(lambda:app.ActiveDocument)
                    if Path(str(d.FullName)).resolve()!=dest.resolve():raise RuntimeError('Reopened drawing identity mismatch')
                    reopen_name=identity(d);actual=verify(d);assert actual==original_geometry
                    record('DWG_Reopen_Verification','PASS',**actual,sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
                    close_owned(app,reopen_name);reopen_name=None
    except Exception as e:
        def errors(ex):
            if isinstance(ex,BaseExceptionGroup):return [v for sub in ex.exceptions for v in errors(sub)]
            return [str(ex)]
        record('AutoCAD_smoke','FAIL',error=str(e),causes=errors(e))
    finally:
        try:
            if myname:close_owned(app,myname)
            if reopen_name:close_owned(app,reopen_name)
            after=[summary(d) for d in doc_list(app)]
            assert sorted(before,key=lambda x:x['name'])==sorted(after,key=lambda x:x['name'])
            if prior:retry_read(lambda:prior.Activate())
            record('Existing_Documents_Preserved','PASS',checked=['names','paths','saved_state','entity_counts'],documents=len(before))
        except Exception as e:record('Existing_Documents_Preserved','FAIL',error=str(e),before=before,after=locals().get('after'))

async def sketchup(args,out):
    if not args.sketchup:
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'installer'))
        from environment_probe import processes
        running=any(x['name'].lower()=='sketchup.exe' for x in processes())
        record('SketchUp_Bridge','SKIPPED_NOT_REQUESTED' if running else 'SKIPPED_NOT_RUNNING',reason='Optional component; no startup or connection attempted')
        return
    if not args.node or not args.ringo:record('SketchUp_Bridge','UNAVAILABLE',reason='Node/Ringo not discovered');return
    script=Path(args.ringo)/'dist/mcp-server.js'
    if not script.is_file():record('SketchUp_Bridge','UNAVAILABLE',reason='Built Ringo MCP entry not found');return
    try:
        with (out/'sketchup-server-stderr.log').open('w',encoding='utf-8') as err:
            async with stdio_client(StdioServerParameters(command=args.node,args=[str(script)],env=dict(os.environ)),errlog=err) as (read,write):
                async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=15)) as session:
                    await asyncio.wait_for(session.initialize(),20)
                    r=await asyncio.wait_for(session.call_tool('bridge_status',{}),20)
                    record('SketchUp_Bridge','FAIL' if r.isError else 'PASS',result=dump_result(r),scope='Existing local bridge; may include local schema patch. No model mutation.')
                    if not r.isError:
                        info=await session.call_tool('model_get_info',{});record('SketchUp_Capability','FAIL' if info.isError else 'PASS',result=dump_result(info))
    except Exception as e:record('SketchUp_Bridge','FAIL',error=str(e),scope='Read-only; no SketchUp start or model mutation')

async def main(args):
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    record('Python','PASS',version=sys.version.split()[0])
    await autocad(args,out);await sketchup(args,out)
    (out/'smoke-results.json').write_text(json.dumps({'records':records},ensure_ascii=False,indent=2),encoding='utf-8')
    return 2 if any(x['status']=='FAIL' for x in records) else 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mcp-exe',required=True);p.add_argument('--progid',required=True);p.add_argument('--output',required=True);p.add_argument('--geometry',action='store_true');p.add_argument('--node');p.add_argument('--ringo');p.add_argument('--sketchup',action='store_true');a=p.parse_args()
    raise SystemExit(asyncio.run(main(a)))
