"""R2.1.4 bootstrap: fix Beta discovery choosing MIN instead of MAX.

The current Windows updater checks PREVIOUS release v2.0.2 bytes. Publishing
another later v2.2.x cannot help it: it always picks the smallest newer tag.
Build a bridge release v2.1.4, immediately after installed v2.1.3, containing
only verified Beta updater fixes. All original SHA guards stay enabled.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile,pathlib

ORIGINAL={
 "updater/beta.py":"1724ebad22568dd0ad018a3a226ea4360ac2e403ef6c6352169c84bac84a5a8d",
 "cep/aive_updater_beta.js":"dc2ec23af66dd3195755a70f0c9b14a54dbf14b1b881848c2526a4dcbbb33eb1",
}
ZIP_221="16fac7181a9bb04bebec4e5e25b970c3e262eb19733728a1b80cb2517f9c009f"

def sha(blob):return hashlib.sha256(blob).hexdigest()
def read_zip(path,version,digest):
    raw=pathlib.Path(path).read_bytes()
    if sha(raw)!=digest:raise ValueError("Wrong original release ZIP hash "+version)
    with zipfile.ZipFile(path) as z:
        meta=json.loads(z.read("manifest.json"))
        if meta.get("format")!=1 or meta.get("version")!=version:
            raise ValueError("Unexpected release format")
        rows={}
        for item in meta["files"]:
            p=item["path"];data=z.read("payload/"+p)
            if sha(data)!=item["sha256"]:raise ValueError("Corrupt upstream SHA "+p)
            rows[p]=(item,data)
        return rows

def build(r221,out):
    patches=read_zip(r221,"2.2.1",ZIP_221)
    if set(patches)!=set(ORIGINAL):raise ValueError("Unexpected 2.2.1 files")
    for name,expected in ORIGINAL.items():
        if patches[name][0]["before_sha256"]!=expected:
            raise ValueError("Installed user baseline not verified: "+name)
    beta=patches["updater/beta.py"][1].decode("utf8")
    old="_,tag,asset=min(choices,key=lambda x:x[0])"
    new="_,tag,asset=max(choices,key=lambda x:x[0])"
    if beta.count(old)!=1:raise ValueError("Old bad beta-selection code not found exactly once")
    beta=beta.replace(old,new)
    if "ensure_ascii=False" in beta or beta.count("ensure_ascii=True")!=2:
        raise ValueError("Windows console fix lost")
    if "min(choices" in beta:raise ValueError("Beta still picks oldest release")
    compile(beta,"updater/beta.py","exec")
    files={"updater/beta.py":beta.encode("utf8"),
           "cep/aive_updater_beta.js":patches["cep/aive_updater_beta.js"][1]}
    if b"PYTHONIOENCODING:'utf-8'" not in files["cep/aive_updater_beta.js"]:
        raise ValueError("Child process must use UTF8 explicitly")
    rows=[{"path":p,"before_sha256":ORIGINAL[p],"sha256":sha(payload)}
          for p,payload in sorted(files.items())]
    meta={"format":1,"version":"2.1.4","files":rows}
    out=pathlib.Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(meta,indent=2)+"\n")
        for name,payload in sorted(files.items()):
            z.writestr("payload/"+name,payload)
    with zipfile.ZipFile(out) as z:
        assert set(z.namelist())=={"manifest.json",*(("payload/"+n) for n in files)}
        assert json.loads(z.read("manifest.json"))==meta
    return {"version":"2.1.4","requires":"2.1.3","paths":sorted(files),
      "zip_sha256":sha(out.read_bytes()),"bytes":out.stat().st_size,
      "new_updater_beta_py_SHA256":sha(files["updater/beta.py"])}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--r221",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    print(json.dumps(build(a.r221,a.out),indent=2))
