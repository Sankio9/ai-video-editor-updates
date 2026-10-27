"""Pinned R2.0.3 NameTag review hotfix. Upgrade from verified R2.0.2 only.

Only two explicitly reviewed file paths. No ZIP installed by hand.
The user's in-app Beta updater verifies SHA-256, backs up and rolls back.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
FILES={
  "cep/r20_panel.js":(
    HERE/"candidate"/"cep"/"r20_panel.js",
    "506dc87dc2b982fadb1cb3b7f33e25103b8529df613ece9f11de73d634934614",
    "440b84a2f01684f74884989de39100f03698d4c7c77ac2b63ddd19482de594b1"
  ),
  "tools/r20_graphics_plans.py":(
    HERE/"candidate"/"tools"/"r20_graphics_plans.py",
    "bf8f4dfcf0a1fbee2b9d770276c18b4d010d736b032be8840efb0188ae8b0356",
    "df0b5f4ab1aa87274305222e51ea02b5adc44b26b72d72155ce38e4a2d52c9af"
  )
}
def digest(raw):return hashlib.sha256(raw).hexdigest()
def build(output):
    manifest={"format":1,"version":"2.0.3","files":[]}
    payload={}
    for relative,(source,expected,before) in FILES.items():
        if not source.is_file() or source.is_symlink():raise ValueError("Missing source: "+relative)
        raw=source.read_bytes()
        if digest(raw)!=expected:raise ValueError("Unexpected source SHA-256: "+relative)
        manifest["files"].append({"path":relative,"sha256":expected,"before_sha256":before})
        payload[relative]=raw
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,ensure_ascii=True,indent=2)+"\n")
        for relative,raw in payload.items():z.writestr("payload/"+relative,raw)
    with zipfile.ZipFile(output) as z:
        if set(z.namelist())!={"manifest.json",*("payload/"+p for p in FILES)}:
            raise ValueError("Unannounced ZIP entry")
        if json.loads(z.read("manifest.json"))!=manifest:raise ValueError("Manifest mismatch")
        for relative in FILES:
            if digest(z.read("payload/"+relative))!=FILES[relative][1]:
                raise ValueError("Invalid update payload: "+relative)
    return {"version":"2.0.3","files":len(payload),"sha256":digest(output.read_bytes()),
            "size":output.stat().st_size}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="dist/AIVE_UPDATE.zip")
    args=p.parse_args()
    print(json.dumps(build(args.output),indent=2))
