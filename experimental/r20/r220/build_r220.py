"""R2.2.0 Beta: exact-source verified incremental update of Montage 01 only.

The update adds one-click integrated ASR capture, contextual approval and a
test-sequence-only Premiere writer. It never modifies release/next.json and
preserves other modules and the original Stable v1.9.13.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile,pathlib

ROOT=pathlib.Path(__file__).resolve().parent
PREVIOUS_ZIP_SHA="5cb8fd4e65ecc77d148aa78a5c98eaff5cf13c1977ed84537f52f5991d257ffd"
ORIGINAL_WORKFLOW_SHA="fcafbea9854bc7176b68342473d9b27f362a8cfc6e3334063532c1b16df81dd9"
OLD_WORKFLOW="cep/r193_workflow.js"
PIPELINE="tools/r193_pipeline.py"
ADDITIONS={
 "tools/r220_montage_plan.py":ROOT/"tools/r220_montage_plan.py",
 "tools/r220_capture.py":ROOT/"tools/r220_capture.py",
 "tools/r220_montage_runner.py":ROOT/"tools/r220_montage_runner.py",
 "cep/jsx/r220_montage_writer.jsx":ROOT/"cep/jsx/r220_montage_writer.jsx",
 "cep/jsx/r220_media_probe.jsx":ROOT/"cep/jsx/r220_media_probe.jsx",
}
def digest(x):return hashlib.sha256(x).hexdigest()
def replace_once(text,a,b):
    if text.count(a)!=1:raise ValueError("Unexpected original source anchor: "+a[:55])
    return text.replace(a,b,1)
def read_asset(p,version,expected_sha=None):
    p=pathlib.Path(p)
    if expected_sha and digest(p.read_bytes())!=expected_sha:
        raise ValueError("Published release ZIP SHA mismatch")
    with zipfile.ZipFile(p) as z:
        manifest=json.loads(z.read("manifest.json"))
        if manifest.get("version")!=version or manifest.get("format")!=1:
            raise ValueError("Wrong release version "+version)
        out={}
        for row in manifest["files"]:
            data=z.read("payload/"+row["path"])
            if digest(data)!=row["sha256"]:
                raise ValueError("Broken release asset "+row["path"])
            out[row["path"]]=data
        return out
def build(prior,workflow,output):
    previous=read_asset(prior,"2.1.3",PREVIOUS_ZIP_SHA)
    older=read_asset(workflow,"1.9.10")
    if OLD_WORKFLOW not in older or digest(older[OLD_WORKFLOW])!=ORIGINAL_WORKFLOW_SHA:
        raise ValueError("Actual CEP 01 version is not the verified v1.9.10")
    if PIPELINE not in previous:
        raise ValueError("Previous 2.1.3 pipeline missing")
    original=previous[PIPELINE]
    code=original.decode("utf8")
    code=replace_once(code,
      "cached=(previous.get('fingerprint')==digest and",
      "cached=(os.environ.get('AIVE_R220_CAPTURE')!='1' and previous.get('fingerprint')==digest and")
    code=replace_once(code,
      "                   # Runs BEFORE old_write: unsafe plans never overwrite good JSON.",
      """                   # R2.2 capture stops the legacy writer BEFORE ANY plan mutation.
                   if os.environ.get('AIVE_R220_CAPTURE')=='1':
                       from r220_capture import capture
                       capture(plan,mapping,docx,os.environ['AIVE_R220_MEDIA_JSON'],
                               os.environ['AIVE_R220_SEQUENCE_ID'])
                   # Runs BEFORE old_write: unsafe plans never overwrite good JSON.""")
    for marker in ("validate_speech_only(plan)","r143_build.is_safe=guarded_safe",
                   "r143_build.write_results=guarded_write",
                   "r143_build.write_results=old_write",
                   "R220_CAPTURE","r213_second_pass"):
        if marker not in code:
            raise ValueError("R1.9.13 guard not retained: "+marker)
    panel=older[OLD_WORKFLOW].decode("utf8")
    panel=replace_once(panel,
      "item.onclick=function(){run(m);};",
      "item.onclick=function(){if(m.key==='cut' && window.AIVE_R220_UI)window.AIVE_R220_UI.start();else run(m);};")
    addon=(ROOT/"cep/r220_montage_panel.js").read_text("utf8")
    for marker in ("runWorker(m,doc,media,done)","buildLegacy(m,plan)",
                   "m.key==='cut' && window.AIVE_R220_UI","r220_montage_runner.py",
                   "CONTINUE_WITH_PLACEHOLDERS","last_report.json"):
        if marker not in panel+"\n"+addon:raise ValueError("Missing single-button UX invariant: "+marker)
    panel+="\n"+addon+"\n"
    files={PIPELINE:code.encode("utf8"),OLD_WORKFLOW:panel.encode("utf8")}
    files.update({dest:path.read_bytes() for dest,path in ADDITIONS.items()})
    expected=set(ADDITIONS)|{PIPELINE,OLD_WORKFLOW}
    if set(files)!=expected:raise ValueError("Unexpected release allowlist")
    # Syntax and runtime invariants verified in GitHub CI as well.
    for p in files:
        if not 500<len(files[p])<200000:raise ValueError("Payload bounds failed "+p)
        if p.endswith(".py"):compile(files[p],p,"exec")
    rows=[]
    for dest,data in sorted(files.items()):
        before=digest(original) if dest==PIPELINE else (ORIGINAL_WORKFLOW_SHA if dest==OLD_WORKFLOW else None)
        rows.append({"path":dest,"sha256":digest(data),"before_sha256":before})
    manifest={"format":1,"version":"2.2.0","files":rows}
    output=pathlib.Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,indent=2)+"\n")
        for dest,data in sorted(files.items()):
            z.writestr("payload/"+dest,data)
    with zipfile.ZipFile(output) as z:
        if set(z.namelist())!={"manifest.json",*(("payload/"+p) for p in files)}:
            raise ValueError("Unsafe extra file")
        for row in rows:
            if digest(z.read("payload/"+row["path"]))!=row["sha256"]:
                raise ValueError("Corrupt packed payload "+row["path"])
    return {"version":"2.2.0","requires":"2.1.3","files":len(files),
            "zip_sha256":digest(output.read_bytes()),"size":output.stat().st_size}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--prior",required=True)
    p.add_argument("--workflow",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args();print(json.dumps(build(a.prior,a.workflow,a.output),indent=2))
