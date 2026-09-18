"""Read-only Windows discovery and integrity/ROT checks. Never activates AutoCAD."""
import ctypes as c
from ctypes import wintypes as wt
import json,os,sys,shutil,winreg,tomllib
from pathlib import Path

def integrity(pid):
    k=c.WinDLL('kernel32',use_last_error=True);a=c.WinDLL('advapi32',use_last_error=True)
    k.OpenProcess.argtypes=[wt.DWORD,wt.BOOL,wt.DWORD];k.OpenProcess.restype=wt.HANDLE
    k.CloseHandle.argtypes=[wt.HANDLE]
    a.OpenProcessToken.argtypes=[wt.HANDLE,wt.DWORD,c.POINTER(wt.HANDLE)]
    a.GetTokenInformation.argtypes=[wt.HANDLE,c.c_int,c.c_void_p,wt.DWORD,c.POINTER(wt.DWORD)]
    a.GetSidSubAuthorityCount.argtypes=[c.c_void_p];a.GetSidSubAuthorityCount.restype=c.POINTER(c.c_ubyte)
    a.GetSidSubAuthority.argtypes=[c.c_void_p,wt.DWORD];a.GetSidSubAuthority.restype=c.POINTER(wt.DWORD)
    h=k.OpenProcess(0x1000,False,pid);t=wt.HANDLE()
    if not h:return {'status':'UNKNOWN','error':c.get_last_error()}
    try:
        if not a.OpenProcessToken(h,8,c.byref(t)):return {'status':'UNKNOWN','error':c.get_last_error()}
        size=wt.DWORD();a.GetTokenInformation(t,25,None,0,c.byref(size));b=c.create_string_buffer(size.value)
        if not a.GetTokenInformation(t,25,b,size,c.byref(size)):return {'status':'UNKNOWN','error':c.get_last_error()}
        sid=c.cast(b,c.POINTER(c.c_void_p))[0];count=a.GetSidSubAuthorityCount(sid)[0];rid=a.GetSidSubAuthority(sid,count-1)[0]
        return {'status':'PASS','rid':rid,'level':'system' if rid>=0x4000 else 'high' if rid>=0x3000 else 'medium' if rid>=0x2000 else 'low'}
    finally:
        if t:k.CloseHandle(t)
        k.CloseHandle(h)

def processes():
    k=c.WinDLL('kernel32',use_last_error=True)
    class Entry(c.Structure):
        _fields_=[('dwSize',wt.DWORD),('cntUsage',wt.DWORD),('th32ProcessID',wt.DWORD),('th32DefaultHeapID',c.c_size_t),('th32ModuleID',wt.DWORD),('cntThreads',wt.DWORD),('th32ParentProcessID',wt.DWORD),('pcPriClassBase',wt.LONG),('dwFlags',wt.DWORD),('szExeFile',wt.WCHAR*260)]
    k.CreateToolhelp32Snapshot.argtypes=[wt.DWORD,wt.DWORD];k.CreateToolhelp32Snapshot.restype=wt.HANDLE
    k.Process32FirstW.argtypes=[wt.HANDLE,c.POINTER(Entry)];k.Process32NextW.argtypes=[wt.HANDLE,c.POINTER(Entry)]
    k.OpenProcess.argtypes=[wt.DWORD,wt.BOOL,wt.DWORD];k.OpenProcess.restype=wt.HANDLE
    k.QueryFullProcessImageNameW.argtypes=[wt.HANDLE,wt.DWORD,wt.LPWSTR,c.POINTER(wt.DWORD)];k.CloseHandle.argtypes=[wt.HANDLE]
    s=k.CreateToolhelp32Snapshot(2,0);e=Entry();e.dwSize=c.sizeof(e);out=[]
    if s==c.c_void_p(-1).value:return out
    try:
        ok=k.Process32FirstW(s,c.byref(e))
        while ok:
            if e.szExeFile.lower() in ['acad.exe','sketchup.exe','codex.exe','trae.exe','trae cn.exe','python.exe']:
                h=k.OpenProcess(0x1000,False,e.th32ProcessID);buf=c.create_unicode_buffer(32768);n=wt.DWORD(len(buf));path=None
                if h:
                    if k.QueryFullProcessImageNameW(h,0,buf,c.byref(n)):path=buf.value
                    k.CloseHandle(h)
                out.append({'name':e.szExeFile,'pid':e.th32ProcessID,'path':path,'integrity':integrity(e.th32ProcessID)})
            ok=k.Process32NextW(s,c.byref(e))
    finally:k.CloseHandle(s)
    return out

def reg_value(hive,key,name=None,view=0):
    try:
        with winreg.OpenKey(hive,key,0,winreg.KEY_READ|view) as k:return winreg.QueryValueEx(k,name)[0]
    except OSError:return None

def main():
    ps=processes();progids=[]
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,'') as k:
            i=0
            while True:
                try:name=winreg.EnumKey(k,i);i+=1
                except OSError:break
                if name.startswith('AutoCAD.Application') and reg_value(winreg.HKEY_CLASSES_ROOT,name+'\\CLSID'):progids.append(name)
    except OSError:pass
    preferred=reg_value(winreg.HKEY_CLASSES_ROOT,r'AutoCAD.Application\CurVer')
    progid=preferred if preferred in progids else (sorted([p for p in progids if p!='AutoCAD.Application'],reverse=True)+progids+[None])[0]
    compat=[]
    for hive,label in [(winreg.HKEY_CURRENT_USER,'HKCU'),(winreg.HKEY_LOCAL_MACHINE,'HKLM')]:
        for view,vlabel in [(winreg.KEY_WOW64_64KEY,'64'),(winreg.KEY_WOW64_32KEY,'32')]:
            try:
                with winreg.OpenKey(hive,r'Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers',0,winreg.KEY_READ|view) as k:
                    i=0
                    while True:
                        try:name,value,_=winreg.EnumValue(k,i);i+=1
                        except OSError:break
                        if Path(name).name.lower()=='acad.exe':compat.append({'hive':label,'view':vlabel,'path':name,'runasadmin':'RUNASADMIN' in str(value).upper()})
            except OSError:pass
    com={'status':'FAIL'}
    try:
        import pythoncom,win32com.client
        pythoncom.CoInitialize();app=win32com.client.GetActiveObject(progid);com={'status':'PASS','version':str(app.Version),'documents':int(app.Documents.Count)}
    except Exception as ex:com={'status':'FAIL','error':str(ex)}
    node=shutil.which('node');ringo=None
    cfg=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))/'config.toml'
    try:
        conf=tomllib.loads(cfg.read_text(encoding='utf-8'))
        for service in conf.get('mcp_servers',{}).values():
            for arg in service.get('args',[]):
                if isinstance(arg,str) and Path(arg).name=='mcp-server.js' and 'ringo' in arg.lower():
                    ringo=str(Path(arg).parent.parent)
                    if not node:node=service.get('command')
    except Exception:pass
    acad_paths=[p['path'] for p in ps if p['name'].lower()=='acad.exe' and p['path']]
    for p in [reg_value(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\acad.exe'),reg_value(winreg.HKEY_CURRENT_USER,r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\acad.exe')]:
        if p and p not in acad_paths:acad_paths.append(p)
    sketch_paths=[p['path'] for p in ps if p['name'].lower()=='sketchup.exe' and p['path']]
    for view in [winreg.KEY_WOW64_64KEY,winreg.KEY_WOW64_32KEY]:
        for hive in [winreg.HKEY_LOCAL_MACHINE,winreg.HKEY_CURRENT_USER]:
            base=reg_value(hive,r'SOFTWARE\SketchUp\SketchUp 2023','InstallLocation',view)
            if base:sketch_paths.append(str(Path(base)/'SketchUp.exe'))
    # Installed desktop paths: vendor registrations and standard uninstall records.
    for hive in [winreg.HKEY_LOCAL_MACHINE,winreg.HKEY_CURRENT_USER]:
        for view in [winreg.KEY_WOW64_64KEY,winreg.KEY_WOW64_32KEY]:
            def scan(key,depth=0):
                if depth>4:return
                try:
                    with winreg.OpenKey(hive,key,0,winreg.KEY_READ|view) as handle:
                        i=0
                        while True:
                            try:name,value,_=winreg.EnumValue(handle,i);i+=1
                            except OSError:break
                            if isinstance(value,str) and name.lower() in ['acadlocation','installlocation','installdir','installationpath']:
                                exe=Path(value.strip('"'))/'acad.exe'
                                if exe.is_file():acad_paths.append(str(exe))
                        i=0
                        while True:
                            try:sub=winreg.EnumKey(handle,i);i+=1
                            except OSError:break
                            scan(key+'\\'+sub,depth+1)
                except OSError:pass
            scan(r'SOFTWARE\Autodesk\AutoCAD')
            base=r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'
            try:
                with winreg.OpenKey(hive,base,0,winreg.KEY_READ|view) as handle:
                    i=0
                    while True:
                        try:sub=winreg.EnumKey(handle,i);i+=1
                        except OSError:break
                        key=base+'\\'+sub;name=reg_value(hive,key,'DisplayName',view);loc=reg_value(hive,key,'InstallLocation',view)
                        if loc and name and 'sketchup' in name.lower():
                            exe=Path(loc)/'SketchUp.exe'
                            if exe.is_file():sketch_paths.append(str(exe))
            except OSError:pass
    acad_paths=list(dict.fromkeys(acad_paths))
    plugin=Path(os.environ.get('APPDATA',''))/'SketchUp/SketchUp 2023/SketchUp/Plugins/ringo_sketchup_mcp.rb'
    me=integrity(os.getpid());auto=[p for p in ps if p['name'].lower()=='acad.exe']
    pairs=[{'pid':p['pid'],'compatible':p['integrity'].get('rid')==me.get('rid') if 'rid' in p['integrity'] and 'rid' in me else None} for p in auto]
    result={'python':{'version':sys.version.split()[0],'executable':sys.executable,'bits':c.sizeof(c.c_void_p)*8},'host_integrity':me,'processes':ps,'autocad_paths':acad_paths,'sketchup_paths':list(dict.fromkeys(sketch_paths)),'progids':progids,'progid':progid,'compatibility_entries':compat,'autocad_host_integrity':pairs,'com':com,'node':node,'ringo':ringo,'ringo_extension_present':plugin.is_file()}
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
