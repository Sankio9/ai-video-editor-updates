"""R2.1.0 BETA ONLY: verified two-stage subtitle preflight delta.

Requires exact R2.0.9 installation; verifies prior r207 (CEP+planner) and
r209 (DOCX detector) release bytes. This ZIP modifies ONLY CEP+planner.
No MOGRT executor/timeline effects; publisher keeps v1.9.13 stable.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile,pathlib

ROOT=pathlib.Path(__file__).resolve().parent
R207_SHA="526cad27b2de0afbe3d27d920604a097e39ce9f2208c9dcf60efd9957535e622"
R209_SHA="2679e98ff441bc993b7e663082f4e912f47ca000f9c994ffc565da5b1e8bb2f2"
FILES={
 "cep/r20_panel.js":ROOT/"candidate/cep/r20_panel.js",
 "tools/r20_graphics_plans.py":ROOT/"candidate/tools/r20_graphics_plans.py",
}
def sha(data):return hashlib.sha256(data).hexdigest()
def check_release(file,version,expected_sha,required):
    zpath=pathlib.Path(file)
    if not zpath.is_file() or sha(zpath.read_bytes())!=expected_sha:
        raise ValueError("Wrong published Beta "+version)
    with zipfile.ZipFile(zpath) as z:
        m=json.loads(z.read("manifest.json"))
        if m.get("format")!=1 or m.get("version")!=version:
            raise ValueError("Wrong manifest "+version)
        rows={r["path"]:r for r in m["files"]}
        if not set(required).issubset(rows):raise ValueError("Missing prior payload")
        out={}
        for dest in required:
            b=z.read("payload/"+dest)
            if sha(b)!=rows[dest]["sha256"]:raise ValueError("Broken prior payload "+dest)
            out[dest]=sha(b)
        return out
def build(output,r207,r209):
    previous=check_release(r207,"2.0.7",R207_SHA,tuple(FILES))
    newer=check_release(r209,"2.0.9",R209_SHA,("tools/r207_docx_strike.py",))
    if len(newer["tools/r207_docx_strike.py"])!=64:
        raise ValueError("Invalid mandatory R2.0.9 helper")
    files={}
    for dest,p in FILES.items():
        if not p.is_file() or p.is_symlink():raise ValueError("Missing candidate "+dest)
        data=p.read_bytes()
        if not 1000<len(data)<200000:raise ValueError("Unexpected candidate size")
        files[dest]=data
    panel=files["cep/r20_panel.js"]
    python=files["tools/r20_graphics_plans.py"]
    for marker in (b"r210AnalyzeSubs",b"r210SubtitlePreview",b"ENGINE_VERSION_MISMATCH",
                   b"STRIKETHROUGH_NOT_DETECTED",b"planSha",b"function run(key,verified)"):
        if marker not in panel:raise ValueError("Missing CEP safety invariant "+repr(marker))
    for marker in (b"R2.1.0-two-phase-preflight",b"strikeAudit",
                   b"STRIKETHROUGH_NOT_DETECTED",b"from r207_docx_strike import extract_strike_policy"):
        if marker not in python:raise ValueError("Missing Python preflight "+repr(marker))
    compile(python,"tools/r20_graphics_plans.py","exec")
    manifest={"format":1,"version":"2.1.0","files":[
        {"path":dest,"sha256":sha(data),"before_sha256":previous[dest]}
        for dest,data in sorted(files.items())
    ]}
    output=pathlib.Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,ensure_ascii=True,indent=2)+"\n")
        for dest,data in sorted(files.items()):z.writestr("payload/"+dest,data)
    with zipfile.ZipFile(output) as z:
        if set(z.namelist())!={"manifest.json",*(("payload/"+p) for p in files)}:raise ValueError("Unlisted files")
        if json.loads(z.read("manifest.json"))!=manifest:raise ValueError("Manifest mismatch")
        for row in manifest["files"]:
            if sha(z.read("payload/"+row["path"]))!=row["sha256"]:raise ValueError("Corrupt payload")
    return {"version":"2.1.0","requires":"2.0.9","files":len(files),
            "archiveSHA256":sha(output.read_bytes()),"bytes":output.stat().st_size,
            "requiredPriorDetectorSHA256":newer["tools/r207_docx_strike.py"]}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--r207",required=True)
    p.add_argument("--r209",required=True)
    p.add_argument("--output",required=True)
    x=p.parse_args()
    print(json.dumps(build(x.output,x.r207,x.r209),indent=2))
