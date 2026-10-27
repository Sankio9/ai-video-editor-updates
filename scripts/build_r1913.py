"""Build R1.9.13: full-phrase ASR second pass, optional TC, fail-closed diagnostics.

Applies DIRECTLY over stable v1.9.11. Reproduces tested v1.9.12 source
from immutable, hash-checked historical base then adds small checked patch.
"""
from __future__ import annotations
import base64,hashlib,json,pathlib,zipfile,zlib
from build_r1912 import build as build_r1912
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/AIVE_UPDATE.zip'
SHA_PIPELINE='8b49231f2c534f87ac2486f407fbc4466b1a2c77ee99961d0ed17d500959080e'
SHA_MATCHER='873604fd8298e93eab52276dc60979e14c34c5d37485fbedd2486aa1893f330a'
def sha(data):return hashlib.sha256(data).hexdigest()
def once(s,a,b):
 if s.count(a)!=1:raise ValueError('Unexpected source anchor: '+repr(a[:90]))
 return s.replace(a,b,1)
def build():
 build_r1912()
 with zipfile.ZipFile(OUT) as z:
  old=json.loads(z.read('manifest.json'))
  files={item['path']:z.read('payload/'+item['path']) for item in old['files']}
  before={item['path']:item.get('before_sha256') for item in old['files']}
 for item in old['files']:
  if sha(files[item['path']])!=item['sha256']:raise ValueError('Base checksum changed')
 key='tools/r193_pipeline.py'
 text=files[key].decode('utf8')
 text=once(text,'R1912_OPTIONAL_TC_V1\\0','R1913_FULL_PHRASE_V1\\0')
 text=once(text,
   'from r1911_speech_first import suggest_boundaries as timed_match, validate_speech_only',
   'from r1913_robust_match import suggest_boundaries as timed_match\n              from r1911_speech_first import validate_speech_only')
 oldguard='''                  validate_speech_only(plan)
                  return old_write(plan,rows,target)'''
 newguard='''                  try:
                      validate_speech_only(plan)
                  except ValueError as ex:
                      reportfile=ROOT/'Temp'/'R193'/'last_match_diagnostic.json'
                      reportfile.parent.mkdir(parents=True,exist_ok=True)
                      diagnostic={'schema':'aive-match-diagnostic-v1',
                                  'sourceDocx':str(docx),
                                  'events':[{'id':e.get('id'),'sourceCode':e.get('sourceCode'),
                                             'scriptText':e.get('text'),
                                             'scriptIn':e.get('inSeconds'),
                                             'scriptOut':e.get('outSeconds'),
                                             'asr':e.get('asr')} for e in plan.get('events',[])
                                            if e.get('kind')=='cut']}
                      reportfile.write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2),encoding='utf8')
                      raise ValueError(str(ex)+' Diagnostic local: '+str(reportfile)) from ex
                  return old_write(plan,rows,target)'''
 text=once(text,oldguard,newguard)
 files[key]=text.encode('utf8')
 files['tools/r1913_robust_match.py']=zlib.decompress(base64.b64decode(
   (ROOT/'scripts/r1913_module.zlib.b64').read_text('ascii').strip(),validate=True))
 before['tools/r1913_robust_match.py']=None
 if sha(files[key])!=SHA_PIPELINE:raise ValueError('Pipeline SHA mismatch: '+sha(files[key]))
 if sha(files['tools/r1913_robust_match.py'])!=SHA_MATCHER:
  raise ValueError('New matcher SHA mismatch: '+sha(files['tools/r1913_robust_match.py']))
 for path,data in files.items():compile(data,path,'exec')
 manifest={'format':1,'version':'1.9.13','files':[
  {'path':p,'sha256':sha(data),'before_sha256':before[p]} for p,data in sorted(files.items())]}
 with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.writestr('manifest.json',json.dumps(manifest,indent=2,ensure_ascii=True)+'\n')
  for path,data in sorted(files.items()):z.writestr('payload/'+path,data)
 with zipfile.ZipFile(OUT) as z:
  for entry in manifest['files']:
   if sha(z.read('payload/'+entry['path']))!=entry['sha256']:
    raise ValueError('Artifact checksum mismatch')
 print('R1.9.13 verified:',OUT.stat().st_size,'bytes')
if __name__=='__main__':build()
