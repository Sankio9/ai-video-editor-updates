"""R2.3.0 Beta release: fallback universal editorial DOCX parser, graphics only.
Do not bypass MOGRT safety; patches existing plan generator, no Premiere handler edits.
"""
import argparse,hashlib,json,pathlib,re,zipfile
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
TARGET="tools/r20_graphics_plans.py"
NEW="tools/r230_universal.py"
BASELINE="2.1.2"

def sha(raw):return hashlib.sha256(raw).hexdigest()
def build(v212,out):
    with zipfile.ZipFile(v212) as z:
        original_manifest=json.loads(z.read("manifest.json"))
        if original_manifest.get("version")!=BASELINE:raise ValueError("PARSER_BASE_VERSION_MISMATCH")
        original=z.read("payload/"+TARGET)
        entries=[row for row in original_manifest["files"] if row["path"]==TARGET]
        if len(entries)!=1 or entries[0]["sha256"]!=sha(original):
            raise ValueError("PARSER_BASE_SHA_MISMATCH")
    source=original.decode("utf8")
    if source.count("def main():")!=1:raise ValueError("PARSER_MAIN_ENTRY_NOT_UNIQUE")
    if "_r230_legacy_build" in source:raise ValueError("PARSER_ALREADY_PATCHED")
    fallback='''
# R2.3.0: preserve approved parser when it understands the DOCX; only
# use universal extraction for different script formats with NO declarations.
# These editorial plans are PREVIEW only. MOGRT executor retains all safety.
_r230_legacy_build=build
def build(docx,module,separator=SEPARATOR,omit_struck=False):
    try:
        return _r230_legacy_build(docx,module,separator,omit_struck)
    except ValueError as problem:
        reason=str(problem)
        if ("Nu am identificat declarații în DOCX" not in reason and
            "Nu există cartoane editoriale în DOCX" not in reason):
            raise
        from r230_universal import build as universal_build
        return universal_build(docx,module,separator,omit_struck)

'''
    patched=source.replace("def main():",fallback+"def main():",1).encode("utf8")
    new=(SOURCE/"candidate/tools/r230_universal.py").read_bytes()
    if sha(new)!="18aa28e9cde7d9ebb3ec349b7a5746844088e8764feda1c8128f7f9938afca4d":
        raise ValueError("UNIVERSAL_SOURCE_SHA_MISMATCH")
    compile(patched,TARGET,"exec");compile(new,NEW,"exec")
    files={TARGET:patched,NEW:new}
    manifest={"format":1,"version":"2.3.0","files":[
        {"path":p,"before_sha256":sha(original) if p==TARGET else None,"sha256":sha(blob)}
        for p,blob in sorted(files.items())
    ]}
    target=Path(out);target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,indent=2,ensure_ascii=True)+"\n")
        for p,blob in sorted(files.items()):z.writestr("payload/"+p,blob)
    with zipfile.ZipFile(target) as z:
        if set(z.namelist())!={"manifest.json",*(("payload/"+p) for p in files)}:
            raise ValueError("ZIP_UNEXPECTED_PATHS")
        for p,blob in files.items():
            if sha(z.read("payload/"+p))!=sha(blob):raise ValueError("ZIP_SHA_MISMATCH")
    return {"version":"2.3.0","files":manifest["files"],"archiveSHA256":sha(target.read_bytes())}
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--v212",required=True);a.add_argument("--out",required=True)
    opts=a.parse_args()
    print(json.dumps(build(opts.v212,opts.out),indent=2))
