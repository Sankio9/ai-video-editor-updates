"""R2.3.3: safe empty DOCX analysis + interpreter diagnostics, never blind V3/V4/V5 writes.
Base: exact published v2.3.2. Two-file SHA-before guarded update; Stable 1.9.13 intact.
"""
from __future__ import annotations
import hashlib,json,zipfile,argparse,pathlib
HERE=pathlib.Path(__file__).resolve().parent
OLD_ZIP_SHA="aee27e237918e5a031ae0a7174554d2e81f1eb48943d9a70e9c40196fb18f662"
PANEL="cep/r20_panel.js"
PARSER="tools/r230_universal.py"
def sha(b):return hashlib.sha256(b).hexdigest()
def single(s,old,new):
 if s.count(old)!=1:raise ValueError("UNEXPECTED_CODE_ANCHOR "+old[:85])
 return s.replace(old,new,1)
def patch_panel(raw,new_sha):
 s=raw.decode('utf8')
 # R2.3.1 original strict engine handshake remains enabled. Update ONLY
 # the approved SHA for our new built-in universal parser.
 s=single(s,"a939e588fa4c458c05ceaae2044539564a21ba4c0975c9294089b518ed84d770",new_sha)
 s=s.replace("R2.3.2 BETA","R2.3.3 BETA")
 s=single(s,"strikeAudit:plan.strikeAudit,strikeAnalysisReady:plan.strikeAnalysisReady});",
   "strikeAudit:plan.strikeAudit,strikeAnalysisReady:plan.strikeAnalysisReady,contentSummary:plan.contentSummary||null});")
 # No automatic 'empty plan' validat(e)/buildOne call. For real no-data
 # without a clear script mark, the user receives a precise diagnosis.
 const_marker=" function run(key,verified){"
 helper="""  function noContentStatus(doc,mod,plan){
    var a=plan.contentSummary||{},base=path.basename(doc||'necunoscut.docx');
    var desc=mod==='02'?'Nu s-au identificat replici pentru V3.':
             mod==='03'?'Nu există perechi nume + funcție verificate pentru V4.':
             'Nu există cartoane declarate/uppercase pentru V5.';
    return 'NIMIC DE INSERAT — '+desc+'\\nDOCX: '+base+
      ' · paragrafe: '+String(a.paragraphs||0)+
      ' · rânduri tabel: '+String(a.tables||0)+
      ' · declarații: '+String(a.speech||0)+
      ' · identități: '+String(a.identified||0)+
      ' · cartoane: '+String(a.cartons||0)+
      '.\\nVerifică scenariul selectat în modulul 00. Timeline-ul este neatins.';
  }
"""
 s=single(s,const_marker,helper+const_marker)
 first="""     if(key==='subs'&&strikeOption&&strikeOption.checked!==omitStruck){status(key,'OPRIT: bifa de text tăiat s-a schimbat în timpul pregătirii. Nicio inserare.');finish();return;}"""
 s=single(s,first,first+"""
     if(plan.items===0){
       status(key,noContentStatus(doc,cfg.num,plan));
       finish();return;
     }""")
 second="""      if(!plan.strikeAnalysisReady||!fs.existsSync(plan.path)||sha(plan.path)!==plan.planSha||"""
 s=single(s,second, """      if(plan.items===0){
        status('subs',noContentStatus(doc,'02',plan));
        finish();return;
      }
      if(plan.contentSummary && plan.contentSummary.autoCn &&
         !window.confirm('DOCX fără marcaje de sincron. Au fost identificate posibile fraze CN. Adaug subtitrări Italic cu durate estimative pe V3?')){
        status('subs','OPRIT: CN fără marcaje nu a fost aprobat. V3 neatinsă.');
        finish();return;
      }
"""+second)
 for invariant in ("ENGINE_VERSION_MISMATCH","showNameTagReview","onClickCapture","recoverOrFallback","evalR20('rollback'","sha(plan.path)!==plan.planSha"):
  if invariant not in s:raise ValueError("LEGACY_SAFETY_MISSING "+invariant)
 return s.encode('utf8')
def build(previous,out):
 archive=pathlib.Path(previous).read_bytes()
 if sha(archive)!=OLD_ZIP_SHA:raise ValueError("RELEASE_2_3_2_SHA_CHANGED")
 with zipfile.ZipFile(previous) as z:
  meta=json.loads(z.read('manifest.json'))
  if meta.get('version')!='2.3.2' or meta.get('format')!=1:raise ValueError("OLD_MANIFEST_UNEXPECTED")
  old={}
  for row in meta['files']:
   content=z.read('payload/'+row['path'])
   if sha(content)!=row['sha256']:raise ValueError("OLD_PAYLOAD_SHA")
   old[row['path']]=content
 if set(old)!={PANEL,PARSER}:raise ValueError("OLD_PAYLOAD_UNEXPECTED")
 parser=(HERE/'candidate/tools/r230_universal.py').read_bytes()
 compile(parser,PARSER,'exec')
 if b"contentSummary" not in parser or b"AUTO_CN_PLAIN_SCRIPT_REVIEW" not in parser:
  raise ValueError("NEW_DIAGNOSTIC_MISSING")
 patched={PANEL:patch_panel(old[PANEL],sha(parser)),PARSER:parser}
 m={"format":1,"version":"2.3.3","files":[
  {"path":p,"before_sha256":sha(old[p]),"sha256":sha(patched[p])}
  for p in sorted(patched)]}
 destination=pathlib.Path(out);destination.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.writestr("manifest.json",json.dumps(m,indent=2,ensure_ascii=True)+'\n')
  for p,b in sorted(patched.items()):z.writestr("payload/"+p,b)
 with zipfile.ZipFile(destination) as z:
  assert json.loads(z.read('manifest.json'))==m
  for row in m['files']:assert sha(z.read('payload/'+row['path']))==row['sha256']
 return {"version":"2.3.3","assets":m['files'],
         "archive_sha256":sha(destination.read_bytes())}
if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument('--prior',required=True);ap.add_argument('--out',required=True)
 a=ap.parse_args();print(json.dumps(build(a.prior,a.out),indent=2))
