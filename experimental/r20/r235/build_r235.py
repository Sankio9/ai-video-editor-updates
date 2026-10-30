"""R235 source-guarded hotfix for user-selected V5 overwrite.
Safe semantic: clone active sequence and ONLY delete six existing MOGRTs
on verified clone, then use the unchanged R20 writer for V5 insertion.
Source/original sequence is never mutated. No QE. Installer SHA unchanged.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
ARCHIVE_SHA="d631e5f7af8a9246b8f04c1f28e57c0f620bd83f7f4616b46a9215eb51a554bf"
PANEL="cep/r20_panel.js"
NEW="cep/jsx/r235_v5_clone.jsx"
def hash(b):return hashlib.sha256(b).hexdigest()
def one(s,a,b):
    if s.count(a)!=1:raise ValueError("R235_SOURCE_ANCHOR_MISMATCH "+a[:80])
    return s.replace(a,b,1)
def patch_panel(s):
    # R235 does NOT rewrite the approved module run/preflight/buildOne paths.
    # New helper only runs when the user explicitly selects replace V5.
    find="function conflict(key,inventory){"
    helper="""function evalR235(method,args,cb){
   var ext=decodeURIComponent(cep.getSystemPath('extension')).replace(/\\\\/g,'/');
   var file=ext+'/jsx/r235_v5_clone.jsx';
   var loader='$.evalFile(new File('+JSON.stringify(file)+'))';
   cep.evalScript(loader,function(loaded){
     if(String(loaded).indexOf('EvalScript error')!==-1){cb(Error('Nu pot încărca verificatorul de clonare V5: '+loaded));return;}
     cep.evalScript('$._AIVE_R235_V5_.'+method+'('+args.map(JSON.stringify).join(',')+')',
       function(raw){try{cb(null,JSON.parse(raw));}catch(e){cb(Error('Răspuns V5 invalid: '+String(raw).slice(0,150)));}});
   });
 }
 var r235CopyName='';
 """
    s=one(s,find,helper+"function conflict(key,inventory,plan){")
    before="""overwrite.textContent='Suprascrie materialele de pe V5';"""
    s=one(s,before,"""overwrite.textContent='Suprascrie V5 într-o copie sigură';""")
    old="""overwrite.onclick=function(){if(!window.confirm('ATENȚIE: suprascrierea V5 este distructivă. Confirmi că ai făcut backup al proiectului de test?'))return;
     status(key,'OPRIT PREVENTIV: executarea suprascrierii distructive nu este certificată în Premiere. V5 rămâne neschimbată.');};"""
    new="""overwrite.onclick=function(){
     if(busy||key!=='caps'||!plan||!plan.path||!fs.existsSync(plan.path)){status(key,'OPRIT: planul V5 a expirat. Reia Generare V5.');return;}
     if(!window.confirm('Voi crea automat o COPIE a secvenței actuale și voi înlocui V5 NUMAI acolo. Originalul rămâne intact. Confirmi?'))return;
     var beforeDoc=docx(),beforeHash='',beforePlan='';
     try{if(!fileValid(beforeDoc))throw Error('DOCX invalid');beforeHash=sha(beforeDoc);beforePlan=sha(plan.path);}
     catch(e){status(key,'OPRIT: '+e.message);return;}
     busy=true;progress('Creez și verific copia secvenței V5',0,0);status(key,'Clonare și verificare V5. Originalul va rămâne neatins.');
     evalR235('prepare',[plan.path,JSON.stringify(inventory)],function(error,res){
       if(error||!res||!res.ok){
         status(key,'OPRIT V5: '+(error?error.message:res&&res.message||'Clonarea a eșuat')+
           '\\\\nOriginalul nu a fost selectat pentru ștergere. Dacă a fost creată o copie parțială, nu o utiliza.');
         finish();return;
       }
       try{if(docx()!==beforeDoc||sha(beforeDoc)!==beforeHash||sha(plan.path)!==beforePlan)
           throw Error('DOCX sau planul s-au schimbat; nu inserez pe copia secvenței');
         if(!res.copySequence||res.copySequence===res.originalSequence)
           throw Error('Identitatea copiei V5 nu este sigură');
       }catch(e){status(key,'OPRIT: '+e.message+'; originalul intact, copia necesită verificare.');finish();return;}
       var option=E('r20Position_caps');if(!option){status(key,'OPRIT: controlul V5 lipsește.');finish();return;}
       option.value='zero';r235CopyName=String(res.copyName||'copie [AIVE V5 REPLACE]');
       status(key,'Copia verificată: '+r235CopyName+' · '+res.removed+' MOGRT eliminate DOAR din copie. Inserez noul V5 de la 00:00.');
       finish();
       run('caps',null);
     });
   };"""
    s=one(s,old,new)
    s=one(s,"conflict(key,r.inventory||[]);finish();return;","conflict(key,r.inventory||[],plan);finish();return;")
    line="""status(key,'[PREMIERE READBACK] '+done.message+"""
    s=one(s,line,"""status(key,'[PREMIERE READBACK] '+done.message+
                (key==='caps'&&r235CopyName?'\\\\nV5 înlocuit în copia: '+r235CopyName+' — secvența originală rămâne neatinsă.':'')+""")
    for invariant in ("onClickCapture","recoverOrFallback","showNameTagReview","noContentStatus",
                      "ENGINE_VERSION_MISMATCH","evalR20('buildOne'","evalR20('rollback'"):
        if invariant not in s:raise ValueError("R235_LEGACY_SAFETY_LOST "+invariant)
    if "executarea suprascrierii distructive nu este certificată" in s:
        raise ValueError("FAKE_OVERWRITE_HANDLER_REMAINS")
    return s
def build(prior,out):
    b=pathlib.Path(prior).read_bytes()
    if hash(b)!=ARCHIVE_SHA:raise ValueError("R234_RELEASE_SHA_MISMATCH")
    with zipfile.ZipFile(prior) as z:
        m=json.loads(z.read('manifest.json'))
        if m.get("format")!=1 or m.get("version")!="2.3.4":raise ValueError("PREVIOUS_VERSION_UNEXPECTED")
        r={row["path"]:row for row in m["files"]}
        if PANEL not in r:raise ValueError("PANEL_NOT_IN_PREVIOUS_RELEASE")
        original=z.read("payload/"+PANEL)
        if hash(original)!=r[PANEL]["sha256"]:raise ValueError("PANEL_RELEASE_PAYLOAD_SHA_MISMATCH")
    changed=patch_panel(original.decode('utf8')).encode('utf8')
    helper=(ROOT/"cep/jsx/r235_v5_clone.jsx").read_bytes()
    if b"source.clone()" not in helper or b"item.remove(false,false)" not in helper:
        raise ValueError("CLONE_HELPER_MISSING")
    if b"app.enableQE" in helper or b"app.enableQE" in changed:
        raise ValueError("QE_FORBIDDEN")
    files={PANEL:changed,NEW:helper}
    meta={"format":1,"version":"2.3.5","files":[
       {"path":p,"before_sha256":hash(original) if p==PANEL else None,"sha256":hash(content)}
       for p,content in sorted(files.items())]}
    result=pathlib.Path(out);result.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(result,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(meta,ensure_ascii=True,indent=2)+"\n")
        for p,b in sorted(files.items()):z.writestr("payload/"+p,b)
    with zipfile.ZipFile(result) as z:
        assert json.loads(z.read("manifest.json"))==meta
        assert set(z.namelist())=={"manifest.json","payload/"+PANEL,"payload/"+NEW}
        for p,b in files.items():assert hash(z.read("payload/"+p))==hash(b)
    return {"version":"2.3.5","files":meta["files"],
            "zip_sha256":hash(result.read_bytes()),"size":result.stat().st_size}
if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument("--prior",required=True);a.add_argument("--out",required=True)
    p=a.parse_args()
    print(json.dumps(build(p.prior,p.out),indent=2))
