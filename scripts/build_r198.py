"""Build UTF-8 Windows CEP hotfix v1.9.8 from immutable v1.9.3 base."""
from __future__ import annotations
import base64,hashlib,io,json,pathlib,zipfile
REPO=pathlib.Path(__file__).resolve().parents[1]
BASE_B64=REPO/'release/assets/v1.9.3.zip.b64'
OUT=REPO/'dist/AIVE_UPDATE.zip'
BEFORE={'cep/r193_workflow.js':'d48db0182e03b9e8f8879c19af89600f6daa16adccd604867ab17c76f97534c4',
        'tools/r193_pipeline.py':'c43b4dc8a3639d30281d718ebe9b4b15e29c75363afd693241e438ee1cce1971'}
def one(old,needle,replacement):
    if old.count(needle)!=1:raise ValueError('Ambiguous patch location: '+repr(needle[:65]))
    return old.replace(needle,replacement)
def build():
    raw=base64.b64decode(BASE_B64.read_text('ascii').strip(),validate=True)
    data={}
    with zipfile.ZipFile(io.BytesIO(raw)) as src:
        manifest=json.loads(src.read('manifest.json'))
        if manifest.get('version')!='1.9.3':raise ValueError('Unexpected base version')
        for path,expected in BEFORE.items():
            data[path]=src.read('payload/'+path)
            if hashlib.sha256(data[path]).hexdigest()!=expected:raise ValueError('Base hash mismatch: '+path)
    workflow=data['cep/r193_workflow.js'].decode('utf8')
    workflow=one(workflow,
        "var p=cp.spawn(python,args,{cwd:root,windowsHide:true}),tail='',full='',finished=false;",
        "// R1.9.8: Windows pipes must be UTF-8 for Romanian speech and progress messages.\n     var env=Object.assign({},process.env,{PYTHONIOENCODING:'utf-8:backslashreplace',PYTHONUTF8:'1'});\n     var p=cp.spawn(python,['-X','utf8'].concat(args),{cwd:root,windowsHide:true,env:env}),tail='',full='',finished=false;")
    data['cep/r193_workflow.js']=workflow.encode('utf8')
    pipeline=data['tools/r193_pipeline.py'].decode('utf8')
    needle="if str(TOOLS) not in sys.path: sys.path.insert(0, str(TOOLS))"
    pipeline=one(pipeline,needle,needle+"\n# R1.9.8: avoid cp1252 crashes under Windows CEP.\nfor _stream in (sys.stdout, sys.stderr):\n    if hasattr(_stream, 'reconfigure'):\n        try: _stream.reconfigure(encoding='utf-8', errors='backslashreplace')\n        except (OSError, ValueError): pass")
    pipeline=one(pipeline,"json.dumps(result,ensure_ascii=False),flush=True","json.dumps(result,ensure_ascii=True),flush=True")
    pipeline=one(pipeline,"json.dumps({'ok':False,'message':str(ex)},ensure_ascii=False),flush=True","json.dumps({'ok':False,'message':str(ex)},ensure_ascii=True),flush=True")
    data['tools/r193_pipeline.py']=pipeline.encode('utf8')
    manifest={'format':1,'version':'1.9.8','files':[
        {'path':p,'sha256':hashlib.sha256(v).hexdigest(),'before_sha256':BEFORE[p]} for p,v in sorted(data.items())
    ]}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as dst:
        dst.writestr('manifest.json',json.dumps(manifest,ensure_ascii=True,indent=2)+'\n')
        for p,v in sorted(data.items()):dst.writestr('payload/'+p,v)
    with zipfile.ZipFile(OUT) as z:
        for entry in manifest['files']:
            assert hashlib.sha256(z.read('payload/'+entry['path'])).hexdigest()==entry['sha256']
    print('R1.9.8 verified:',OUT,OUT.stat().st_size)
if __name__=='__main__':build()
