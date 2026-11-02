"""AI Video Editor R2.0.5 Beta delta builder (candidate, never Stable).

R2.0.4 -> R2.0.5 ONLY. Two files; no project data and no unsafe overwrite.
The GitHub prerelease workflow must verify exact v2.0.4 asset digest, manifest
and on-disk SHA before allowing this builder to publish anything.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, zipfile

ROOT=pathlib.Path(__file__).resolve().parent
SOURCE={
    "cep/r20_panel.js":ROOT/"candidate/cep/r20_panel.js",
    "tools/r204_carton_layout.py":ROOT/"candidate/tools/r204_carton_layout.py",
}
# Panel is unchanged by v2.0.4; this is its known v2.0.3 SHA-256.
BEFORE_PANEL="6b4c799a3e627fe015698073db8579d0255fed698d09e51492c20f21cb776baf"
# Frozen last-version input from real published v2.0.4.
BEFORE_LAYOUT="caceca0f2d1f99729c7c18ae8b7a9b890281cd2689c9ff56ae7ec1d9c39f4a53"
PREVIOUS_RELEASE_ZIP_SHA="dc5fe714758ec388a18ac317b113452a33a6a65e5ae1101b7cda6c792308be9f"
def sha(b):return hashlib.sha256(b).hexdigest()

def verify_previous(path):
    raw=pathlib.Path(path).read_bytes()
    if sha(raw)!=PREVIOUS_RELEASE_ZIP_SHA:raise ValueError("Wrong v2.0.4 release ZIP")
    with zipfile.ZipFile(path) as z:
        m=json.loads(z.read("manifest.json"))
        if m.get("version")!="2.0.4" or m.get("format")!=1:raise ValueError("Wrong prior version")
        found={x["path"]:x for x in m["files"]}
        if found["tools/r204_carton_layout.py"]["sha256"]!=BEFORE_LAYOUT:
            raise ValueError("R2.0.4 layout base hash mismatch")
        if sha(z.read("payload/tools/r204_carton_layout.py"))!=BEFORE_LAYOUT:
            raise ValueError("R2.0.4 layout payload mismatch")
    return True

def build(output,previous_release):
    verify_previous(previous_release)
    result=[];data={}
    for dest,p in SOURCE.items():
        if not p.is_file() or p.is_symlink():raise ValueError("Missing/unsafe source: "+dest)
        blob=p.read_bytes()
        if not blob or len(blob)>150000:raise ValueError("Unexpected source size")
        data[dest]=blob
        result.append({"path":dest,"sha256":sha(blob),
            "before_sha256":BEFORE_PANEL if dest.startswith("cep/") else BEFORE_LAYOUT})
    ui=data["cep/r20_panel.js"]
    layout=data["tools/r204_carton_layout.py"]
    for needle in (b"function setLegacyVisible(independent)",b"mode.onchange",b"R2.0 Beta"):
        if needle not in ui:raise ValueError("Unexpected UI candidate missing "+repr(needle))
    for needle in (b"concept_before_colon",b"def compact_lines(",b"def build_pages("):
        if needle not in layout:raise ValueError("Unexpected layout candidate missing "+repr(needle))
    if b"REVIEW_MISSING_IDENTITY" in layout:raise ValueError("Unexpected NameTag code in carton helper")
    manifest={"format":1,"version":"2.0.5","files":result}
    output=pathlib.Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,sort_keys=True,indent=2,ensure_ascii=True)+"\n")
        for name,blob in sorted(data.items()):z.writestr("payload/"+name,blob)
    with zipfile.ZipFile(output) as z:
        if set(z.namelist())!={"manifest.json",*(f"payload/{p}" for p in SOURCE)}:
            raise ValueError("Unexpected entry")
        if json.loads(z.read("manifest.json"))!=manifest:raise ValueError("Manifest corruption")
        for x in result:
            if sha(z.read("payload/"+x["path"]))!=x["sha256"]:raise ValueError("Payload mismatch")
    return {"version":"2.0.5","requires":"2.0.4","bytes":output.stat().st_size,
            "sha256":sha(output.read_bytes())}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    p.add_argument("--previous",required=True,help="Verified v2.0.4 release ZIP")
    a=p.parse_args();print(json.dumps(build(a.output,a.previous),indent=2))
