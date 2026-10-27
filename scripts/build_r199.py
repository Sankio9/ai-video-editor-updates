"""Safe R1.9.9 Project-bin and source-name lookup hotfix, from R1.9.8."""
from __future__ import annotations
import base64, hashlib, io, json, pathlib, zipfile
from build_r198 import build as build_r198
REPO=pathlib.Path(__file__).resolve().parents[1]
OUT=REPO/'dist/AIVE_UPDATE.zip'
BASE=REPO/'release/assets/v1.9.3.zip.b64'
BEFORE={'cep/jsx/r193_media_probe.jsx':'0398cd90cf328d1182fa08f6b4944e799fea829a4b299c217afe396b5ca91e4d',
        'tools/r193_pipeline.py':'b888441cf6d58397f0387a65e1fe44503ca1c197061ef41152d70b79a830b791'}
def one(source,needle,replacement):
    if source.count(needle)!=1:raise ValueError('Patch location missing or ambiguous: '+repr(needle[:85]))
    return source.replace(needle,replacement)
def build():
    build_r198()  # Reproduce EXACT previous UTF-8 patch before applying the follow-up.
    with zipfile.ZipFile(OUT) as z:
        p=z.read('payload/tools/r193_pipeline.py')
    raw=base64.b64decode(BASE.read_text('ascii').strip(),validate=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as base:
        s=base.read('payload/cep/jsx/r193_media_probe.jsx')
    data={'cep/jsx/r193_media_probe.jsx':s,'tools/r193_pipeline.py':p}
    for path,content in data.items():
        if hashlib.sha256(content).hexdigest()!=BEFORE[path]:raise ValueError('Input hash mismatch: '+path)
    jsx=s.decode('utf8')
    jsx=one(jsx,'function walk(item,depth){','function walk(item,depth,location){')
    jsx=one(jsx,
       "var type=String(x.type).toUpperCase(),num=Number(x.type);\n       if(type==='BIN'||type==='ROOT'||num===2||num===3){walk(x,depth+1);continue;}\n       if(typeof x.getMediaPath!=='function')continue;",
       "var name=String(x.name||''),place=location?location+'/'+name:name;")
    jsx=one(jsx,
       "if(p&&p!=='undefined'&&p!=='null')result.push({name:String(x.name||''),path:p});\n     }\n   }\n   walk(app.project.rootItem,0);",
       "if(p&&p!=='undefined'&&p!=='null')result.push({name:name,path:p,bin:location,projectPath:place});\n       walk(x,depth+1,place);\n     }\n   }\n   walk(app.project.rootItem,0,'');")
    jsx=one(jsx,"return JSON.stringify({ok:true,media:result,sequence:app.project.activeSequence.name,count:count});",
            "return JSON.stringify({ok:true,media:result,sequence:app.project.activeSequence.name,count:count,scanned:{items:count}});")
    data['cep/jsx/r193_media_probe.jsx']=jsx.encode('utf8')
    py=p.decode('utf8')
    py=one(py,
      "match = re.search(r'(\\d{4})$', path.stem)\n        if not match or match.group(1) not in choices: continue",
      """# Search Premiere display name AND original basename, in any Project bin.
        # 9881_01.mov and DJI_9881_B.mp4 are valid; 199881.mov is not.
        pattern=lambda code: r'(?<!\\d)'+re.escape(code)+r'(?!\\d)'
        named={code for code in codes if re.search(pattern(code),str(entry.get('name') or ''))}
        disk={code for code in codes if re.search(pattern(code),path.stem)}
        if (named and disk and named!=disk) or len(named)>1 or len(disk)>1:
            raise ValueError('Coduri video contradictorii/ambigue: '+str(entry.get('name') or path.name))
        found=named or disk
        if not found: continue
        code=next(iter(found))""")
    py=one(py,"if path not in choices[match.group(1)]:\n            choices[match.group(1)].append(path)",
       "if path not in choices[code]:\n            choices[code].append(path)")
    py=one(py,"raise ValueError('Verifică importul în Project Panel: ' + '; '.join(problem))",
       """samples=[str(e.get('name') or pathlib.Path(e.get('path') or '').name)+' ['+str(e.get('bin') or 'Project')+']'
                 for e in source['media'] if isinstance(e,dict) and pathlib.Path(str(e.get('path') or '')).suffix.lower() in VIDEO]
        raise ValueError('Verifică importul în Project Panel (inclusiv foldere): ' + '; '.join(problem)
                         + '. Video găsite ('+str(len(samples))+'): '+('; '.join(samples[:12]) or 'niciunul'))""".replace('pathlib.Path(', 'Path('))
    data['tools/r193_pipeline.py']=py.encode('utf8')
    manifest={'format':1,'version':'1.9.9','files':[
        {'path':p,'sha256':hashlib.sha256(data[p]).hexdigest(),'before_sha256':BEFORE[p]} for p in sorted(data)]}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=True,indent=2)+'\n')
        for p,v in sorted(data.items()):z.writestr('payload/'+p,v)
    with zipfile.ZipFile(OUT) as z:
        for entry in manifest['files']:
            assert hashlib.sha256(z.read('payload/'+entry['path'])).hexdigest()==entry['sha256']
    print('R1.9.9 safe project source resolver:',OUT,OUT.stat().st_size)
if __name__=='__main__':build()
