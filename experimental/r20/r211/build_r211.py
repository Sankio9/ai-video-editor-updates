"""R2.1.1 Beta incremental 2-file update from exact published R2.1.0.

Only the independent 02 frontend and shared 02/03/04 planner change.
Stable and Premiere JSX executors are not included.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,zipfile

ROOT=pathlib.Path(__file__).resolve().parent
PRIOR_ZIP_SHA="287eabc714e853ec6d6d2d7504abe8225a5c326fc5dea88c973f6c68f7145be2"
FILES={
 "cep/r20_panel.js":ROOT/"candidate/cep/r20_panel.js",
 "tools/r20_graphics_plans.py":ROOT/"candidate/tools/r20_graphics_plans.py",
}
def digest(data):return hashlib.sha256(data).hexdigest()
def build(out,prior):
    prev=pathlib.Path(prior)
    if not prev.is_file() or digest(prev.read_bytes())!=PRIOR_ZIP_SHA:
        raise ValueError("R2.1.0 published archive does not match exact SHA256")
    with zipfile.ZipFile(prev) as z:
        m=json.loads(z.read("manifest.json"))
        if m.get("version")!="2.1.0" or m.get("format")!=1:
            raise ValueError("Not the required v2.1.0 baseline")
        prior_rows={r["path"]:r for r in m["files"]}
        if set(prior_rows)!=set(FILES):raise ValueError("Unexpected baseline allowlist")
        before={}
        for dest in FILES:
            blob=z.read("payload/"+dest)
            if digest(blob)!=prior_rows[dest]["sha256"]:
                raise ValueError("Baseline payload corrupted: "+dest)
            before[dest]=digest(blob)
    files={}
    for dest,source in FILES.items():
        if not source.is_file() or source.is_symlink():raise ValueError("Invalid candidate source")
        data=source.read_bytes()
        if not 1000<len(data)<220000:raise ValueError("Unexpected candidate size")
        if digest(data)==before[dest]:raise ValueError("No change in "+dest)
        files[dest]=data
    panel=files["cep/r20_panel.js"]
    planner=files["tools/r20_graphics_plans.py"]
    for marker in (b"runSubtitlesOneClick",b"Insereaz",b"ENGINE_VERSION_MISMATCH",
                   b"STRIKETHROUGH_NOT_DETECTED",b"planSha",
                   b"R2.1.1-auto-preflight-readable"):
        if marker not in panel:raise ValueError("Missing CEP gate: "+repr(marker))
    for marker in (b"split_subtitles_readable(original,74)",b"strikeAudit",
                   b"R2.1.1-auto-preflight-readable",b"reviewPolicy"):
        if marker not in planner:raise ValueError("Missing planner invariant "+repr(marker))
    if b"r210AnalyzeSubs" in panel or b"r210SubtitlePreview" in panel:
        raise ValueError("Redundant manual buttons still in panel")
    compile(planner,"tools/r20_graphics_plans.py","exec")
    manifest={"format":1,"version":"2.1.1","files":[
        {"path":dest,"sha256":digest(blob),"before_sha256":before[dest]}
        for dest,blob in sorted(files.items())
    ]}
    out=pathlib.Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,ensure_ascii=True,indent=2)+"\n")
        for dest,blob in sorted(files.items()):z.writestr("payload/"+dest,blob)
    with zipfile.ZipFile(out) as z:
        assert set(z.namelist())=={"manifest.json",*(("payload/"+p) for p in files)}
        assert json.loads(z.read("manifest.json"))==manifest
        for r in manifest["files"]:
            assert digest(z.read("payload/"+r["path"]))==r["sha256"]
    return {"version":"2.1.1","requires":"2.1.0","files":len(files),
            "archive_sha256":digest(out.read_bytes()),"bytes":out.stat().st_size}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--prior",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args();print(json.dumps(build(a.output,a.prior),indent=2))
