"""R239 verified COMBINED patch assembled from the exact last shipped
file for each path, not from presumed repo state. Stable R1.9.13 untouched.
For the user-reported defects: 01 opaque JSX error, 03 legacy NameTag
code mismatch, 02/04 silent incomplete independent DOCX.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,tempfile,zipfile,sys
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"r236"))
from build_r236 import build as build_parser_fix
WRITER="cep/jsx/r220_montage_writer.jsx"
WORKFLOW="cep/r193_workflow.js"
VERSIONS={WRITER:("2.2.5","003834a50a7e9f2a15e9beb28348724749ed15e91db275a61df44a14ae9696fa"),
          WORKFLOW:("2.2.7",None)}
def sha(b):return hashlib.sha256(b).hexdigest()
def item(archive,version,path,expected=None):
 with zipfile.ZipFile(archive) as z:
  m=json.loads(z.read("manifest.json"))
  if m.get("version")!=version:raise ValueError("OLD_RELEASE_VERSION_CHANGED "+version)
  rows=[r for r in m["files"] if r["path"]==path]
  if len(rows)!=1:raise ValueError("PATH_NOT_IN_RELEASE "+path)
  data=z.read("payload/"+path)
  if sha(data)!=rows[0]["sha256"]:raise ValueError("RELEASE_SHA_MISMATCH "+path)
  if expected and sha(data)!=expected:raise ValueError("PINNED_SOURCE_SHA_MISMATCH "+path)
  return data
def replace(s,old,new):
 if s.count(old)!=1:raise ValueError("UPSTREAM_ANCHOR_CHANGED: "+old[:70])
 return s.replace(old,new,1)
def writer(raw):
 s=raw.decode("utf8")
 s=replace(s,'if(s.overwriteClip(item,c.timelineStart,0,0)!==true)',
             'if(s.overwriteClip(item,String(c.timelineStart),0,0)!==true)')
 anchor="  return {preflight:preflight,commit:commit};"
 source=(ROOT.parent/"r238/cep/jsx/r220_montage_writer.jsx").read_text("utf8")
 begin=source.index("  // CEP can return only")
 finish=source.index("  return {preflight:preflight,commit:commit,commitFromFile:commitFromFile};",begin)
 injected=source[begin:finish]
 s=replace(s,anchor,injected+"  return {preflight:preflight,commit:commit,commitFromFile:commitFromFile};")
 if "return JSON.stringify({ok:false,phase:\"PREFLIGHT_REJECTED\"" not in s:
  raise ValueError("ERROR_RETURN_GUARD_MISSING")
 if "rollback(s,added,markers)" not in s:raise ValueError("ROLLBACK_REQUIRED")
 return s.encode("utf8")
def workflow(raw):
 s=raw.decode("utf8")
 source=(ROOT.parent/"r238/cep/r220_montage_panel.js").read_text("utf8")
 begin=source.index("   // Plan JSON was already")
 finish=source.index("   evalJS('AIVE_R220.commitFromFile('+params+')',function(error,result){",begin)
 new=source[begin:finish]+"   evalJS('AIVE_R220.commitFromFile('+params+')',function(error,result){"
 old="   var params=JSON.stringify(state.lock.plan)+','+JSON.stringify(choice)+','+\n       JSON.stringify(state.lock.plan.planSHA256);\n   evalJS('AIVE_R220.commit('+params+')',function(error,result){"
 s=replace(s,old,new)
 if "AIVE_R220.commit('+params+')'" in s:raise ValueError("OLD_INLINE_PLAN_CALL_REMAINS")
 if "verifyState(state,media" not in s or "loadLocked(response" not in s:
  raise ValueError("R220_PREFLIGHT_IDENTITY_LOST")
 return s.encode("utf8")
def build(paths,out):
 with tempfile.TemporaryDirectory() as td:
  partial=pathlib.Path(td)/"base.zip"
  build_parser_fix(paths["v230"],paths["v226"],paths["v234"],paths["v235"],partial)
  old_writer=item(paths["v225"],"2.2.5",WRITER,VERSIONS[WRITER][1])
  old_workflow=item(paths["v227"],"2.2.7",WORKFLOW)
  extra={WRITER:(old_writer,writer(old_writer)),WORKFLOW:(old_workflow,workflow(old_workflow))}
  with zipfile.ZipFile(partial) as z:
   m=json.loads(z.read("manifest.json"))
   data={r["path"]:z.read("payload/"+r["path"]) for r in m["files"]}
  for p,(before,after) in extra.items():
   if p in data:raise ValueError("DUPLICATE_PATCH_PATH "+p)
   data[p]=after
   m["files"].append({"path":p,"before_sha256":sha(before),"sha256":sha(after)})
  m["files"].sort(key=lambda v:v["path"])
  assert len(m["files"])==7
  dest=pathlib.Path(out);dest.parent.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(dest,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
   z.writestr("manifest.json",json.dumps(m,indent=2,ensure_ascii=True)+"\n")
   for p,v in sorted(data.items()):z.writestr("payload/"+p,v)
  with zipfile.ZipFile(dest) as z:
   assert set(z.namelist())=={"manifest.json",*(("payload/"+p) for p in data)}
   for row in m["files"]:assert sha(z.read("payload/"+row["path"]))==row["sha256"]
  return {"version":m["version"],"paths":[x["path"] for x in m["files"]],
          "zipSHA256":sha(dest.read_bytes()),"archive":str(dest)}
if __name__=="__main__":
 p=argparse.ArgumentParser()
 for v in ("v225","v226","v227","v230","v234","v235","out"):p.add_argument("--"+v,required=True)
 a=p.parse_args()
 print(json.dumps(build({v:getattr(a,v) for v in ("v225","v226","v227","v230","v234","v235")},a.out),indent=2))
