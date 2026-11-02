"""R2.3.1 independent DOCX and panel handshake repair.

Input pinned REAL previously published Beta ZIP assets:
R2.2.9 owns installed cep/r20_panel.js
R2.3.0 owns installed tools/r230_universal.py.
The R2.3.1 update alters ONLY these 2 files with before SHA.
R2.1.1 legacy DOCX analyzer remains byte-for-byte untouched.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,zipfile
SOURCE=pathlib.Path(__file__).resolve().parent
ZIP229_SHA="80d73162aa15019f80b615fb9b0709db0914e3d774d21fd89b1556c2ffb5411c"
ZIP230_SHA="34a824f71d228d7b45a72314d1a6a3c6edf227081be976c7a608d4f3a246d6af"
UNIVERSAL_BEFORE="18aa28e9cde7d9ebb3ec349b7a5746844088e8764feda1c8128f7f9938afca4d"
UNIVERSAL_AFTER="a939e588fa4c458c05ceaae2044539564a21ba4c0975c9294089b518ed84d770"
PANEL="cep/r20_panel.js"
UNIVERSAL="tools/r230_universal.py"
OLD_GATE="""if(plan.generatorVersion!=='R2.1.1-auto-preflight-readable'||
          r.generatorVersion!==plan.generatorVersion)"""
NEW_GATE="""var validEngine=plan.generatorVersion==='R2.1.1-auto-preflight-readable';
        if(plan.generatorVersion==='R2.3-UNIVERSAL-DOCX-9-FORMATS'){
          var universalFile=path.join(root,'tools','r230_universal.py');
          validEngine=fs.existsSync(universalFile)&&sha(universalFile)==='a939e588fa4c458c05ceaae2044539564a21ba4c0975c9294089b518ed84d770';
        }
        if(!validEngine||r.generatorVersion!==plan.generatorVersion)"""
def sha(x):return hashlib.sha256(x).hexdigest()
def read(path,version,archive_sha):
    raw=pathlib.Path(path).read_bytes()
    if sha(raw)!=archive_sha:raise ValueError("RELEASE_ZIP_SHA_MISMATCH_"+version)
    with zipfile.ZipFile(path) as z:
        m=json.loads(z.read("manifest.json"))
        if m.get("version")!=version or m.get("format")!=1:raise ValueError("RELEASE_VERSION_INVALID")
        files={}
        for row in m["files"]:
            b=z.read("payload/"+row["path"])
            if sha(b)!=row["sha256"]:raise ValueError("RELEASE_FILE_SHA_MISMATCH")
            files[row["path"]]=b
        return files
def build(release229,release230,output):
    before_panel=read(release229,"2.2.9",ZIP229_SHA)[PANEL]
    before_universal=read(release230,"2.3.0",ZIP230_SHA)[UNIVERSAL]
    if sha(before_universal)!=UNIVERSAL_BEFORE:raise ValueError("UNEXPECTED_UNIVERSAL_BASELINE")
    old=before_panel.decode("utf8")
    if old.count(OLD_GATE)!=1:
        i=old.find("ENGINE_VERSION_MISMATCH")
        print("ACTUAL_ENGINE_GATE_SNIPPET",repr(old[max(0,i-520):i+155]) if i>=0 else "NO_ENGINE_VERSION_MISMATCH_TEXT")
        raise ValueError("EXPECTED_LEGACY_GATE_NOT_FOUND")
    after_panel=old.replace(OLD_GATE,NEW_GATE,1)
    # Visible confirmation of correct CEP bridge; independent module remains
    # unchanged, and R220 readback capability is not touched.
    after_panel=after_panel.replace("R2.2.9 BETA","R2.3.1 BETA")
    if "R2.3.1 BETA" not in after_panel or "recoverOrFallback" not in after_panel:
        raise ValueError("PANEL_HOOK_OR_R220_BRIDGE_MISSING")
    if "onClickCapture" not in after_panel or "r207OmitStruck" not in after_panel:
        raise ValueError("APPROVED_PANEL_FEATURE_MISSING")
    after_universal=(SOURCE/"candidate/tools/r230_universal.py").read_bytes()
    if sha(after_universal)!=UNIVERSAL_AFTER:raise ValueError("PATCHED_UNIVERSAL_SOURCE_SHA_CHANGED")
    compile(after_universal,UNIVERSAL,"exec")
    # The old generator requires these exact enum values. Matching them is
    # mandatory; never reduce/skip the independent graphics safety checks.
    s=after_universal.decode("utf8")
    assert "INCLUDE_STRUCK" in s and "NOT_APPLICABLE" in s
    assert "R2.3-UNIVERSAL-DOCX-9-FORMATS" in s
    payload={PANEL:after_panel.encode("utf8"),UNIVERSAL:after_universal}
    pre={PANEL:sha(before_panel),UNIVERSAL:sha(before_universal)}
    meta={"format":1,"version":"2.3.1","files":[
        {"path":p,"before_sha256":pre[p],"sha256":sha(b)}
        for p,b in sorted(payload.items())]}
    path=pathlib.Path(output);path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(meta,indent=2,ensure_ascii=True)+"\n")
        for p,b in sorted(payload.items()):z.writestr("payload/"+p,b)
    with zipfile.ZipFile(path) as z:
        assert set(z.namelist())=={"manifest.json",*(("payload/"+p) for p in payload)}
        assert json.loads(z.read("manifest.json"))==meta
        for p,b in payload.items():assert sha(z.read("payload/"+p))==sha(b)
    return {"release":"v2.3.1","asset":"AIVE_UPDATE.zip","files":meta["files"],
            "archiveSHA256":sha(path.read_bytes()),"bytes":path.stat().st_size}
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--v229",required=True)
    parser.add_argument("--v230",required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.v229,args.v230,args.out),indent=2))
