"""Build one verified UI-only updater patch from the already public v1.8.11 asset.
No production CEP / editorial source files are published here.
"""
import hashlib, io, json, urllib.request, zipfile
from pathlib import Path

URL="https://github.com/Sankio9/ai-video-editor-updates/releases/download/v1.8.11/AIVE_UPDATE.zip"
ARCHIVE_SHA="cbe35fc444a043059b9c473190147d3930353df51e21209f99d3c898d71396e5"
BASE_SHA="ec1bac9e38ae28310a398eda8b050d3c90b52b503307261782cadb0e317d5868"
TARGET_SHA="3892fe8efc7f0c5b53ef1db4e8b1d8579820db1bc15604b7ff0c270c2b9dacdb"

def sha(data):return hashlib.sha256(data).hexdigest()
def once(s,old,new):
    if s.count(old)!=1:raise ValueError("Unexpected base UI source; refusing patch")
    return s.replace(old,new,1)

def main():
    with urllib.request.urlopen(urllib.request.Request(URL,headers={"User-Agent":"AIVE-release-builder"}),timeout=30) as resp:
        blob=resp.read(5_000_000)
    if sha(blob)!=ARCHIVE_SHA:raise ValueError("Previous release hash mismatch")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        source=z.read("payload/cep/aive_updater_panel.js")
    if sha(source)!=BASE_SHA:raise ValueError("Previous UI hash mismatch")
    s=source.decode("utf-8")
    s=once(s,"AI Video Editor Updater R1.8.11","AI Video Editor Updater R1.9.1")
    s=once(s,"  var pyw=path.join(root,'.venv','Scripts','pythonw.exe');\n","")
    s=once(s,"    if(which==='--prepare'&&!fs.existsSync(pyw)){cb({ok:false,message:'Lipsește pythonw.exe. Actualizarea este oprită pentru a evita fereastra neagră.'});return;}\n","")
    s=once(s,"var proc=cp.spawn(which==='--prepare'?pyw:py,args,{cwd:root,windowsHide:true})","var proc=cp.spawn(py,args,{cwd:root,windowsHide:true})")
    s=once(s,"say('Disponibilă: '+r.latest+' (instalat: '+r.current+'). Apasă din nou pentru pregătire.');","say('Disponibilă: '+r.latest+' (instalat: '+r.current+'). După descărcare va apărea mesajul de salvare și închidere Premiere.');")
    s=once(s,"        btn.textContent='Actualizare pregătită';btn.disabled=true;\n        reminder(pendingVersion);","        btn.textContent='Reafișează instrucțiunile';btn.disabled=false;\n        reminder(pendingVersion);")
    s=once(s,"if(r&&r.stage==='waiting'){state='waiting';btn.textContent='Actualizare pregătită';btn.disabled=true;pendingVersion=(r.message.match(/v?\\d+\\.\\d+\\.\\d+/)||[])[0]||'';}","if(r&&r.stage==='waiting'){state='waiting';btn.textContent='Reafișează instrucțiunile';btn.disabled=false;pendingVersion=(r.message.match(/v?\\d+\\.\\d+\\.\\d+/)||[])[0]||'';reminder(pendingVersion);}")
    data=s.encode("utf-8")
    if sha(data)!=TARGET_SHA:raise ValueError("Patched UI hash differs from tested local build")
    files=[{"path":"cep/aive_updater_panel.js","sha256":sha(data),"before_sha256":BASE_SHA}]
    output=Path("dist/AIVE_UPDATE.zip");output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("payload/cep/aive_updater_panel.js",data)
        z.writestr("manifest.json",json.dumps({"format":1,"version":"1.9.1","files":files},indent=2))
    print("v1.9.1 UI-only, SHA-256 verified:",sha(output.read_bytes()))

if __name__=="__main__":main()
