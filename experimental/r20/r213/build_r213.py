"""Build 2.1.3 Beta Montage safe second search from stable 1.9.13 pipeline.

Requires installed Beta 2.1.2. R1.9.13's documented pipeline SHA must
match; this changes only that file + an isolated helper. All existing
is_safe, validate_speech_only and Project Panel preflight gates remain.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile,pathlib

ROOT=pathlib.Path(__file__).resolve().parent
STABLE_ARCHIVE_SHA="9ab648fd3472d0a13ce7cb815e953894d961fcc2ea9113f250099720dabb1034"
PRIOR_BETA_ARCHIVE_SHA="e5a0a277fd13834acba3712eacec82a9f9eeaa05887668458c124797c6e89f4e"
STABLE_PIPELINE_SHA="8b49231f2c534f87ac2486f407fbc4466b1a2c77ee99961d0ed17d500959080e"
PIPELINE="tools/r193_pipeline.py"
HELPER="tools/r213_second_pass.py"
def digest(data):return hashlib.sha256(data).hexdigest()
def prior_asset(filename,sha,version):
    filename=pathlib.Path(filename)
    if not filename.is_file() or digest(filename.read_bytes())!=sha:
        raise ValueError("The exact published "+version+" release asset is required")
    with zipfile.ZipFile(filename) as z:
        m=json.loads(z.read("manifest.json"))
        if m.get("version")!=version or m.get("format")!=1:
            raise ValueError("Wrong previous release format")
        for x in m["files"]:
            if digest(z.read("payload/"+x["path"]))!=x["sha256"]:
                raise ValueError("Corrupted release manifest "+x["path"])
        return {x["path"]:z.read("payload/"+x["path"]) for x in m["files"]}
def replace_once(data,before,after):
    if data.count(before)!=1:
        raise ValueError("Wrong stable pipeline anchor: "+repr(before[:85]))
    return data.replace(before,after,1)
def build(stable,beta,output):
    base=prior_asset(stable,STABLE_ARCHIVE_SHA,"1.9.13")
    prior_asset(beta,PRIOR_BETA_ARCHIVE_SHA,"2.1.2")
    old=base.get(PIPELINE)
    if old is None or digest(old)!=STABLE_PIPELINE_SHA:
        raise ValueError("Unexpected stable Montage 01 pipeline SHA")
    code=old.decode("utf8")
    needle="              from r1913_robust_match import suggest_boundaries as timed_match"
    insert=needle+"\n              from r213_second_pass import recover as _r213_recover"
    code=replace_once(code,needle,insert)
    old_guard="""              def guarded_match(ev,words,max_search_s=50.):
                  result=(suggest_untimed(ev,words) if ev.get('timecodeHint') else
                          timed_match(ev,words,max_search_s=max_search_s))
                  proposals[ev['id']]=result
                  return result"""
    safe_guard="""              def guarded_match(ev,words,max_search_s=50.):
                  result=(suggest_untimed(ev,words) if ev.get('timecodeHint') else
                          timed_match(ev,words,max_search_s=max_search_s))
                  # R2.1.3: one conservative second search on EXISTING REAL
                  # Whisper words, only if the first robust match is weak.
                  # All R1.9.13 is_safe and validate_speech_only gates remain.
                  if not ev.get('timecodeHint'):
                      result=_r213_recover(ev,words,result,max_search_s=90.)
                  proposals[ev['id']]=result
                  return result"""
    code=replace_once(code,old_guard,safe_guard)
    if "validate_speech_only(plan)" not in code:
        raise ValueError("Mandatory Montage safe gate disappeared")
    if "r143_build.is_safe=guarded_safe" not in code:
        raise ValueError("Mandatory source/score safety gate disappeared")
    if "_r213_recover(ev,words,result,max_search_s=90.)" not in code:
        raise ValueError("Second search is not wired")
    pipeline=code.encode("utf8")
    helper_path=ROOT/"candidate"/HELPER
    if not helper_path.is_file() or helper_path.is_symlink():
        raise ValueError("Missing recovery helper")
    helper=helper_path.read_bytes()
    if not 2000<len(helper)<40000:raise ValueError("Unexpected helper")
    for marker in (b"REVIEW_ALTERNATIVE_OCCURRENCE",b"MIN_FULL_SCORE=.88",
                   b"MAX_TC_DRIFT_SECONDS=75.",b"REVIEW_SUGGESTED"):
        if marker not in helper:raise ValueError("Missing recovery safety marker")
    compile(pipeline,PIPELINE,"exec")
    compile(helper,HELPER,"exec")
    manifest={"format":1,"version":"2.1.3","files":[
        {"path":PIPELINE,"sha256":digest(pipeline),"before_sha256":digest(old)},
        {"path":HELPER,"sha256":digest(helper),"before_sha256":None}
    ]}
    output=pathlib.Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,indent=2,ensure_ascii=True)+"\n")
        z.writestr("payload/"+PIPELINE,pipeline)
        z.writestr("payload/"+HELPER,helper)
    with zipfile.ZipFile(output) as z:
        if set(z.namelist())!={"manifest.json","payload/"+PIPELINE,"payload/"+HELPER}:
            raise ValueError("Unsafe update file allowlist")
        if json.loads(z.read("manifest.json"))!=manifest:raise ValueError("Write readback failed")
        for x in manifest["files"]:
            if digest(z.read("payload/"+x["path"]))!=x["sha256"]:
                raise ValueError("Payload SHA write readback failed")
    return {"version":"2.1.3","requires":"2.1.2","files":2,
            "zip_sha256":digest(output.read_bytes()),"size":output.stat().st_size}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--stable",required=True)
    p.add_argument("--prior",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    print(json.dumps(build(a.stable,a.prior,a.output),indent=2))
