"""Reproducible, inert R2.0 GitHub candidate build. Does NOT publish a release.

Never run as stable updater. Only four pre-approved, hash-pinned files are eligible.
"""
from __future__ import annotations
import argparse, hashlib, io, json, pathlib, zipfile

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT.parents[2]/"dist"/"R20_CANDIDATE_UPDATE.zip"
VERSION="2.0.0"
FILES={
    "cep/index.html":("af6e84fcf6ce746ac34d02174a398481f618efc851c087061dfb1a2bcbc92023",
                      "6530eb2cf1fab4167e8263a661515bf5ddd68a0b8d0a4b9ec1ae328afb37a797"),
    "cep/r20_panel.js":("1fd3e2e5254bc77442ff0b54d824ee72b28cbeb87b993282f1e79f7c5250454c",None),
    "cep/jsx/r20_graphics.jsx":("d9a704f50a9f221fb93f15884c3cda20e328d3aa0ffbd7a6cced202ebe6a52a2",None),
    "tools/r20_graphics_plans.py":("37ec5e19ae2223d079263cbac9763fe2cb915593f9d4e37151cff7d522fa562f",None),
}
def sha(data): return hashlib.sha256(data).hexdigest()
def build(out=OUT):
    payload=[]
    manifest={"format":1,"version":VERSION,"files":[]}
    for name,(expected,before) in FILES.items():
        path=ROOT.joinpath(*name.split("/"))
        if not path.is_file() or path.is_symlink():
            raise ValueError("Unexpected file: "+name)
        blob=path.read_bytes()
        if sha(blob)!=expected: raise ValueError("Candidate source checksum mismatch: "+name)
        manifest["files"].append({"path":name,"sha256":expected,"before_sha256":before})
        payload.append((name,blob))
    out=pathlib.Path(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,indent=2,ensure_ascii=True)+"\n")
        for name,blob in payload: z.writestr("payload/"+name,blob)
    with zipfile.ZipFile(out) as z:
        assert set(z.namelist())=={"manifest.json",*["payload/"+p for p in FILES]}
        checked=json.loads(z.read("manifest.json"))
        assert checked==manifest
        for name,(expected,_) in FILES.items():
            assert sha(z.read("payload/"+name))==expected
    return {"status":"CANDIDATE_ONLY_NOT_RELEASED","version":VERSION,"sha256":sha(out.read_bytes()),
            "files":len(FILES),"bytes":out.stat().st_size,"output":str(out)}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",default=str(OUT))
    print(json.dumps(build(p.parse_args().output),indent=2))
