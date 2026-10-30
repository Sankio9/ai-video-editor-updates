"""R2.3.6 candidate: preserve verified NameTags on contradictory source markers,
and keep already confirmed R220 subtitle cuts if another cut cannot fit.
No QE, no Premiere mutation; only conservative analysis sources.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
NAMETAG="tools/r20_graphics_plans.py"
SUBS="tools/r226_partial_subtitles.py"
PANEL="cep/r229_subtitles_panel.js"
def sha(x):return hashlib.sha256(x).hexdigest()
def replace(s,old,new):
 if s.count(old)!=1:raise ValueError("UNKNOWN_UPSTREAM_CODE: "+old[:85])
 return s.replace(old,new,1)

def patch_nametag(original):
 s=original.decode("utf8")
 # The last document source header may contradict a CUT source. Do NOT silently
 # assign that person's name to the contradictory CUT; mark explicit REVIEW.
 old="""    if last_source and code and last_source[2]!=code:
        raise ValueError('NameTag REVIEW: cod sursă DOCX %s ≠ %s la CUT-%02d' %
                         (last_source[2],code,seg['ordinal']))"""
 new="""    if last_source and code and last_source[2]!=code:
        return ('REVIEW_MISSING_IDENTITY',
                'COD_SURSĂ_CONTRADICTORIU: în Word %s, CUT-%02d %s. '
                'Burtiera CUT-ului este omisă; verifică manual identificarea.' %
                (last_source[2],seg['ordinal'],code))"""
 s=replace(s,old,new)
 old="""            if last_source and code and last_source[2]!=code:
                raise ValueError('NameTag REVIEW: cod sursă DOCX %s ≠ %s la CUT-%02d' %
                                 (last_source[2],code,seg['ordinal']))
            marker=(before[-1][0],before[-1][1])"""
 new="""            if last_source and code and last_source[2]!=code:
                # A source mismatch can never become a NameTag, even if a
                # parser has extracted a plausible person's name and role.
                prior_identity=None;prior_marker=None
                yield seg,None,None
                continue
            marker=(before[-1][0],before[-1][1])"""
 s=replace(s,old,new)
 # If ALL NameTags are questionable, generate an empty review plan so CEP
 # reports skipped CUTs, rather than raising an opaque Python traceback.
 s=replace(s,
     "    if not items:raise ValueError('Nu există elemente valide pentru categoria '+module)",
     "    if not items and module!='03':raise ValueError('Nu există elemente valide pentru categoria '+module)")
 assert "REVIEW_MISSING_IDENTITY" in s and "COD_SURSĂ_CONTRADICTORIU" in s
 compile(s,NAMETAG,"exec")
 return s.encode('utf8')

def patch_subtitles(original):
 s=original.decode("utf8")
 s=replace(s,
  "    included=[];seen=set();layout=[];cursor=0",
  "    included=[];seen=set();layout=[];cursor=0;skipped_confirmed=[]")
 old="""        # Reuse validated R2.1.2 readable layout and strikethrough policy.
        durations=allocate([v["text"] for v in group],ed-st)
        progress=st"""
 new="""        # Only this one confirmed CUT can fail to fit. Do not discard other
        # fully verified CUTs. Never shorten a caption or invent word timing.
        try:
            durations=allocate([v["text"] for v in group],ed-st)
        except ValueError as problem:
            if str(problem) not in ("SUBTITLE_DURATION_UNREADABLE",
                                    "CUT_TOO_SHORT_OR_LONG_FOR_SUBTITLES"):
                raise
            skipped_confirmed.append({"cutId":cut,"sourceCode":m["sourceCode"],
                "reason":str(problem),
                "durationSeconds":round(ed-st,4),
                "cueCount":len(group)})
            continue
        progress=st"""
 s=replace(s,old,new)
 s=replace(s,
  '    require(layout and len(layout)<=2000,"NO_ELIGIBLE_SUBTITLES")',
  '    require(layout and len(layout)<=2000,"NO_ELIGIBLE_SUBTITLES: '+ '" + str(skipped_confirmed))')
 s=replace(s,
  '"items":layout,"totalItems":len(layout),"subtitledCuts":included}',
  '"items":layout,"totalItems":len(layout),"subtitledCuts":included,'+
  '"skippedConfirmedCuts":skipped_confirmed}')
 s=replace(s,
  '"reservedCuts":p["reservedCount"],"timing":p["timing"]}',
  '"reservedCuts":p["reservedCount"],"timing":p["timing"],'+
  '"skippedConfirmedCuts":p["skippedConfirmedCuts"]}')
 compile(s,SUBS,"exec")
 return s.encode('utf8')

def patch_panel(original):
 s=original.decode("utf8")
 old="""   var msg='Montaj parțial R220: '+summary.subtitledCuts+' CUT-uri validate, '+"""
 new="""   var doubtful=summary.skippedConfirmedCuts||[];
   var doubtfulReport=doubtful.length?
       '\\nCUT-uri confirmate fără subtitrare din cauza duratei: '+
       doubtful.map(function(x){return x.cutId+' ('+x.reason+')';}).join(', ')+'.\\n':'';
   var msg='Montaj parțial R220: '+summary.subtitledCuts+' CUT-uri validate, '+"""
 s=replace(s,old,new)
 old="""       ' CUT-uri rezervate NU vor avea subtitrări.\\n'+"""
 new="""       ' CUT-uri rezervate NU vor avea subtitrări.\\n'+doubtfulReport+"""
 s=replace(s,old,new)
 old="""          status('[PREMIERE READBACK] '+r.message+' | '+r.sourceCuts+
            ' CUT-uri cu subtitrări, '+r.omitted+' CUT-uri fără audio confirmat.');"""
 new="""          status('[PREMIERE READBACK] '+r.message+' | '+r.sourceCuts+
            ' CUT-uri cu subtitrări, '+r.omitted+' CUT-uri fără audio confirmat, '+
            (summary.skippedConfirmedCuts||[]).length+' CUT-uri audio confirmate omise pentru durate nesigure.'+
            ((summary.skippedConfirmedCuts||[]).length?'\\n'+
             summary.skippedConfirmedCuts.map(function(x){return x.cutId+': '+x.reason;}).join('\\n'):''));"""
 s=replace(s,old,new)
 if 'recoverOrFallback' not in s or 'onClickCapture' not in s:
  raise ValueError("R229_BRIDGE_LOST")
 return s.encode('utf8')

def build(r230,r226,r235,output):
 # Released files only, never guess from branch candidates.
 sources={}
 for file,version,path in [(r230,"2.3.0",NAMETAG),(r226,"2.2.6",SUBS),(r235,"2.3.5",PANEL)]:
  with zipfile.ZipFile(file) as z:
   manifest=json.loads(z.read("manifest.json"))
   if manifest.get("version")!=version:raise ValueError("SOURCE_RELEASE_VERSION_CHANGED "+version)
   entries=[i for i in manifest["files"] if i["path"]==path]
   if len(entries)!=1:raise ValueError("SOURCE_FILE_MISSING "+path)
   old=z.read("payload/"+path)
   if sha(old)!=entries[0]["sha256"]:raise ValueError("SOURCE_RELEASE_SHA_MISMATCH "+path)
   sources[path]=old
 payload={NAMETAG:patch_nametag(sources[NAMETAG]),SUBS:patch_subtitles(sources[SUBS]),
         PANEL:patch_panel(sources[PANEL])}
 meta={"format":1,"version":"2.3.6","files":[
    {"path":p,"before_sha256":sha(sources[p]),"sha256":sha(payload[p])}
    for p in sorted(payload)]}
 dest=pathlib.Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.writestr("manifest.json",json.dumps(meta,indent=2,ensure_ascii=True)+"\n")
  for p,raw in sorted(payload.items()):z.writestr("payload/"+p,raw)
 with zipfile.ZipFile(dest) as z:
  assert json.loads(z.read("manifest.json"))==meta
  for p,b in payload.items():assert sha(z.read("payload/"+p))==sha(b)
 return {"version":"2.3.6","files":meta["files"],"zipSha256":sha(dest.read_bytes())}
if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--v230",required=True);ap.add_argument("--v226",required=True)
 ap.add_argument("--v235",required=True);ap.add_argument("--out",required=True)
 a=ap.parse_args()
 print(json.dumps(build(a.v230,a.v226,a.v235,a.out),indent=2))
