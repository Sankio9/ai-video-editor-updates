"""Strict incremental R2.3.7 Word-reader hotfix over published R2.3.6.
No Montage 01, captions writer, updater or Stable changes.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_SHA="b6db0f75852fb390851bdf2a40ba6620e5b331ee75ba39033ea5b925412d7537"
TARGETS={"tools/r230_universal.py":"candidate/tools/r230_universal.py",
         "tools/r236_name_guard.py":"candidate/tools/r236_name_guard.py"}
def sha(x):return hashlib.sha256(x).hexdigest()
def build(before,out):
    p=pathlib.Path(before);raw=p.read_bytes()
    if sha(raw)!=BASE_SHA:raise ValueError("R236_BASE_ARCHIVE_SHA_MISMATCH")
    with zipfile.ZipFile(p) as z:
        meta=json.loads(z.read("manifest.json"))
        if meta["format"]!=1 or meta["version"]!="2.3.6":
            raise ValueError("NOT_INSTALLED_BASE_R236")
        old={x["path"]:x for x in meta["files"]}
        changes={}
        for target,source in TARGETS.items():
            if target not in old:raise ValueError("BASE_PATH_NOT_PINNED "+target)
            b=z.read("payload/"+target)
            if sha(b)!=old[target]["sha256"]:raise ValueError("BASE_FILE_INTEGRITY "+target)
            a=(ROOT/source).read_bytes()
            compile(a,target,"exec")
            if sha(a)==sha(b):raise ValueError("FILE_UNCHANGED "+target)
            changes[target]=(b,a)
        panel="cep/r20_panel.js"
        old_panel=z.read("payload/"+panel)
        if sha(old_panel)!=old[panel]["sha256"]:raise ValueError("BASE_PANEL_INTEGRITY")
        # CEP engine/version SHA handshake must remain strict.
        prior_parser_sha=sha(changes["tools/r230_universal.py"][0])
        if old_panel.count(prior_parser_sha.encode())!=1:
            raise ValueError("CEP_EXPECTED_PARSER_SHA_MISSING")
        panel_new=old_panel.replace(prior_parser_sha.encode(),
             sha(changes["tools/r230_universal.py"][1]).encode(),1)
        changes[panel]=(old_panel,panel_new)
        for phrase in (b"ENGINE_VERSION_MISMATCH",b"recoverOrFallback",
                       b"showNameTagReview",b"noContentStatus"):
            if phrase not in panel_new:raise ValueError("APPROVED_GUARD_MISSING")
        if b"expand_mixed_word_paragraphs" not in changes["tools/r230_universal.py"][1]:
            raise ValueError("INLINE_WORD_SPLIT_MISSING")
        if b"NAMETAG_REVIEW_IDENTITY_MISMATCH" not in changes["tools/r236_name_guard.py"][1]:
            raise ValueError("SOURCE_ROLE_GUARD_MISSING")
    entries=[{"path":path,"before_sha256":sha(b),"sha256":sha(a)}
             for path,(b,a) in sorted(changes.items())]
    dest=pathlib.Path(out);dest.parent.mkdir(parents=True,exist_ok=True)
    manifest={"format":1,"version":"2.3.7","files":entries}
    with zipfile.ZipFile(dest,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,indent=2,ensure_ascii=True)+"\n")
        for path,(b,a) in sorted(changes.items()):z.writestr("payload/"+path,a)
    with zipfile.ZipFile(dest) as z:
        for x in entries:
            assert sha(z.read("payload/"+x["path"]))==x["sha256"]
    return {"version":"2.3.7","sha256":sha(dest.read_bytes()),"files":entries}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True);p.add_argument("--out",required=True)
    a=p.parse_args();print(json.dumps(build(a.base,a.out),indent=2))
