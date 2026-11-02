"""R2.2.2 Beta cumulative, source-hash compatible with the real user's panel.

The user supplied D:\\AI-Video-Editor\\cep\\r193_workflow.js; independently
verified SHA256 b1913064... matches documented BEFORE state of the
published v1.9.10 patch, NOT its AFTER state fcafbea9....

DO NOT turn off SHA protection. Rebase an unchanged, already-tested public
R2.2.0 Montage payload on that exact earlier workflow SHA, include R2.2.1
UTF-8 updater fixes, and retain every other independent module unchanged.
"""
import argparse,hashlib,json,pathlib,zipfile

SOURCE_SHA_R220="2dec078fa67cd75de67a24090d20258720cd8b88a48672d4eebbfae64002b00c"
SOURCE_SHA_R221="16fac7181a9bb04bebec4e5e25b970c3e262eb19733728a1b80cb2517f9c009f"
USER_EXACT_SHA="b191306499a2fbb0077dd48e7e2d6b07c8f87075c9e03437e86a4cce0f611222"
OLDER_WORKFLOW_SHA="fcafbea9854bc7176b68342473d9b27f362a8cfc6e3334063532c1b16df81dd9"
FILE="cep/r193_workflow.js"
EXPECTED_R220={
    "cep/r193_workflow.js","tools/r193_pipeline.py",
    "tools/r220_montage_plan.py","tools/r220_capture.py",
    "tools/r220_montage_runner.py",
    "cep/jsx/r220_montage_writer.jsx","cep/jsx/r220_media_probe.jsx",
}
EXPECTED_R221={"updater/beta.py","cep/aive_updater_beta.js"}

def sha(x):return hashlib.sha256(x).hexdigest()
def read(name,version,digest):
    name=pathlib.Path(name)
    data=name.read_bytes()
    if sha(data)!=digest:raise ValueError("Incorrect released archive checksum for "+version)
    with zipfile.ZipFile(name) as z:
        m=json.loads(z.read("manifest.json"))
        if m.get("version")!=version or m.get("format")!=1:
            raise ValueError("Unexpected released manifest version")
        blobs={}
        for row in m["files"]:
            p=row["path"]
            if p in blobs or not p.startswith(("cep/","tools/","updater/")):
                raise ValueError("Unsafe or duplicate release file "+p)
            b=z.read("payload/"+p)
            if sha(b)!=row["sha256"]:raise ValueError("Corrupt payload "+p)
            blobs[p]=(row,b)
        if set(z.namelist())!={"manifest.json",*(("payload/"+p) for p in blobs)}:
            raise ValueError("Archive contains unexpected files")
        return blobs

def build(previous,updater,output):
    montage=read(previous,"2.2.0",SOURCE_SHA_R220)
    utf8=read(updater,"2.2.1",SOURCE_SHA_R221)
    if set(montage)!=EXPECTED_R220 or set(utf8)!=EXPECTED_R221:
        raise ValueError("Unexpected release payload allowlist")
    assert not (set(montage)&set(utf8))
    if montage[FILE][0]["before_sha256"]!=OLDER_WORKFLOW_SHA:
        raise ValueError("Original v2.2.0 workflow before hash mismatch")
    new_code=montage[FILE][1].decode("utf8")
    if "window.AIVE_R220_UI.start()" not in new_code:
        raise ValueError("Montage 01 one-click R220 not integrated")
    if "runWorker(m,doc,media,done)" not in new_code:
        raise ValueError("Original stable workflow lost")
    if "if(m.key==='cut'" not in new_code:
        raise ValueError("Missing conditional 01 Montage handler")
    if b"PYTHONUTF8:'1'" not in utf8["cep/aive_updater_beta.js"][1]:
        raise ValueError("UTF8 permanent updater missing")
    if b"ensure_ascii=True" not in utf8["updater/beta.py"][1]:
        raise ValueError("Python codepage fix missing")
    # All other recorded before SHA256 values are preserved EXACTLY.
    merged={**montage,**utf8}
    rows=[]
    for filename,(meta,data) in sorted(merged.items()):
        expected_before=USER_EXACT_SHA if filename==FILE else meta.get("before_sha256")
        if expected_before is not None and len(expected_before)!=64:
            raise ValueError("Bad original SHA for "+filename)
        rows.append({"path":filename,"sha256":sha(data),"before_sha256":expected_before})
        if filename.endswith(".py"):compile(data,filename,"exec")
    manifest={"format":1,"version":"2.2.2","files":rows}
    out=pathlib.Path(output);out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,indent=2,ensure_ascii=True)+"\n")
        for filename,(_,data) in sorted(merged.items()):
            z.writestr("payload/"+filename,data)
    with zipfile.ZipFile(out) as z:
        assert set(z.namelist())=={"manifest.json",*(("payload/"+p) for p in merged)}
        assert json.loads(z.read("manifest.json"))==manifest
        for r in rows:
            assert sha(z.read("payload/"+r["path"]))==r["sha256"]
    return {"version":"2.2.2","files":len(rows),"workflowBeforeSHA256":USER_EXACT_SHA,
            "workflowAfterSHA256":sha(montage[FILE][1]),
            "packageSHA256":sha(out.read_bytes()),"sizeBytes":out.stat().st_size}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--r220",required=True)
    p.add_argument("--r221",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    print(json.dumps(build(a.r220,a.r221,a.output),indent=2))
