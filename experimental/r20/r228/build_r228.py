"""R2.2.8 Beta: asynchronous CEP hook hotfix, SHA-pinned one-file update.

Only cep/r20_panel.js. No changes to Montage writer, graphics executors,
modules 03/04/05, Stable, updater code or user files.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_227_SHA="3f04f91e630cba694b1214c758f17cb4203da066ef681c76f3d1a73b8e014519"
BASE_211_SHA="f0a088d7954b09664706e66eb10abb9cf17fa3726eef52fe5639d7ce486b0a12"
TARGET="cep/r20_panel.js"
def sha(x):return hashlib.sha256(x).hexdigest()
def read_release(p,version,expected):
    b=pathlib.Path(p).read_bytes()
    if sha(b)!=expected:raise ValueError("RELEASE_ARCHIVE_SHA_CHANGED_"+version)
    with zipfile.ZipFile(p) as z:
        meta=json.loads(z.read("manifest.json"))
        if meta.get("version")!=version or meta.get("format")!=1:raise ValueError("RELEASE_MANIFEST_INVALID")
        files={}
        for r in meta["files"]:
            raw=z.read("payload/"+r["path"])
            if sha(raw)!=r["sha256"]:raise ValueError("RELEASE_FILE_SHA_CHANGED")
            files[r["path"]]=raw
        return files
def build(b227,b211,out):
    prior=read_release(b227,"2.2.7",BASE_227_SHA)
    before=prior[TARGET]
    ref=read_release(b211,"2.1.1",BASE_211_SHA)
    original=ref[TARGET]
    if not before.startswith(original+b"\n"):
        raise ValueError("R227_PANEL_BASE_CHANGED")
    old=before[len(original)+1:]
    for invariant in (b"recoverOrFallback",b"r207OmitStruck",b"last_report.json",b"R2.2.6"):
        if invariant not in before:raise ValueError("EARLIER_FEATURE_MISSING")
    if b"onClickCapture" in old:raise ValueError("ALREADY_CAPTURE_PATCHED")
    addon=(ROOT/"cep/r228_subtitles_panel.js").read_bytes()
    for invariant in (b"onClickCapture",b"document.addEventListener('click',onClickCapture,true)",
      b"MutationObserver",b"R2.2.8 BETA",b"recoverOrFallback",b"r226_partial_subtitles.py",
      b"r227_montage_recovery.jsx",b"oldClick"):
        if invariant==b"oldClick":
            if invariant in addon:raise ValueError("STALE_BOUND_ONCLICK_HANDLER")
        elif invariant not in addon:raise ValueError("MISSING_R228_INVARIANT "+str(invariant))
    # Preserve byte-for-byte all previously approved 02 independent/03/04 code.
    after=original+b"\n"+addon+b"\n"
    if after==before or not after.startswith(original):raise ValueError("NO_EFFECTIVE_PATCH")
    meta={"format":1,"version":"2.2.8","files":[
      {"path":TARGET,"before_sha256":sha(before),"sha256":sha(after)}
    ]}
    target=pathlib.Path(out);target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(meta,ensure_ascii=True,indent=2)+"\n")
        z.writestr("payload/"+TARGET,after)
    with zipfile.ZipFile(target) as z:
        assert set(z.namelist())=={"manifest.json","payload/"+TARGET}
        assert json.loads(z.read("manifest.json"))==meta
        assert sha(z.read("payload/"+TARGET))==meta["files"][0]["sha256"]
    return {"version":"2.2.8","files":meta["files"],"bytes":target.stat().st_size,
      "archive_sha256":sha(target.read_bytes())}
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--v227",required=True);ap.add_argument("--v211",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args()
    print(json.dumps(build(a.v227,a.v211,a.out),indent=2))
