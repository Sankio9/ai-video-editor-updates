"""AI Video Editor R2.1.2 BETA: verified one-file caption-balancing delta.

Installed v2.1.1 is mandatory; source and before SHA-256 are verified.
No changes to CEP panel, JSX executor, 01/03/04 or 05 HOLD.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
PRIOR_RELEASE_SHA="f0a088d7954b09664706e66eb10abb9cf17fa3726eef52fe5639d7ce486b0a12"
TARGET="tools/r20_graphics_plans.py"
SOURCE=ROOT/"candidate"/TARGET
def sha(data):return hashlib.sha256(data).hexdigest()

def build(out,previous):
    previous=pathlib.Path(previous)
    if not previous.is_file() or sha(previous.read_bytes())!=PRIOR_RELEASE_SHA:
        raise ValueError("Wrong published R2.1.1 Beta baseline")
    with zipfile.ZipFile(previous) as z:
        meta=json.loads(z.read("manifest.json"))
        if meta.get("format")!=1 or meta.get("version")!="2.1.1":
            raise ValueError("Wrong previous release manifest")
        rows=[x for x in meta["files"] if x.get("path")==TARGET]
        if len(rows)!=1:raise ValueError("Missing previous caption generator")
        before=z.read("payload/"+TARGET)
        if sha(before)!=rows[0]["sha256"]:raise ValueError("Baseline payload SHA mismatch")
        before_hash=sha(before)
    if not SOURCE.is_file() or SOURCE.is_symlink():
        raise ValueError("Missing/unsafe candidate file")
    code=SOURCE.read_bytes()
    if not 2000<len(code)<240000 or sha(code)==before_hash:
        raise ValueError("Unexpected or unchanged caption code")
    for marker in (
        b"split_subtitles_readable(original,74)",
        b"R2.1.1-auto-preflight-readable",
        b"strikeAnalysisReady",
        b"STRIKETHROUGH_NOT_DETECTED",
        b"_SENTENCE_END",
        b"minimum_readable",
    ):
        if marker not in code:raise ValueError("Required guard absent "+repr(marker))
    compile(code,TARGET,"exec")
    manifest={"format":1,"version":"2.1.2","files":[{
        "path":TARGET,"sha256":sha(code),"before_sha256":before_hash
    }]}
    out=pathlib.Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,indent=2,ensure_ascii=True)+"\n")
        z.writestr("payload/"+TARGET,code)
    with zipfile.ZipFile(out) as z:
        if set(z.namelist())!={"manifest.json","payload/"+TARGET}:
            raise ValueError("Extra update files")
        if json.loads(z.read("manifest.json"))!=manifest:
            raise ValueError("Manifest changed in archive")
        if sha(z.read("payload/"+TARGET))!=sha(code):
            raise ValueError("Payload failed readback")
    return {"version":"2.1.2","requires":"2.1.1","fileCount":1,
            "before_sha256":before_hash,"payload_sha256":sha(code),
            "zip_sha256":sha(out.read_bytes()),"bytes":out.stat().st_size}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--prior",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    print(json.dumps(build(a.output,a.prior),indent=2))
