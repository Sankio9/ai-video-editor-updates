"""R2.0.4 Beta incremental ZIP for verified v2.0.3, NEVER stable.
Only R2.0.3 planner + one additive local deterministic layout helper.
No media, DOCX, transcripts, full legacy application or MOGRT template published.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BEFORE="60b60012536cef103094ed33d2f31c05a9aec10a6bcbeb2149bca0c7c89a6698"
SOURCES={
 "tools/r20_graphics_plans.py": ROOT/"candidate/tools/r20_graphics_plans.py",
 "tools/r204_carton_layout.py": ROOT/"candidate/tools/r204_carton_layout.py",
}

def digest(b):return hashlib.sha256(b).hexdigest()

def build(out):
    rows=[];contents={}
    for rel,source in SOURCES.items():
        if not source.is_file() or source.is_symlink():raise ValueError("Source missing or symlink: "+rel)
        raw=source.read_bytes()
        if not raw or len(raw)>100000:raise ValueError("Unexpected source size: "+rel)
        contents[rel]=raw
        rows.append({"path":rel,"sha256":digest(raw),
                     "before_sha256":BEFORE if rel=="tools/r20_graphics_plans.py" else None})
    assert len(rows)==2
    source=contents["tools/r20_graphics_plans.py"]
    assert b"R2.0.4-captions-layout" in source
    assert b"R2.0.3" not in source[source.find(b"generatorVersion"):], "Unexpected suffix"
    assert b"REVIEW_MISSING_IDENTITY" in source and b"EXPLICIT_SKIP_APPROVAL" in source
    assert b"from r204_carton_layout import build_pages" in source
    assert b"r204_carton_layout" in source
    assert b"importMGT" not in source, "No Adobe executor changes permitted"
    assert b"def semantic_emphasis" in contents["tools/r204_carton_layout.py"]
    manifest={"format":1,"version":"2.0.4","files":rows}
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,ensure_ascii=True,indent=2)+"\n")
        for rel,b in contents.items():z.writestr("payload/"+rel,b)
    with zipfile.ZipFile(out) as z:
        assert set(z.namelist())=={"manifest.json",*["payload/"+p for p in SOURCES]}
        assert json.loads(z.read("manifest.json"))==manifest
        for row in rows:assert digest(z.read("payload/"+row["path"]))==row["sha256"]
    if out.stat().st_size>=45*1024*1024:raise ValueError("Oversized")
    return {"version":"2.0.4","requires":"2.0.3","files":len(rows),"archive_sha256":digest(out.read_bytes())}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",default="dist/AIVE_UPDATE.zip")
    a=p.parse_args();print(json.dumps(build(a.output),indent=2))
