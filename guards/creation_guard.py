"""Self-authored postcondition guard. Does not patch MCP or retry mutations."""
import asyncio,math

SUPPORTED={'entity_create_line','entity_create_polyline','entity_create_circle','entity_create_text','entity_create_block_ref','block_insert','entity_create_hatch','dimension_linear'}

def dynamic(obj):
    import win32com.client.dynamic
    return win32com.client.dynamic.Dispatch(obj._oleobj_)

def document_key(doc):
    # The caller owns this document; IDispatch identity is checked separately.
    return (str(doc.Name),str(doc.FullName))

def active_is(app,doc):
    return app.ActiveDocument._oleobj_ == doc._oleobj_ and document_key(app.ActiveDocument)==document_key(doc)

def describe(raw):
    e=dynamic(raw);t=str(e.ObjectName);d={'handle':str(e.Handle),'type':t,'layer':str(e.Layer)}
    if t=='AcDbLine':d.update(start=list(e.StartPoint),end=list(e.EndPoint))
    elif t=='AcDbPolyline':d.update(coordinates=list(e.Coordinates),closed=bool(e.Closed),area=float(e.Area),length=float(e.Length))
    elif t=='AcDbCircle':d.update(center=list(e.Center),radius=float(e.Radius))
    elif t=='AcDbText':d.update(text=str(e.TextString),insertion=list(e.InsertionPoint),height=float(e.Height),rotation=float(e.Rotation))
    elif t=='AcDbBlockReference':d.update(name=str(e.Name),insertion=list(e.InsertionPoint),scale_x=float(e.XScaleFactor),scale_y=float(e.YScaleFactor),scale_z=float(e.ZScaleFactor),rotation=float(e.Rotation))
    elif t=='AcDbHatch':
        lo,hi=e.GetBoundingBox();d.update(pattern=str(e.PatternName),scale=float(e.PatternScale),angle=float(e.PatternAngle),loops=int(e.NumberOfLoops),area=float(e.Area),bbox_min=list(lo),bbox_max=list(hi))
    elif t=='AcDbRotatedDimension':
        position=list(e.TextPosition);rotation=float(e.Rotation)
        d.update(measurement=float(e.Measurement),rotation=rotation,normal=list(e.Normal),text_position=position,text_projection=position[0]*math.cos(rotation)+position[1]*math.sin(rotation))
    return d

def snapshot(doc):
    return {d['handle']:d for d in (describe(doc.ModelSpace.Item(i)) for i in range(int(doc.ModelSpace.Count)))}

def near(a,b):
    if isinstance(a,dict) and isinstance(b,dict):return set(a)==set(b) and all(near(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)) and isinstance(b,(list,tuple)):return len(a)==len(b) and all(near(x,y) for x,y in zip(a,b))
    if isinstance(a,bool) or isinstance(b,bool):return a==b
    if isinstance(a,(float,int)) and isinstance(b,(float,int)):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-6)
    return a==b

def expected_signature(tool,a):
    pt=lambda x,y:[float(x),float(y),0.]
    if tool=='entity_create_line':return {'type':'AcDbLine','start':[a['x1'],a['y1'],a.get('z1',0)],'end':[a['x2'],a['y2'],a.get('z2',0)]}
    if tool=='entity_create_polyline':return {'type':'AcDbPolyline','coordinates':[v for pt2 in a['points'] for v in pt2],'closed':a.get('closed',False)}
    if tool=='entity_create_circle':return {'type':'AcDbCircle','center':pt(a['cx'],a['cy']),'radius':a['radius']}
    if tool=='entity_create_text':return {'type':'AcDbText','text':a['text'],'insertion':pt(a['x'],a['y']),'height':a.get('height',2.5),'rotation':math.radians(a.get('rotation',0))}
    if tool in ['entity_create_block_ref','block_insert']:return {'type':'AcDbBlockReference','name':a['name'],'insertion':pt(a['x'],a['y']),'scale_x':a.get('scale_x',1),'scale_y':a.get('scale_y',1),'scale_z':1.,'rotation':math.radians(a.get('rotation',0))}
    if tool=='entity_create_hatch':
        points=a['boundary_points'];area=abs(sum(x[0]*y[1]-y[0]*x[1] for x,y in zip(points,points[1:]+points[:1])))/2
        # RC supported boundary is a simple rectangle. Arbitrary hatch regions require review.
        if len(points)!=4 or len(set(x[0] for x in points))!=2 or len(set(x[1] for x in points))!=2:raise ValueError('Only simple rectangular hatch postconditions supported in RC1.1')
        return {'type':'AcDbHatch','pattern':a['pattern'],'scale':a.get('scale',1),'angle':math.radians(a.get('angle',0)),'loops':1,'area':area,'bbox_min':pt(min(x[0] for x in points),min(x[1] for x in points)),'bbox_max':pt(max(x[0] for x in points),max(x[1] for x in points))}
    if tool=='dimension_linear':
        r=math.radians(a.get('rotation',0));measure=abs((a['x2']-a['x1'])*math.cos(r)+(a['y2']-a['y1'])*math.sin(r))
        return {'type':'AcDbRotatedDimension','rotation':r,'measurement':measure,'normal':[0.,0.,1.],'text_projection':((a['x1']+a['x2'])*math.cos(r)+(a['y1']+a['y2'])*math.sin(r))/2}
    raise ValueError('Unsupported creation tool; do not call unguarded')

def classify(before,after,expected,failed,transport_uncertain=False):
    added=sorted(set(after)-set(before));removed=sorted(set(before)-set(after));changed=[h for h in before if h in after and not near(before[h],after[h])]
    result={'before_count':len(before),'after_count':len(after),'count_delta':len(after)-len(before),'new_handles':added,'removed_handles':removed,'changed_existing_handles':changed,'new_entities':[after[h] for h in added],'repeat_creation_allowed':False}
    matches=not removed and not changed and len(added)==1 and all(k in after[added[0]] and near(after[added[0]][k],v) for k,v in expected.items())
    if matches:result['status']='SUCCESS_WITH_FALSE_ERROR' if failed else 'SUCCESS'
    elif not added and not removed and not changed:result['status']='REVIEW_REQUIRED' if transport_uncertain else 'FAIL_NO_ENTITY_CREATED'
    else:result['status']='REVIEW_REQUIRED'
    return result

async def _guarded_create_once(session,app,doc,tool,arguments):
    if tool not in SUPPORTED:raise ValueError('Unsupported tool')
    expected=expected_signature(tool,arguments)
    if arguments.get('layer') is not None:expected['layer']=arguments['layer']
    # Attributes not checked by the signature must never be silently treated as verified.
    allowed={'entity_create_line':{'x1','y1','x2','y2','z1','z2','layer'},'entity_create_polyline':{'points','closed','layer'},'entity_create_circle':{'cx','cy','radius','layer'},'entity_create_text':{'text','x','y','height','rotation','layer'},'entity_create_block_ref':{'name','x','y','scale_x','scale_y','rotation','layer'},'block_insert':{'name','x','y','scale_x','scale_y','rotation','layer'},'entity_create_hatch':{'pattern','boundary_points','scale','angle','layer'},'dimension_linear':{'x1','y1','x2','y2','dim_x','dim_y','rotation','layer'}}
    if set(arguments)-allowed[tool]:raise ValueError('Unverified optional parameters; review required before invocation')
    if not active_is(app,doc):raise RuntimeError('Target document changed; mutation refused')
    before=snapshot(doc);raw=None;error=None;uncertain=False
    # Exactly one mutating invocation. Postcondition reads may repeat; creations never do.
    try:
        reply=await session.call_tool('call_tool',{'name':tool,'arguments':arguments})
        raw=reply.model_dump(mode='json',exclude_none=True);failed=bool(reply.isError)
        if failed:error='\n'.join(c.text for c in reply.content if getattr(c,'type',None)=='text')
    except Exception as ex:failed=True;error=str(ex);uncertain=True
    after=None;read_error=None
    for _ in range(8):
        try:
            if not active_is(app,doc):raise RuntimeError('Target document changed after invocation')
            after=snapshot(doc);read_error=None
            result=classify(before,after,expected,failed,uncertain)
            if result['status'] in ['SUCCESS','SUCCESS_WITH_FALSE_ERROR']:break
        except Exception as ex:read_error=str(ex)
        await asyncio.sleep(.2)
    if after is None or read_error:
        result={'status':'REVIEW_REQUIRED','repeat_creation_allowed':False,'before_count':len(before),'verification_error':read_error}
    result.update(tool=tool,arguments=arguments,expected=expected,raw_mcp=raw,error_original=error,mutation_calls=1)
    return result

# Operation IDs distinguish intentional identical geometry from an accidental retry.
_operations={}
_owners={}
async def guarded_create(session,app,doc,tool,arguments,*,operation_id):
    if not operation_id:raise ValueError('An operation_id is required for repeat prevention')
    key=(session,operation_id)
    if key in _operations:
        prior=_operations[key]
        if _owners[key] != doc._oleobj_:raise ValueError('Operation ID reused for a different document')
        if prior['tool']!=tool or prior['arguments']!=arguments:raise ValueError('Operation ID reused for different creation')
        return {**prior,'duplicate_blocked':True,'mutation_calls':0,'repeat_creation_allowed':False}
    _owners[key]=doc._oleobj_
    _operations[key]={'tool':tool,'arguments':dict(arguments),'status':'REVIEW_REQUIRED','repeat_creation_allowed':False,'reason':'Operation in progress or interrupted; inspect before any new operation'}
    result=await _guarded_create_once(session,app,doc,tool,arguments)
    _operations[key]=result
    return result
