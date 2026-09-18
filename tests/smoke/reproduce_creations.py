"""Seven minimal creation reproductions. Requires zero open AutoCAD documents."""
import argparse,asyncio,json,os,sys,time
from pathlib import Path
from datetime import timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'guards'))
from creation_guard import guarded_create,dynamic
from smoke_test import doc_list,identity,close_owned,retry_read
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def main(a):
    import pythoncom,win32com.client
    pythoncom.CoInitialize();app=dynamic(win32com.client.GetActiveObject(a.progid));assert len(doc_list(app))==0,'Existing documents present; refusing test'
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True);results=[]
    cases=[('Line','entity_create_line',{'x1':0,'y1':0,'x2':1000,'y2':500}),('Polyline','entity_create_polyline',{'points':[[0,0],[1000,0],[1000,500],[0,500]],'closed':True}),('Circle','entity_create_circle',{'cx':1500,'cy':250,'radius':100}),('Text','entity_create_text',{'text':'LAP RC1.1 Test','x':0,'y':700,'height':100}),('Block','entity_create_block_ref',{'name':'LAP_RC_TEST_BLOCK','x':2000,'y':0}),('Hatch','entity_create_hatch',{'pattern':'SOLID','boundary_points':[[0,0],[1000,0],[1000,500],[0,500]]}),('Dimension','dimension_linear',{'x1':0,'y1':0,'x2':1000,'y2':0,'dim_x':500,'dim_y':-100,'rotation':0})]
    env={**os.environ,'AUTOCAD_MCP_BACKEND':'com','CAD_PROGID':a.progid,'DISCOVERY_MODE':'search','ALLOWED_PATHS':str(out),'PYTHONIOENCODING':'utf-8'}
    with (out/'server-stderr.log').open('w',encoding='utf-8') as err:
        async with stdio_client(StdioServerParameters(command=a.mcp_exe,args=[],env=env),errlog=err) as (read,write):
            async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=40)) as session:
                await session.initialize()
                for label,tool,values in cases:
                    name=None
                    try:
                        await session.call_tool('call_tool',{'name':'drawing_new','arguments':{'bootstrap':False}})
                        assert len(doc_list(app))==1
                        doc=retry_read(lambda:app.ActiveDocument);name=identity(doc);doc.SetVariable('INSUNITS',4)
                        if label=='Block':
                            block=dynamic(doc.Blocks.Add(win32com.client.VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,[0.,0.,0.]),values['name']))
                            block.AddLine(win32com.client.VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,[0.,0.,0.]),win32com.client.VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,[100.,0.,0.]))
                        r=await guarded_create(session,app,doc,tool,values,operation_id='repro-'+label);r['case']=label
                        count=int(doc.ModelSpace.Count)
                        replay=await guarded_create(session,app,doc,tool,values,operation_id='repro-'+label)
                        assert replay['mutation_calls']==0 and replay['duplicate_blocked'] and int(doc.ModelSpace.Count)==count
                        r['repeat_prevention_verified']=True
                        probes=[]
                        for i in range(doc.ModelSpace.Count):
                            entity=doc.ModelSpace.Item(i);entry={'handle':str(entity.Handle)}
                            try:entry['generated_Color']=win32com.client.Dispatch(entity._oleobj_).Color
                            except Exception as e:entry['generated_Color_error']=str(e)
                            try:entry['generated_lowercase_color']=win32com.client.Dispatch(entity._oleobj_).color
                            except Exception as e:entry['generated_lowercase_color_error']=str(e)
                            try:entry['dynamic_Color']=dynamic(entity).Color
                            except Exception as e:entry['dynamic_Color_error']=str(e)
                            probes.append(entry)
                        r['same_entity_Color_probes']=probes;results.append(r);print(label+': '+r['status'],flush=True)
                    except Exception as e:results.append({'case':label,'tool':tool,'status':'REPRODUCTION_ERROR','error':str(e)});print(label+': REPRODUCTION_ERROR '+str(e),flush=True)
                    finally:
                        if name:close_owned(app,name)
                        assert len(doc_list(app))==0
    (out/'reproduction-results.json').write_text(json.dumps({'cases':results,'existing_documents_preserved':True},ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if len(results)==7 and all(x['status'] in ['SUCCESS','SUCCESS_WITH_FALSE_ERROR','FAIL_NO_ENTITY_CREATED'] for x in results) else 2
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mcp-exe',required=True);p.add_argument('--progid',default='AutoCAD.Application.25');p.add_argument('--output',required=True)
    raise SystemExit(asyncio.run(main(p.parse_args())))
