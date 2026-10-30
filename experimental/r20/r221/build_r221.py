"""R2.2.1 BETA: permanent UTF-8/cp1252-safe Beta updater.
Only 2 exact existing files, original installed v2.0.2 bytes pinned.
Previous montage v2.2.0 and Stable v1.9.13 unchanged.
"""
import argparse,hashlib,json,zipfile,pathlib

ROOT=pathlib.Path(__file__).resolve().parent
BEFORE={
 "updater/beta.py":"1724ebad22568dd0ad018a3a226ea4360ac2e403ef6c6352169c84bac84a5a8d",
 "cep/aive_updater_beta.js":"dc2ec23af66dd3195755a70f0c9b14a54dbf14b1b881848c2526a4dcbbb33eb1",
}
def digest(blob):return hashlib.sha256(blob).hexdigest()
def contents(filename,version):
    with zipfile.ZipFile(filename) as z:
        m=json.loads(z.read("manifest.json"))
        if m.get("format")!=1 or m.get("version")!=version:
            raise ValueError("Unexpected prior release version")
        out={}
        for row in m["files"]:
            b=z.read("payload/"+row["path"])
            if digest(b)!=row["sha256"]:raise ValueError("Corrupt original patch")
            out[row["path"]]=b
        return out

def replace_once(s,old,new):
    if s.count(old)!=1:
        raise ValueError("Required exact original updater anchor missing: "+old[:75])
    return s.replace(old,new,1)
def build(previous,baseline,output):
    prior=contents(previous,"2.2.0")
    if len(prior)!=7 or "tools/r193_pipeline.py" not in prior:
        raise ValueError("Unexpected R2.2.0 montage baseline")
    original=contents(baseline,"2.0.2")
    assert set(BEFORE).issubset(original)
    for name,sha in BEFORE.items():
        if digest(original[name])!=sha:raise ValueError("Unexpected installed updater baseline "+name)
    py=original["updater/beta.py"].decode("utf8")
    py=replace_once(py,"print(json.dumps(result,ensure_ascii=False))",
                    "print(json.dumps(result,ensure_ascii=True))")
    py=replace_once(py,"print(json.dumps({'ok':False,'message':str(exc)},ensure_ascii=False))",
                    "print(json.dumps({'ok':False,'message':str(exc)},ensure_ascii=True))")
    js=original["cep/aive_updater_beta.js"].decode("utf8")
    js=replace_once(js,
      "var ps=cp.spawn(python,args,{cwd:root,windowsHide:true}),stdout='',stderr='',done=false;",
      "var betaEnv=Object.assign({},process.env,{PYTHONIOENCODING:'utf-8',PYTHONUTF8:'1'});\n"+
      "   var ps=cp.spawn(python,args,{cwd:root,windowsHide:true,env:betaEnv}),stdout='',stderr='',done=false;")
    # Validity: after a forced cp1252 error the CLI must always emit
    # ASCII-escaped JSON that can be parsed by CEP, NEVER a traceback.
    assert "ensure_ascii=False" not in py
    assert py.count("ensure_ascii=True")==2
    assert "PYTHONIOENCODING:'utf-8'" in js
    compile(py,"updater/beta.py","exec")
    payload={"updater/beta.py":py.encode("utf8"),
             "cep/aive_updater_beta.js":js.encode("utf8")}
    manifest={"format":1,"version":"2.2.1","files":[
        {"path":name,"sha256":digest(payload[name]),"before_sha256":BEFORE[name]}
        for name in sorted(BEFORE)
    ]}
    output=pathlib.Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,indent=2)+"\n")
        for name in sorted(payload):z.writestr("payload/"+name,payload[name])
    with zipfile.ZipFile(output) as z:
        assert set(z.namelist())=={"manifest.json",*(("payload/"+x) for x in BEFORE)}
        assert json.loads(z.read("manifest.json"))==manifest
        assert all(digest(z.read("payload/"+x))==digest(y) for x,y in payload.items())
    return {"version":"2.2.1","requires":"2.2.0","files":len(payload),
            "sha256":digest(output.read_bytes()),"size":output.stat().st_size}
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--previous",required=True)
    a.add_argument("--baseline",required=True)
    a.add_argument("--output",required=True)
    p=a.parse_args()
    print(json.dumps(build(p.previous,p.baseline,p.output),indent=2))
