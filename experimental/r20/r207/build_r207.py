"""R2.0.7 Beta SHA-pinned 3-file delta from previously installed v2.0.5.

R2.0.5 changed the CEP UI, R2.0.4 changed the plan generator; both archives
must be verified. This is a Beta-only candidate, never a Stable release.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
PREV_R205="0c2af0a11dea5a2234e840551059d8712da1c4dec1290a22963ca63442561469"
PREV_R204="dc5fe714758ec388a18ac317b113452a33a6a65e5ae1101b7cda6c792308be9f"
SOURCE={
    "cep/r20_panel.js":ROOT/"candidate/cep/r20_panel.js",
    "tools/r20_graphics_plans.py":ROOT/"candidate/tools/r20_graphics_plans.py",
    "tools/r207_docx_strike.py":ROOT/"tools/r207_docx_strike.py"
}
def sha(b):return hashlib.sha256(b).hexdigest()
def previous_archive(path,expected,version,required):
    data=pathlib.Path(path).read_bytes()
    if sha(data)!=expected:raise ValueError("Previous GitHub archive hash changed: "+version)
    with zipfile.ZipFile(path) as z:
        m=json.loads(z.read("manifest.json"))
        if m.get("version")!=version or m.get("format")!=1:raise ValueError("Wrong archive "+version)
        rows={x["path"]:x for x in m["files"]}
        if required not in rows:raise ValueError("Required prior file not present "+required)
        blob=z.read("payload/"+required)
        if sha(blob)!=rows[required]["sha256"]:raise ValueError("Corrupt prior payload "+required)
        return sha(blob)

def build(output,prior_r204,prior_r205):
    before={
      "cep/r20_panel.js":previous_archive(prior_r205,PREV_R205,"2.0.5","cep/r20_panel.js"),
      "tools/r20_graphics_plans.py":previous_archive(prior_r204,PREV_R204,"2.0.4","tools/r20_graphics_plans.py"),
      "tools/r207_docx_strike.py":None
    }
    files={}
    for rel,p in SOURCE.items():
        if not p.is_file() or p.is_symlink():raise ValueError("Missing candidate "+rel)
        b=p.read_bytes()
        if not b or len(b)>200000:raise ValueError("Unexpected candidate size "+rel)
        files[rel]=b
    assert b"function setLegacyVisible(independent)" in files["cep/r20_panel.js"]
    assert b"r207OmitStruck" in files["cep/r20_panel.js"]
    assert b"OMIT_STRUCK" in files["cep/r20_panel.js"]
    assert b"from r207_docx_strike import extract_strike_policy" in files["tools/r20_graphics_plans.py"]
    assert b"REVIEW_MISSING_IDENTITY" in files["tools/r20_graphics_plans.py"]
    assert b"from r204_carton_layout import build_pages" in files["tools/r20_graphics_plans.py"]
    assert b"def extract_strike_policy(" in files["tools/r207_docx_strike.py"]
    manifest={"format":1,"version":"2.0.7",
              "files":[{"path":k,"sha256":sha(v),"before_sha256":before[k]}
                       for k,v in sorted(files.items())]}
    output=pathlib.Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,indent=2,ensure_ascii=True)+"\n")
        for k,v in sorted(files.items()):z.writestr("payload/"+k,v)
    with zipfile.ZipFile(output) as z:
        assert set(z.namelist())=={"manifest.json",*(("payload/"+p) for p in files)}
        assert json.loads(z.read("manifest.json"))==manifest
        for row in manifest["files"]:
            assert sha(z.read("payload/"+row["path"]))==row["sha256"]
    if output.stat().st_size>=45*1024*1024:raise ValueError("Unexpected ZIP size")
    return {"requires":"2.0.5","version":"2.0.7","files":len(files),
            "archiveSHA256":sha(output.read_bytes()),"bytes":output.stat().st_size}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    p.add_argument("--r204",required=True)
    p.add_argument("--r205",required=True)
    v=p.parse_args()
    print(json.dumps(build(v.output,v.r204,v.r205),indent=2))
