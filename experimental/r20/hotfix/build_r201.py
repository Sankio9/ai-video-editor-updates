"""Hash-pinned R2.0.1 NameTag-only hotfix for installed prerelease R2.0.0.

The official updater enforces before_sha256 on the only modified file.
Do NOT update modules 01,02,04,05, CEP or legacy NameTag.
"""
from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'candidate'/'tools'/'r20_graphics_plans.py'
BEFORE='37ec5e19ae2223d079263cbac9763fe2cb915593f9d4e37151cff7d522fa562f'
AFTER='df0b5f4ab1aa87274305222e51ea02b5adc44b26b72d72155ce38e4a2d52c9af'
REL='tools/r20_graphics_plans.py'
VERSION='2.0.1'
def sha(data):return hashlib.sha256(data).hexdigest()
def build(out):
    raw=SOURCE.read_bytes()
    if sha(raw)!=AFTER:raise ValueError('Hotfix source SHA mismatch: '+sha(raw))
    manifest={'format':1,'version':VERSION,'files':[
        {'path':REL,'sha256':AFTER,'before_sha256':BEFORE}]}
    out=Path(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=True,indent=2)+'\n')
        z.writestr('payload/'+REL,raw)
    with zipfile.ZipFile(out) as z:
        assert set(z.namelist())=={'manifest.json','payload/'+REL}
        assert sha(z.read('payload/'+REL))==AFTER
        assert json.loads(z.read('manifest.json'))==manifest
    return {'version':VERSION,'sha256':sha(out.read_bytes()),'bytes':out.stat().st_size,'files':1}
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='dist/AIVE_UPDATE.zip')
    print(json.dumps(build(parser.parse_args().output),indent=2))
