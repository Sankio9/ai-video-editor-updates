"""R2.2.7 single-purpose repair: persist R220 readback and recover it safely.

Build on exact PUBLIC v2.2.6 and v2.2.3 assets, not guessed local files.
Patch only CEP 01 report saving, CEP 02 launch, and add read-only recovery JSX.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
RELEASE_226="586119dc870dcb1638ba35055d9b46af8754a1501a64591fa58588520e6d1016"
RELEASE_223="fc82f6777bacf71bd0153c6d1baa281bc1dd5b083a7c433c11c73a6d723c176f"
RELEASE_211="f0a088d7954b09664706e66eb10abb9cf17fa3726eef52fe5639d7ce486b0a12"
def sha(v):return hashlib.sha256(v).hexdigest()
def asset(filename,version,expected):
    raw=pathlib.Path(filename).read_bytes()
    if sha(raw)!=expected:raise ValueError("Wrong published ZIP "+version)
    with zipfile.ZipFile(filename) as z:
        meta=json.loads(z.read("manifest.json"))
        if meta["version"]!=version or meta["format"]!=1:raise ValueError("Wrong manifest "+version)
        files={r["path"]:z.read("payload/"+r["path"]) for r in meta["files"]}
        for r in meta["files"]:
            if sha(files[r["path"]])!=r["sha256"]:raise ValueError("Corrupt published source "+r["path"])
        return files
def unique(text,old,new):
    if text.count(old)!=1:raise ValueError("Expected exactly one source anchor: "+old[:70])
    return text.replace(old,new,1)
def build(v226,v223,v211,out):
    previous=asset(v226,"2.2.6",RELEASE_226)
    old223=asset(v223,"2.2.3",RELEASE_223)
    base211=asset(v211,"2.1.1",RELEASE_211)
    p=previous["cep/r20_panel.js"];base=base211["cep/r20_panel.js"]
    assert p.startswith(base+b"\n"),"2.2.6 panel not derived from pinned 2.1.1"
    oldAddon=p[len(base)+1:]
    assert oldAddon.startswith(b"/* R2.2.6:") and oldAddon.endswith(b"\n")
    assert oldAddon.count(b"last_report.json")==1
    newAddon=(ROOT/"cep/r226_partial_subtitles_panel.js").read_bytes()
    assert b"recoverOrFallback" in newAddon and b"r227_montage_recovery.jsx" in newAddon
    newPanel=base+b"\n"+newAddon+b"\n"
    assert newPanel.count(b"recoverOrFallback")==2
    originalWorkflow=old223["cep/r193_workflow.js"].decode("utf-8")
    source=unique(originalWorkflow,
          "if(actual.join('|')!==expected.join('|')",
          "if(actualC.join('|')!==expected.join('|')")
    source=unique(source,"report.confirmedInsertedCount=actual.length;",
                  "report.confirmedInsertedCount=actualC.length;")
    source=unique(source,"report.phase='POST_READBACK';",
                  "report.phase='POST_READBACK';\n report.readbackKind='LIVE_PREMIERE_CONFIRMED';")
    assert "R220" in source and "saveReport(state,result)" in source
    newJSX=(ROOT/"cep/jsx/r227_montage_recovery.jsx").read_bytes()
    assert b"R227_RECOVERY" in newJSX and b"LIVE_CLIP_READBACK_FAIL" in newJSX
    files={
       "cep/r20_panel.js":newPanel,
       "cep/r193_workflow.js":source.encode("utf8"),
       "cep/jsx/r227_montage_recovery.jsx":newJSX,
    }
    prior={
       "cep/r20_panel.js":sha(p),
       "cep/r193_workflow.js":sha(old223["cep/r193_workflow.js"]),
       "cep/jsx/r227_montage_recovery.jsx":None,
    }
    manifest={"format":1,"version":"2.2.7","files":[
       {"path":n,"before_sha256":prior[n],"sha256":sha(v)}
       for n,v in sorted(files.items())
    ]}
    destination=pathlib.Path(out);destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,ensure_ascii=True,indent=2)+"\n")
        for n,b in sorted(files.items()):z.writestr("payload/"+n,b)
    with zipfile.ZipFile(destination) as z:
        assert set(z.namelist())=={"manifest.json",*(("payload/"+n) for n in files)}
        assert json.loads(z.read("manifest.json"))==manifest
        for r in manifest["files"]:assert sha(z.read("payload/"+r["path"]))==r["sha256"]
    return {"version":"2.2.7","files":manifest["files"],
      "ZIP_SHA256":sha(destination.read_bytes()),"bytes":destination.stat().st_size}
if __name__=="__main__":
    arg=argparse.ArgumentParser()
    for name in ("v226","v223","v211","out"):arg.add_argument("--"+name,required=True)
    a=arg.parse_args()
    print(json.dumps(build(a.v226,a.v223,a.v211,a.out),indent=2))
