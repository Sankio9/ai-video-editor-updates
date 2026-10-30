"""R2.3.4: exact SHA-guarded update for merged six-column newsroom DOCX.
Only cep/r20_panel.js (version/engine SHA) and tools/r230_universal.py.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,re,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
OLD_ZIP_SHA="49f7b50a6ec145e681d0ded7a5aa5d3f9133e827a93db78cec0a2447ae2ddcd3"
FILES={"cep/r20_panel.js","tools/r230_universal.py"}
def sha(x):return hashlib.sha256(x).hexdigest()
def build(previous,output):
    prior=pathlib.Path(previous).read_bytes()
    if sha(prior)!=OLD_ZIP_SHA:raise ValueError("RELEASE_R233_ZIP_SHA_MISMATCH")
    with zipfile.ZipFile(previous) as z:
        m=json.loads(z.read("manifest.json"))
        if m.get("version")!="2.3.3" or m.get("format")!=1:raise ValueError("R233_MANIFEST_INVALID")
        files={}
        for entry in m["files"]:
            name=entry["path"]
            data=z.read("payload/"+name)
            if sha(data)!=entry["sha256"]:raise ValueError("R233_PAYLOAD_SHA_MISMATCH")
            files[name]=data
    if set(files)!=FILES:raise ValueError("R233_SCOPE_UNEXPECTED")
    parser=(ROOT/"candidate/tools/r230_universal.py").read_bytes()
    compile(parser,"r230_universal.py","exec")
    if not all(x in parser for x in (b"def unique_cells(row):",b"inside_pkg",b"boundary = max(1, len(row.cells) // 3)",
                                    b"contentSummary",b"SKIP_NARRATION")):
        raise ValueError("R234_TABLE_PARSER_FEATURE_MISSING")
    panel=files["cep/r20_panel.js"].decode("utf-8")
    marker=r"(sha\(universalFile\)==='([a-f0-9]{64})')"
    matches=list(re.finditer(marker,panel))
    if len(matches)!=1 or matches[0].group(2)!=sha(files["tools/r230_universal.py"]):
        raise ValueError("R233_PANEL_HANDSHAKE_SHA_MISMATCH")
    panel=panel[:matches[0].start(2)]+sha(parser)+panel[matches[0].end(2):]
    if panel.count("R2.3.3 BETA")!=1:raise ValueError("R233_VERSION_MARKER_CHANGED")
    panel=panel.replace("R2.3.3 BETA","R2.3.4 BETA")
    for invariant in (b"ENGINE_VERSION_MISMATCH",b"onClickCapture",b"recoverOrFallback",
                      b"showNameTagReview",b"NIMIC DE INSERAT",b"rollback"):
        if invariant not in panel.encode("utf8"):raise ValueError("APPROVED_PANEL_INVARIANT_MISSING")
    files_new={"cep/r20_panel.js":panel.encode("utf8"),"tools/r230_universal.py":parser}
    manifest={"format":1,"version":"2.3.4","files":[
        {"path":name,"before_sha256":sha(files[name]),"sha256":sha(files_new[name])}
        for name in sorted(FILES)]}
    dest=pathlib.Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(dest,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,indent=2,ensure_ascii=True)+"\n")
        for name in sorted(FILES):z.writestr("payload/"+name,files_new[name])
    with zipfile.ZipFile(dest) as z:
        if set(z.namelist())!={"manifest.json",*(("payload/"+p) for p in FILES)}:
            raise ValueError("PACKAGING_SCOPE_INVALID")
        for item in manifest["files"]:
            if sha(z.read("payload/"+item["path"]))!=item["sha256"]:
                raise ValueError("PACKAGING_SHA_INVALID")
    return {"version":"2.3.4","files":manifest["files"],"zipSha256":sha(dest.read_bytes())}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--previous",required=True);p.add_argument("--out",required=True)
    a=p.parse_args();print(json.dumps(build(a.previous,a.out),indent=2))
