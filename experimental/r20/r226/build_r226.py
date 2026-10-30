"""R2.2.6 Beta: only V3 partial Montage additions, preserving old modes.

Only patch one exact R2.1.1 cep/r20_panel.js and create two new assets.
No script, transcription or media contents in the public GitHub release.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,zipfile

ORIGINAL_RELEASE_SHA="f0a088d7954b09664706e66eb10abb9cf17fa3726eef52fe5639d7ce486b0a12"
PANEL_BEFORE="41f321ca4c57c2dde938948c5dafd4189037c377ff00679a3341f0a19d12f5d0"
PANEL="cep/r20_panel.js"
SRC=pathlib.Path(__file__).resolve().parent
NEW={
 "tools/r226_partial_subtitles.py":SRC/"tools/r226_partial_subtitles.py",
 "cep/jsx/r226_partial_subtitles.jsx":SRC/"cep/jsx/r226_partial_subtitles.jsx",
}
def sha(b):return hashlib.sha256(b).hexdigest()
def build(old_release,out):
    raw=pathlib.Path(old_release).read_bytes()
    if sha(raw)!=ORIGINAL_RELEASE_SHA:raise ValueError("Published v2.1.1 ZIP changed")
    with zipfile.ZipFile(old_release) as z:
        m=json.loads(z.read("manifest.json"))
        if m.get("version")!="2.1.1" or m.get("format")!=1:
            raise ValueError("Unexpected original release")
        entry=[x for x in m["files"] if x.get("path")==PANEL]
        if len(entry)!=1:raise ValueError("Cannot identify panel")
        old=z.read("payload/"+PANEL)
        if sha(old)!=PANEL_BEFORE or sha(old)!=entry[0]["sha256"]:
            raise ValueError("Installed panel baseline differs")
    addon=(SRC/"cep/r226_partial_subtitles_panel.js").read_bytes()
    if b"r20Mode_subs" not in addon or b"last_report.json" not in addon:
        raise ValueError("No scoped R220 bridge")
    if b"r20Mode_subs" not in old or b"r207OmitStruck" not in old:
        raise ValueError("Existing independent/strikethrough flow missing")
    amended=old+b"\n"+addon+b"\n"
    if amended.count(addon)!=1:raise ValueError("Duplicate addon")
    payload={PANEL:amended}
    for name,p in NEW.items():
        if not p.is_file():raise ValueError("New source missing "+name)
        b=p.read_bytes()
        if len(b)<700:raise ValueError("Source truncated "+name)
        if name.endswith(".py"):compile(b,name,"exec")
        payload[name]=b
    rows=[{"path":p,"before_sha256":PANEL_BEFORE if p==PANEL else None,
           "sha256":sha(b)} for p,b in sorted(payload.items())]
    manifest={"format":1,"version":"2.2.6","files":rows}
    target=pathlib.Path(out);target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,indent=2,ensure_ascii=True)+"\n")
        for p,b in sorted(payload.items()):z.writestr("payload/"+p,b)
    with zipfile.ZipFile(target) as z:
        assert set(z.namelist())=={"manifest.json",*(("payload/"+p) for p in payload)}
        assert json.loads(z.read("manifest.json"))==manifest
        for row in rows:
            assert sha(z.read("payload/"+row["path"]))==row["sha256"]
    return {"version":"2.2.6","paths":sorted(payload),"archiveSHA256":sha(target.read_bytes()),
            "bytes":target.stat().st_size,"panelBefore":PANEL_BEFORE,
            "panelAfter":sha(amended)}
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--prior",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args()
    print(json.dumps(build(a.prior,a.out),indent=2))
