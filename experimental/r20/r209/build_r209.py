"""R2.0.9: one-file Beta hotfix over installed R2.0.7, never Stable.

Strict prior published archive SHA256 + base file SHA256 required.
Only replaces tools/r207_docx_strike.py. No MOGRT, Montage 01,
NameTag, cartons, VO, or CEP UI modifications.
"""
from __future__ import annotations

import argparse, hashlib, json, pathlib, zipfile

ROOT=pathlib.Path(__file__).resolve().parent
OLD_RELEASE_ZIP_SHA="526cad27b2de0afbe3d27d920604a097e39ce9f2208c9dcf60efd9957535e622"
TARGET="tools/r207_docx_strike.py"
SOURCE=ROOT/"candidate"/TARGET
def sha(data):return hashlib.sha256(data).hexdigest()

def make(out, prior):
    prior=pathlib.Path(prior)
    if not prior.is_file() or sha(prior.read_bytes())!=OLD_RELEASE_ZIP_SHA:
        raise ValueError("R2.0.7 Beta archive changed or missing")
    with zipfile.ZipFile(prior) as z:
        m=json.loads(z.read("manifest.json"))
        if m.get("format")!=1 or m.get("version")!="2.0.7":
            raise ValueError("Unexpected previous version")
        rows=[r for r in m.get("files",[]) if r.get("path")==TARGET]
        if len(rows)!=1:raise ValueError("Missing previous strike detector")
        previous=z.read("payload/"+TARGET)
        if sha(previous)!=rows[0].get("sha256"):
            raise ValueError("R2.0.7 detector payload mismatched manifest")
        before=sha(previous)
    if not SOURCE.is_file() or SOURCE.is_symlink():
        raise ValueError("Missing safe R2.0.9 source")
    code=SOURCE.read_bytes()
    if len(code)<500 or len(code)>250000:raise ValueError("Unexpected size")
    for marker in (b"STRIKETHROUGH_NOT_DETECTED",b"w:delText",
                   b"def _formatting_strike",b"def extract_strike_policy"):
        if marker not in code:raise ValueError("Missing crucial regression guard")
    compile(code,TARGET,"exec")
    if code==previous:raise ValueError("No change relative to v2.0.7")
    manifest={"format":1,"version":"2.0.9","files":[{
        "path":TARGET,"sha256":sha(code),"before_sha256":before}]}
    out=pathlib.Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,ensure_ascii=True,indent=2)+"\n")
        z.writestr("payload/"+TARGET,code)
    with zipfile.ZipFile(out) as z:
        if set(z.namelist())!={"manifest.json","payload/"+TARGET}:
            raise ValueError("Unexpected files")
        if json.loads(z.read("manifest.json"))!=manifest:raise ValueError("Manifest mismatch")
        if sha(z.read("payload/"+TARGET))!=sha(code):raise ValueError("Payload mismatch")
    return {"version":"2.0.9","requires":"2.0.7","files":1,
            "before_sha256":before,"payload_sha256":sha(code),
            "archive_sha256":sha(out.read_bytes()),"bytes":out.stat().st_size}

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--prior",required=True)
    cli.add_argument("--output",required=True)
    a=cli.parse_args()
    print(json.dumps(make(a.output,a.prior),indent=2))
