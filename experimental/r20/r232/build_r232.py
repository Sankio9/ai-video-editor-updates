"""R2.3.2: fix reporter/CN subtitle segmentation + readable NameTag review.
Exactly two files, authenticated against R2.3.1 published asset.
No MOGRT writer, V1/A1, editor safety or Stable changes.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,zipfile
HERE=pathlib.Path(__file__).resolve().parent
PREVIOUS_ZIP="bb0f574b073022198a0ce7f4fb40be3182032d2f8d78bc9559a8e899b365768b"
PANEL="cep/r20_panel.js"
PARSER="tools/r230_universal.py"
def sha(x):return hashlib.sha256(x).hexdigest()
def splice_one(text,needle,replacement):
    if text.count(needle)!=1:raise ValueError("SOURCE_ANCHOR_UNEXPECTED: "+needle[:90])
    return text.replace(needle,replacement,1)
def patch_panel(old):
    source=old.decode("utf8")
    dialog="""  // R2.3.2: custom scrollable review. No truncated native JS confirm box.
  // The user explicitly decides BEFORE V4 preflight/insertion.
  function showNameTagReview(items,validCount,callback){
    if(!document.body){callback(false);return;}
    var overlay=document.createElement('div');
    overlay.setAttribute('role','dialog');
    overlay.setAttribute('aria-label','Revizuire editorială NameTag');
    overlay.style.cssText='position:fixed;inset:0;z-index:2147483640;background:rgba(0,0,0,.78);display:flex;align-items:center;justify-content:center;padding:10px;box-sizing:border-box;';
    var panel=document.createElement('div');
    panel.style.cssText='display:flex;flex-direction:column;width:100%;max-width:660px;max-height:calc(100vh - 20px);background:#2c323c;border:1px solid #7f93a9;color:#f7f7f7;border-radius:7px;box-sizing:border-box;box-shadow:0 8px 36px #0009;padding:16px;gap:10px;';
    var title=document.createElement('div');
    title.style.cssText='font-weight:700;font-size:15px;';
    title.textContent='NameTag — '+items.length+' identificări de verificat';
    panel.appendChild(title);
    var summary=document.createElement('div');
    summary.style.cssText='font-size:12px;line-height:1.5;';
    summary.textContent='Se vor crea '+validCount+' burtiere confirmate. Cele '+items.length+' identificări de mai jos vor fi omise. Nicio identitate nu va fi inventată.';
    panel.appendChild(summary);
    var scroll=document.createElement('div');
    scroll.setAttribute('role','region');
    scroll.setAttribute('aria-label','Lista completă CUT-uri neconfirmate');
    scroll.style.cssText='min-height:80px;max-height:56vh;overflow-y:auto;overscroll-behavior:contain;border:1px solid #5e6e80;border-radius:4px;padding:8px;background:#1f242c;font-size:12px;line-height:1.55;white-space:pre-wrap;overflow-wrap:anywhere;';
    for(var i=0;i<items.length;i++){
      var entry=items[i],line=document.createElement('div');
      line.style.cssText='padding:6px 3px;border-bottom:1px solid #49515e;';
      line.textContent=String(entry.cutId)+' · sursa '+String(entry.sourceCode||'?')+
        ' · paragraf '+String(entry.paragraph)+' — '+String(entry.reason||'identitate neconfirmată');
      scroll.appendChild(line);
    }
    panel.appendChild(scroll);
    var note=document.createElement('div');
    note.style.cssText='font-size:12px;color:#f6d28c;';
    note.textContent='Continuarea NU va genera burtiere pentru CUT-urile neconfirmate. Verifică lista completă înainte de a accepta.';
    panel.appendChild(note);
    var actions=document.createElement('div');
    actions.style.cssText='display:flex;justify-content:flex-end;gap:10px;flex-wrap:wrap;';
    var stop=document.createElement('button');stop.textContent='Oprește';
    var proceed=document.createElement('button');proceed.textContent='Continuă — omite '+items.length;
    stop.style.cssText='padding:8px 12px;cursor:pointer;';
    proceed.style.cssText='padding:8px 12px;background:#346b96;color:white;border:1px solid #6196bd;cursor:pointer;';
    actions.appendChild(stop);actions.appendChild(proceed);panel.appendChild(actions);
    overlay.appendChild(panel);
    var completed=false;
    function close(approved){
      if(completed)return;
      completed=true;
      if(window.removeEventListener)window.removeEventListener('keydown',keyDown,true);
      if(overlay.parentNode)overlay.parentNode.removeChild(overlay);
      callback(approved);
    }
    function keyDown(e){if(e.key==='Escape'||e.keyCode===27){if(e.preventDefault)e.preventDefault();close(false);}}
    if(window.addEventListener)window.addEventListener('keydown',keyDown,true);
    stop.onclick=function(){close(false);};
    proceed.onclick=function(){close(true);};
    overlay.onclick=function(e){if(e.target===overlay)close(false);};
    document.body.appendChild(overlay);
    if(stop.focus)stop.focus();
  }
"""
    source=splice_one(source,"  function conflict(key,inventory){",dialog+"  function conflict(key,inventory){")
    start=source.index("     var skipReport='';")
    end=source.index("     var n=0,tok='';",start)
    if start<0 or end<start:raise ValueError("NAMETAG_BLOCK_NOT_FOUND")
    original=source[start:end]
    assert original.count("if(!window.confirm(question))")==1
    replacement="""     var skipReport='',reviewItems=[];
     if(cfg.num==='03'&&plan.skipped.length){
       skipReport=plan.skipped.map(function(x){return String(x.kind)+' · '+String(x.cutId)+
         ' (paragraful '+String(x.paragraph)+', sursa '+String(x.sourceCode||'?')+') — '+String(x.reason);}).join('\\n');
       reviewItems=plan.skipped.filter(function(x){return x.kind==='REVIEW_MISSING_IDENTITY';});
       if(!reviewItems.length)status(key,'SKIP_EDITORIAL: '+plan.skipped.length+' fragmente fără NameTag.\\n'+skipReport);
     }
     function proceedAfterReview(){
"""
    source=source[:start]+replacement+source[end:]
    anchor="""       }next();
     });
   }
   if(key==='subs')withPlan"""
    replacement="""       }next();
     });
     }
     if(reviewItems.length){
       showNameTagReview(reviewItems,plan.items,function(approved){
         if(!approved){
           status(key,'OPRIT: omiterile NameTag nu au fost aprobate. V4 neatinsă.\\n'+skipReport);
           finish();return;
         }
         // The DOCX/plan is still checked by existing per-clip SHA gates.
         status(key,'REVIEW APROBAT: '+reviewItems.length+' identificări omise.\\n'+skipReport);
         proceedAfterReview();
       });
     }else proceedAfterReview();
   }
   if(key==='subs')withPlan"""
    source=splice_one(source,anchor,replacement)
    if "if(!window.confirm(question))" in source:raise ValueError("NATIVE_TRUNCATED_CONFIRM_REMAINS")
    if "onClickCapture" not in source or "recoverOrFallback" not in source:
        raise ValueError("R220_BRIDGE_LOST")
    return source.encode("utf8")

def build(previous,out):
    blob=pathlib.Path(previous).read_bytes()
    if sha(blob)!=PREVIOUS_ZIP:raise ValueError("PREVIOUS_BETA_ARCHIVE_SHA_CHANGED")
    with zipfile.ZipFile(previous) as z:
        m=json.loads(z.read("manifest.json"))
        if m.get("version")!="2.3.1" or m.get("format")!=1:
            raise ValueError("PREVIOUS_MANIFEST_UNEXPECTED")
        prior={}
        for item in m["files"]:
            content=z.read("payload/"+item["path"])
            if sha(content)!=item["sha256"]:raise ValueError("PREVIOUS_FILE_SHA_CHANGED")
            prior[item["path"]]=content
    if set(prior)!={PANEL,PARSER}:raise ValueError("PREVIOUS_FILE_SCOPE_UNEXPECTED")
    parser=(HERE/"candidate/tools/r230_universal.py").read_bytes()
    compile(parser,PARSER,"exec")
    if b"def styled_parts" not in parser or b"SKIP_NARRATION" not in parser:
        raise ValueError("R232_PARSER_FEATURE_MISSING")
    changed={PANEL:patch_panel(prior[PANEL]),PARSER:parser}
    info={"format":1,"version":"2.3.2","files":[
        {"path":p,"before_sha256":sha(prior[p]),"sha256":sha(changed[p])}
        for p in sorted(changed)]}
    path=pathlib.Path(out);path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(info,ensure_ascii=True,indent=2)+"\n")
        for name,data in sorted(changed.items()):z.writestr("payload/"+name,data)
    with zipfile.ZipFile(path) as z:
        assert set(z.namelist())=={"manifest.json",*(("payload/"+p) for p in changed)}
        assert json.loads(z.read("manifest.json"))==info
        for name,data in changed.items():
            assert sha(z.read("payload/"+name))==sha(data)
    return {"files":info["files"],"version":"2.3.2",
            "asset_sha256":sha(path.read_bytes()),"bytes":path.stat().st_size}
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--prior",required=True)
    parser.add_argument("--output",required=True)
    options=parser.parse_args()
    print(json.dumps(build(options.prior,options.output),indent=2))
