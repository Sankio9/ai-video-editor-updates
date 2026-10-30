"""R2.0.2 beta updater bootstrap + R2.0.1 NameTag fix.
Four file exact-SHA delta from installed R2.0.0. Experimental pre-release only.
No stable module executors modified. Verification via runner.preflight in Windows.
"""
from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json,zipfile

HERE=Path(__file__).resolve().parent
EXPERIMENTAL=HERE.parents[0]
FILES={
  'cep/index.html':(
    HERE/'cep'/'index.html',
    '81a976fd8393294dd7f2d57ab69ea04ab2d675a936ddfefa6c50fafd3ec05f82',
    'af6e84fcf6ce746ac34d02174a398481f618efc851c087061dfb1a2bcbc92023'),
  'cep/aive_updater_beta.js':(
    HERE/'cep'/'aive_updater_beta.js',
    'dc2ec23af66dd3195755a70f0c9b14a54dbf14b1b881848c2526a4dcbbb33eb1',None),
  'updater/beta.py':(
    HERE/'updater'/'beta.py',
    '1724ebad22568dd0ad018a3a226ea4360ac2e403ef6c6352169c84bac84a5a8d',None),
  'tools/r20_graphics_plans.py':(
    HERE.parents[0]/'candidate'/'tools'/'r20_graphics_plans.py',
    'df0b5f4ab1aa87274305222e51ea02b5adc44b26b72d72155ce38e4a2d52c9af',
    '37ec5e19ae2223d079263cbac9763fe2cb915593f9d4e37151cff7d522fa562f')
}
def sha(b):return hashlib.sha256(b).hexdigest()
def build(out):
    manifest={'format':1,'version':'2.0.2','files':[]}
    binaries={}
    for rel,(path,expected,before) in FILES.items():
        if not path.is_file() or path.is_symlink():raise ValueError('Missing source '+str(path))
        data=path.read_bytes()
        if sha(data)!=expected:raise ValueError('Unexpected '+rel+' SHA-256 '+sha(data))
        manifest['files'].append({'path':rel,'sha256':expected,'before_sha256':before})
        binaries[rel]=data
    out=Path(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('manifest.json',json.dumps(manifest,indent=2,ensure_ascii=True)+'\n')
        for k,v in binaries.items():z.writestr('payload/'+k,v)
    with zipfile.ZipFile(out) as z:
        assert set(z.namelist())=={'manifest.json',*('payload/'+p for p in FILES)}
        assert json.loads(z.read('manifest.json'))==manifest
        for p in FILES:assert sha(z.read('payload/'+p))==FILES[p][1]
    return {'version':'2.0.2','files':len(FILES),'archive_sha256':sha(out.read_bytes()),'bytes':out.stat().st_size}
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='dist/AIVE_UPDATE.zip')
    args=parser.parse_args()
    print(json.dumps(build(args.output),indent=2))
