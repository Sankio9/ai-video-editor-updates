"""Build R1.9.11 ASR-first, never timecode-fallback hotfix over R1.9.10."""
from __future__ import annotations
import hashlib,json,zipfile,pathlib
from build_r199 import build as build_r199
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/AIVE_UPDATE.zip'
PATH='tools/r193_pipeline.py'
MODULE='tools/r1911_speech_first.py'
BEFORE='f710ce32094d858bbb0137b1790625733a2c1e2b215c438179d3e9f3e68ff029'
AFTER='b5c9ebba6bf9e1baa204868751c9a232392f9ad16ae488dc7aa394835777a856'

def patch(s,old,new):
    if s.count(old)!=1:raise ValueError('Patch location changed: '+repr(old[:70]))
    return s.replace(old,new)
def build():
    build_r199()
    with zipfile.ZipFile(OUT) as z:raw=z.read('payload/'+PATH)
    if hashlib.sha256(raw).hexdigest()!=BEFORE:raise ValueError('Unexpected prior pipeline')
    s=raw.decode('utf8')
    s=patch(s,'    digest=fingerprint(docx,mapping)',
        '    # R1.9.11 policy change invalidates legacy timecode-fallback plan cache.\n'
        '    digest=hashlib.sha256(("R1911_SPEECH_FIRST_V1\\0"+fingerprint(docx,mapping)).encode("utf8")).hexdigest()')
    old='''              import argparse
              import r143_build
              original=r143_build.detect_media
              r143_build.detect_media=lambda folder,codes: {c:mapping[c] for c in codes}
              try:
                  args=argparse.Namespace(docx=docx,media_dir=ROOT,transcripts_json=None,
                      model=model,device=device,output=path,postroll=.5,min_score=.67,
                      max_drift=15.,keep_temp=False)
                  r143_build.run(args)
              finally:
                  r143_build.detect_media=original'''
    new='''              import argparse
              import r143_build
              from r1911_speech_first import suggest_boundaries, validate_speech_only
              # Use the existing proven ASR and plan generator. Change only the
              # matching policy and ensure no fallback plan reaches Premiere.
              old_media=r143_build.detect_media
              old_match=r143_build.suggest_boundaries
              old_write=r143_build.write_results
              proposals={}
              def guarded_match(ev,words,max_search_s=50.):
                  result=suggest_boundaries(ev,words,max_search_s=max_search_s)
                  proposals[ev['id']]=result
                  return result
              def guarded_write(plan, rows, target):
                  for event in plan.get('events',[]):
                      if event.get('kind')=='cut':
                          suggestion=proposals.get(event.get('id'),{})
                          event['asr']['fullTextScore']=suggestion.get('fullTextScore',0.)
                          event['asr']['matcherVersion']=suggestion.get('matchMethod','')
                          event['asr']['driftSeconds']=suggestion.get('driftSeconds')
                  # Runs BEFORE old_write: unsafe plans never overwrite good JSON.
                  validate_speech_only(plan)
                  return old_write(plan,rows,target)
              r143_build.detect_media=lambda folder,codes: {c:mapping[c] for c in codes}
              r143_build.suggest_boundaries=guarded_match
              r143_build.write_results=guarded_write
              try:
                  args=argparse.Namespace(docx=docx,media_dir=ROOT,transcripts_json=None,
                      model=model,device=device,output=path,postroll=.5,min_score=.67,
                      max_drift=75.,keep_temp=False)
                  r143_build.run(args)
              finally:
                  r143_build.detect_media=old_media
                  r143_build.suggest_boundaries=old_match
                  r143_build.write_results=old_write'''
    s=patch(s,old,new)
    s=patch(s,"    review=plan.get('aiReview',[])",
        "    from r1911_speech_first import validate_speech_only\n    validate_speech_only(plan)\n    review=plan.get('aiReview',[])")
    output=s.encode('utf8')
    if hashlib.sha256(output).hexdigest()!=AFTER:raise ValueError('Output SHA does not match tested file')
    speech=(ROOT/'scripts/r1911_speech_first.py').read_bytes()
    compile(output,PATH,'exec');compile(speech,MODULE,'exec')
    files={PATH:output,MODULE:speech}
    manifest={'format':1,'version':'1.9.11','files':[
        {'path':p,'sha256':hashlib.sha256(v).hexdigest(),
         'before_sha256':BEFORE if p==PATH else None} for p,v in sorted(files.items())]}
    with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=True,indent=2)+'\n')
        for p,v in sorted(files.items()):z.writestr('payload/'+p,v)
    with zipfile.ZipFile(OUT) as z:
        for entry in manifest['files']:
            assert hashlib.sha256(z.read('payload/'+entry['path'])).hexdigest()==entry['sha256']
    print('Safe ASR-first update ready, bytes:',OUT.stat().st_size)
if __name__=='__main__':build()
