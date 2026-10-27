"""R1.9.12: build optional-timecode ASR-first hotfix from exact R1.9.11 assets."""
from __future__ import annotations
import base64, hashlib, io, json, pathlib, zipfile, zlib
from build_r1911_speech import build as build_r1911
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/AIVE_UPDATE.zip'
BASE_SHA={
 'tools/r193_pipeline.py':'b5c9ebba6bf9e1baa204868751c9a232392f9ad16ae488dc7aa394835777a856',
 'tools/r193_docx_reader.py':'c8b682a2fd1f7b18273227914e84e8e1547afd9f1f4c7e0bd1ecd86ba851a822'
}
AFTER={
 'tools/r193_pipeline.py':'44d18e3ba2d79327545334d987de21d6e6e220309226313a2fdb83db080f932d',
 'tools/r193_docx_reader.py':'2d0c4c74d01ec22a678cf7a5f2cad942b0c392af9cbc1e58d55b30481b46b819',
 'tools/r1912_optional_tc.py':'c5d3178a758143cba942c34f5dd6f98600c798eac7334a334011de55c05cffd0'
}
def sha(data):return hashlib.sha256(data).hexdigest()
def once(s,old,new):
 if s.count(old)!=1:raise ValueError('R1.9.12: unexpected patch anchor '+repr(old[:55]))
 return s.replace(old,new)
def build():
 build_r1911()
 with zipfile.ZipFile(OUT) as z:
  prior=z.read('payload/tools/r193_pipeline.py')
 raw=base64.b64decode((ROOT/'release/assets/v1.9.3.zip.b64').read_text('ascii').strip(),validate=True)
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  previous_reader=z.read('payload/tools/r193_docx_reader.py')
 assert sha(prior)==BASE_SHA['tools/r193_pipeline.py']
 assert sha(previous_reader)==BASE_SHA['tools/r193_docx_reader.py']
 p=prior.decode('utf8')
 p=once(p,'R1911_SPEECH_FIRST_V1','R1912_OPTIONAL_TC_V1')
 p=once(p,'''              from r1911_speech_first import suggest_boundaries, validate_speech_only
              # Use the existing proven ASR and plan generator. Change only the
              # matching policy and ensure no fallback plan reaches Premiere.
              old_media=r143_build.detect_media
              old_match=r143_build.suggest_boundaries
              old_write=r143_build.write_results
              proposals={}
              def guarded_match(ev,words,max_search_s=50.):
                  result=suggest_boundaries(ev,words,max_search_s=max_search_s)
                  proposals[ev['id']]=result
                  return result''',
 '''              from r1911_speech_first import suggest_boundaries as timed_match, validate_speech_only
              from r1912_optional_tc import (prepare_document, mark_plan,
                  suggest_untimed, safe_untimed)
              # Preflight source durations BEFORE loading the model or transcribing.
              # Untimed quotes in >8min media stop without altering the timeline.
              prepared,hints=prepare_document(parsed,mapping,r143_build.source_length)
              old_media=r143_build.detect_media
              old_match=r143_build.suggest_boundaries
              old_write=r143_build.write_results
              old_generate=r143_build.generate
              old_safe=r143_build.is_safe
              proposals={}
              def guarded_generate(document,sequence):
                  return mark_plan(old_generate(prepared,sequence),hints)
              def guarded_match(ev,words,max_search_s=50.):
                  result=(suggest_untimed(ev,words) if ev.get('timecodeHint') else
                          timed_match(ev,words,max_search_s=max_search_s))
                  proposals[ev['id']]=result
                  return result
              def guarded_safe(proposal,ev,minimum,max_drift):
                  if ev.get('timecodeHint'):
                      return safe_untimed(proposal,ev,minimum)
                  return old_safe(proposal,ev,minimum,max_drift)''')
 p=once(p,'''                  # Runs BEFORE old_write: unsafe plans never overwrite good JSON.
                  validate_speech_only(plan)''',
 '''                  # Runs BEFORE old_write: unsafe plans never overwrite good JSON.
                  if plan.get('review'):
                      raise ValueError('OPRIT: pasajele din DOCX au fost omise; '+
                          '; '.join(x.get('id','?') for x in plan['review']))
                  validate_speech_only(plan)''')
 p=once(p,'''              r143_build.detect_media=lambda folder,codes: {c:mapping[c] for c in codes}
              r143_build.suggest_boundaries=guarded_match
              r143_build.write_results=guarded_write''',
 '''              r143_build.detect_media=lambda folder,codes: {c:mapping[c] for c in codes}
              r143_build.generate=guarded_generate
              r143_build.suggest_boundaries=guarded_match
              r143_build.is_safe=guarded_safe
              r143_build.write_results=guarded_write''')
 p=once(p,'''                  r143_build.detect_media=old_media
                  r143_build.suggest_boundaries=old_match
                  r143_build.write_results=old_write''',
 '''                  r143_build.detect_media=old_media
                  r143_build.generate=old_generate
                  r143_build.suggest_boundaries=old_match
                  r143_build.is_safe=old_safe
                  r143_build.write_results=old_write''')
 r=previous_reader.decode('utf8')
 r=once(r,"RANGE=re.compile(r'^\\s*('+TC+r')\\s*[\\u2013\\u2014\\-]\\s*('+TC+r')?\\s*$')",
        "RANGE=re.compile(r'^\\s*('+TC+r')?\\s*[\\u2013\\u2014\\-]\\s*('+TC+r')?\\s*$')")
 r=once(r,'        if rang:\n','        if rang and (rang.group(1) or rang.group(2)):\n')
 module=zlib.decompress(base64.b64decode((ROOT/'scripts/r1912_module.zlib.b64').read_text('ascii').strip(),validate=True))
 contents={'tools/r193_pipeline.py':p.encode('utf8'),
           'tools/r193_docx_reader.py':r.encode('utf8'),
           'tools/r1912_optional_tc.py':module}
 for path,blob in contents.items():
  compile(blob,path,'exec')
  if sha(blob)!=AFTER[path]:raise ValueError('Final checksum differs: '+path+' '+sha(blob))
 manifest={'format':1,'version':'1.9.12','files':[
    {'path':path,'sha256':sha(blob),'before_sha256':BASE_SHA.get(path)}
    for path,blob in contents.items()]}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=True,indent=2)+'\n')
  for path,blob in contents.items():z.writestr('payload/'+path,blob)
 with zipfile.ZipFile(OUT) as z:
  for row in manifest['files']:
   assert sha(z.read('payload/'+row['path']))==row['sha256']
 print('R1.9.12 verified:',OUT.stat().st_size,'bytes')
if __name__=='__main__':build()
