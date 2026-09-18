"""Read-only document snapshot. Raw output is private; no activation or save."""
import argparse,json
import pythoncom,win32com.client
p=argparse.ArgumentParser();p.add_argument('--progid',default='AutoCAD.Application');a=p.parse_args()
pythoncom.CoInitialize();app=win32com.client.GetActiveObject(a.progid)
rows=[]
for d in app.Documents:rows.append({'name':str(d.Name),'path':str(d.FullName),'saved':bool(d.Saved),'entities':int(d.ModelSpace.Count)})
print(json.dumps({'documents':rows},ensure_ascii=False))
