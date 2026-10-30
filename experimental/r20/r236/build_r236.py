"""R2.3.6 candidate: true independent NameTag DOCX source re-verification
and partial R220 subtitle per-cut duration REVIEW. Not a montage/VO rewrite.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,re,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
NAMETAG="tools/r20_graphics_plans.py"
SUBS="tools/r226_partial_subtitles.py"
UNIVERSAL="tools/r230_universal.py"
GUARD="tools/r236_name_guard.py"
COVERAGE="tools/r237_coverage.py"
PANEL="cep/r20_panel.js"
def sha(x):return hashlib.sha256(x).hexdigest()
def replace(s,old,new):
 if s.count(old)!=1:raise ValueError("UNKNOWN_UPSTREAM_CODE: "+old[:85])
 return s.replace(old,new,1)
def source(f,version,file):
 with zipfile.ZipFile(f) as z:
  m=json.loads(z.read("manifest.json"))
  if m.get("version")!=version or m.get("format")!=1:
   raise ValueError("SOURCE_VERSION_INVALID: "+version)
  rows=[r for r in m["files"] if r["path"]==file]
  if len(rows)!=1:raise ValueError("SOURCE_FILE_MISSING "+file)
  data=z.read("payload/"+file)
  if sha(data)!=rows[0]["sha256"]:raise ValueError("SOURCE_FILE_SHA_CHANGED "+file)
  return data
def patch_nametag(raw):
 s=raw.decode("utf8")
 old="""def build(docx,module,separator=SEPARATOR,omit_struck=False):
    try:
        return _r230_legacy_build(docx,module,separator,omit_struck)
    except ValueError as problem:
        reason=str(problem)
        if ("Nu am identificat declarații în DOCX" not in reason and
            "Nu există cartoane editoriale în DOCX" not in reason):
            raise
        from r230_universal import build as universal_build
        return universal_build(docx,module,separator,omit_struck)"""
 new="""def build(docx,module,separator=SEPARATOR,omit_struck=False):
    # R2.3.7 root cause: the original legacy-first parser may return a
    # PARTIAL plan without raising. Do not accept its silent omissions.
    # Run one universal DOCX parser for ALL independent modules, then
    # validate that timed dialogue and uppercase VO paragraphs were read.
    from r230_universal import parse as universal_parse, build as universal_build
    from r237_coverage import verify as verify_editorial_coverage
    parsed=universal_parse(docx)
    coverage=verify_editorial_coverage(docx,parsed,omit_struck,module)
    plan=universal_build(docx,module,separator,omit_struck)
    plan['editorialCoverage']=coverage
    if module=='03' and plan['totalItems']>0:
        from docx import Document
        from r236_name_guard import check as check_docx_name_anchors
        import re as _re
        visible=[p.text.strip() for p in Document(docx).paragraphs]
        if any(_re.fullmatch(r'[0-9]{4}',x) for x in visible):
            plan['sourceNameReview']=check_docx_name_anchors(docx,plan)
    return plan"""
 s=replace(s,old,new)
 compile(s,NAMETAG,"exec")
 return s.encode("utf8")
def patch_panel(raw,old_universal,new_universal):
 s=raw.decode("utf8")
 before=sha(old_universal)
 if s.count(before)!=1:raise ValueError("UNIVERSAL_SHA_HANDSHAKE_ANCHOR_MISSING")
 s=replace(s,before,sha(new_universal))
 if 'R2.3.5 BETA' in s:s=s.replace('R2.3.5 BETA','R2.3.6 BETA')
 # Do not modify any of the R229 approval/readback sequence with string
 # substitutions unless an exact verified source signature is available.
 # Per-CUT review remains captured in the SHA-guarded R226 plan JSON.
 for key in ('ENGINE_VERSION_MISMATCH','onClickCapture','recoverOrFallback',
             'showNameTagReview','noContentStatus','rollback'):
  if key not in s:raise ValueError("SAFETY_FEATURE_LOST "+key)
 return s.encode("utf8")
def build(v230,v226,v234,v235,out):
 originals={
  NAMETAG:source(v230,"2.3.0",NAMETAG),
  SUBS:source(v226,"2.2.6",SUBS),
  UNIVERSAL:source(v234,"2.3.4",UNIVERSAL),
  PANEL:source(v235,"2.3.5",PANEL)
 }
 universal=(ROOT/"candidate/tools/r230_universal.py").read_bytes()
 subtitles=(ROOT/"candidate/tools/r226_partial_subtitles.py").read_bytes()
 guard=(ROOT/"candidate/tools/r236_name_guard.py").read_bytes()
 coverage=(ROOT.parent/"r237/candidate/tools/r237_coverage.py").read_bytes()
 for name,raw in ((UNIVERSAL,universal),(SUBS,subtitles),(GUARD,guard),(COVERAGE,coverage)):
  compile(raw,name,"exec")
 if b'primar|medic|doctor|locuitor' not in universal:
  raise ValueError("MEDIC_EXPLICIT_ROLE_MISSING")
 if b'durationReview' not in subtitles or b'REVIEW_DURATION_ON_CONFIRMED_CUT' not in subtitles:
  raise ValueError("PER_CUT_DURATION_REVIEW_MISSING")
 files={
  NAMETAG:patch_nametag(originals[NAMETAG]),
  SUBS:subtitles,
  UNIVERSAL:universal,GUARD:guard,COVERAGE:coverage,
  PANEL:patch_panel(originals[PANEL],originals[UNIVERSAL],universal)
 }
 meta={"format":1,"version":"2.3.6","files":[{
   "path":p,"before_sha256":sha(originals[p]) if p in originals else None,
   "sha256":sha(files[p])} for p in sorted(files)]}
 target=pathlib.Path(out);target.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.writestr("manifest.json",json.dumps(meta,indent=2,ensure_ascii=True)+"\n")
  for p,raw in sorted(files.items()):z.writestr("payload/"+p,raw)
 with zipfile.ZipFile(target) as z:
  if set(z.namelist())!={"manifest.json",*(("payload/"+p) for p in files)}:
   raise ValueError("ZIP_UNEXPECTED_SCOPE")
  for p,raw in files.items():
   if sha(z.read("payload/"+p))!=sha(raw):raise ValueError("PAYLOAD_SHA_INVALID")
 return {"version":"2.3.6","files":meta["files"],"zipSHA256":sha(target.read_bytes())}
if __name__=="__main__":
 ap=argparse.ArgumentParser()
 for n in ("v230","v226","v234","v235","out"):ap.add_argument("--"+n,required=True)
 a=ap.parse_args()
 print(json.dumps(build(a.v230,a.v226,a.v234,a.v235,a.out),indent=2))
