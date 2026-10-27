"""R1.9.10: show missing source IDs in red (UI only)."""
from __future__ import annotations
import hashlib, json, zipfile
from pathlib import Path
from build_r198 import build as build_r198

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/AIVE_UPDATE.zip'
PATH='cep/r193_workflow.js'
BEFORE='b191306499a2fbb0077dd48e7e2d6b07c8f87075c9e03437e86a4cce0f611222'
AFTER='fcafbea9854bc7176b68342473d9b27f362a8cfc6e3334063532c1b16df81dd9'
RENDER="""// R1.9.10: highlight missing media identifiers without altering validation or timeline.
 function renderMediaStatus(target,message){
   target.textContent='';
   var missed=[],seen={},match,re=/(?:^|[\\s;])(\\d{4})\\s*:\\s*0\\s+surse\\b/g;
   if(message.indexOf('Verifică importul în Project Panel')>=0){
     while((match=re.exec(message))!==null){
       if(!seen[match[1]]){seen[match[1]]=true;missed.push(match[1]);}
     }
   }
   if(missed.length){
     var warning=document.createElement('div');warning.className='r1910-missing-media';
     var heading=document.createElement('strong');
     heading.textContent=missed.length===1?'FIȘIER VIDEO NEGĂSIT':'FIȘIERE VIDEO NEGĂSITE';
     warning.appendChild(heading);
     for(var i=0;i<missed.length;i++){
       var code=document.createElement('span');code.className='r1910-missing-code';
       code.textContent=missed[i];warning.appendChild(code);
     }
     target.appendChild(warning);
     var details=document.createElement('div');details.textContent=message;
     target.appendChild(details);
   }else{target.textContent=message;}
 }
"""
CSS=""".r1910-missing-media{margin:7px 0;padding:9px 11px;border:1px solid #d95c66;
 background:rgba(184,42,54,.16);color:#ff838a;border-radius:5px;line-height:1.5}
 .r1910-missing-media strong{display:block;font-size:12px;letter-spacing:.25px}
 .r1910-missing-code{display:inline-block;color:#fff;background:#b92f3c;
 margin:5px 5px 0 0;padding:2px 9px;font-weight:700;border-radius:3px}
 """

def replace_one(text,old,new):
    if text.count(old)!=1:raise ValueError('Unexpected UI code')
    return text.replace(old,new)

def build():
    build_r198()
    with zipfile.ZipFile(OUT) as z:
        old=z.read('payload/'+PATH)
    if hashlib.sha256(old).hexdigest()!=BEFORE:raise ValueError('Wrong installed code hash')
    js=old.decode('utf8')
    needle=" function say(m,s){var node=E(m.key+'R193Status');if(node)node.textContent=s;"
    js=replace_one(js,needle,RENDER+" function say(m,s){var node=E(m.key+'R193Status');if(node)renderMediaStatus(node,String(s));")
    needle=".r192-launch{font-weight:bold;padding:13px 10px}'"
    js=replace_one(js,needle,".r192-launch{font-weight:bold;padding:13px 10px}"+CSS.replace('\\n',' ')+"'")
    payload=js.encode('utf8')
    if hashlib.sha256(payload).hexdigest()!=AFTER:raise ValueError('New UI hash mismatch')
    manifest={'format':1,'version':'1.9.10','files':[{'path':PATH,'before_sha256':BEFORE,'sha256':AFTER}]}
    with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json',json.dumps(manifest,indent=2)+'\\n')
        z.writestr('payload/'+PATH,payload)
    print('R1.9.10 ready:',OUT.stat().st_size,'bytes')
if __name__=='__main__':build()
