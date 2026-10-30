"""R229 package: exact two-file SHA-verified Beta incremental update.

No modifying 01, 03, 04, 05, updater or R1.9.13 Stable.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,zipfile
HERE=pathlib.Path(__file__).resolve().parent
R228_SHA="c5a3e0f237a2a90d9274a8c8bb3405db87714fd6c49458063350d96d128bfcfb"
R211_SHA="f0a088d7954b09664706e66eb10abb9cf17fa3726eef52fe5639d7ce486b0a12"
def sha(x):return hashlib.sha256(x).hexdigest()
def release(path,version,expected):
    raw=pathlib.Path(path).read_bytes()
    assert sha(raw)==expected, "ARCHIVE_SHA_MISMATCH "+version
    with zipfile.ZipFile(path) as z:
        m=json.loads(z.read("manifest.json"))
        assert m.get("version")==version and m.get("format")==1
        out={}
        for entry in m["files"]:
            content=z.read("payload/"+entry["path"])
            assert sha(content)==entry["sha256"], "PAYLOAD_SHA_MISMATCH"
            out[entry["path"]]=content
        return out
def build(v228,v211,out):
    prior=release(v228,"2.2.8",R228_SHA)["cep/r20_panel.js"]
    base=release(v211,"2.1.1",R211_SHA)["cep/r20_panel.js"]
    assert prior.startswith(base+b"\n"),"APPROVED_R211_PANEL_PREFIX_MISSING"
    assert b"R2.2.8 BETA" in prior and b"onClickCapture" in prior
    new=(HERE/"cep/r229_subtitles_panel.js").read_bytes()
    validator=(HERE/"tools/r229_validate_r220.py").read_bytes()
    assert b"R2.2.9 BETA" in new and b"verifyR220Plan" in new
    assert b"reportTemplate" in new and b"PLAN_R220:" in new
    assert b"onClickCapture" in new
    assert b"r20Mode_subs" in new and b"r207OmitStruck" in base
    assert b"r220_montage_plan import" in validator
    assert b"R220_PLAN_SHA_CHANGED" in validator
    compile(validator,"r229_validate_r220.py","exec")
    panel=base+b"\n"+new+b"\n"
    assert panel!=prior and panel.startswith(base+b"\n")
    files={"cep/r20_panel.js":panel,"tools/r229_validate_r220.py":validator}
    meta={"format":1,"version":"2.2.9","files":[
       {"path":p,"before_sha256":sha(prior) if p=="cep/r20_panel.js" else None,
        "sha256":sha(b)}
       for p,b in sorted(files.items())
    ]}
    output=pathlib.Path(out);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(meta,ensure_ascii=True,indent=2)+"\n")
        for p,b in sorted(files.items()):z.writestr("payload/"+p,b)
    with zipfile.ZipFile(output) as z:
        assert set(z.namelist())=={"manifest.json",*(("payload/"+p) for p in files)}
        assert json.loads(z.read("manifest.json"))==meta
        for item in meta["files"]:
            assert sha(z.read("payload/"+item["path"]))==item["sha256"]
    return {"version":"2.2.9","files":meta["files"],
       "zipSHA256":sha(output.read_bytes()),"size":output.stat().st_size}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for n in ("v228","v211","out"):p.add_argument("--"+n,required=True)
    x=p.parse_args()
    print(json.dumps(build(x.v228,x.v211,x.out),indent=2))
