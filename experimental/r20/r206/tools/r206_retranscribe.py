"""R2.0.6 experimental offline selective ASR runner: NO timeline operations.

Explicit --execute, local CTranslate2 model folder + ffmpeg/ffprobe and source map.
All output contains *unapproved candidate words*. Audio and private transcripts
remain on local machine. No network calls; no model auto-downloading.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path

SCHEMA_IN = "aive-r206-asr-rescan-request-v1"
SCHEMA_OUT = "aive-r206-unapproved-asr-candidates-v1"
MEDIA_EXT = frozenset((".mp4",".mov",".mxf",".avi",".mkv",".mts",".m2ts",
                      ".wav",".mp3",".m4a",".aac",".flac",".wma"))
MAX_WINDOWS = 1500


def number(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)


def validate(request,media_map):
    if not isinstance(request,dict) or request.get("schema")!=SCHEMA_IN:
        raise ValueError("Invalid R206 rescan request schema")
    if request.get("automaticCuttingAllowed") is not False or request.get("safeToModifyPremiereTimeline") is not False:
        raise ValueError("Unexpected automatic-cut permission")
    if request.get("action")!="REQUEST_SELECTIVE_RETRANSCRIPTION_ONLY":
        raise ValueError("Wrong R206 action")
    sources=request.get("rescans")
    if not isinstance(sources,list) or len(sources)>300:
        raise ValueError("Invalid rescan list")
    if not isinstance(media_map,dict):raise ValueError("Missing media map")
    out=[];used=set();total=0
    for row in sources:
        code=row.get("sourceCode") if isinstance(row,dict) else None
        if not isinstance(code,str) or not code.isdigit() or len(code)!=4 or code in used:
            raise ValueError("Duplicate/invalid source code")
        used.add(code)
        p=media_map.get(code)
        if not isinstance(p,str) or not p:raise ValueError("Offline/unmapped source "+code)
        file=Path(p)
        if not file.is_file() or file.suffix.casefold() not in MEDIA_EXT:
            raise ValueError("Missing/invalid original media for "+code)
        if file.stat().st_size<=0:raise ValueError("Empty original source "+code)
        duration=row.get("sourceDurationSeconds")
        if not number(duration) or duration<=0:raise ValueError("Invalid original source length "+code)
        windows=row.get("windows")
        if not isinstance(windows,list) or not windows:raise ValueError("No ASR windows")
        output_windows=[];prev_end=-1.
        for w in windows:
            if not isinstance(w,dict):raise ValueError("Invalid window")
            a,b=w.get("startSeconds"),w.get("endSeconds")
            if not number(a) or not number(b) or a<0 or b-a<.25 or b>duration+.02:
                raise ValueError("Window bounds unsafe for source "+code)
            if a<prev_end-0.001:raise ValueError("ASR windows overlap or are unordered")
            cut_ids=w.get("cutIds")
            if not isinstance(cut_ids,list) or not cut_ids or any(not isinstance(x,str) or not x.startswith("CUT-") for x in cut_ids):
                raise ValueError("Missing origin CUT ids")
            prev_end=b
            output_windows.append((float(a),float(b),list(cut_ids)))
            total+=1
            if total>MAX_WINDOWS:raise ValueError("Too many ASR windows")
        out.append((code,file,float(duration),output_windows))
    return out


def actual_media_duration(media,ffprobe):
    args=[str(ffprobe),"-v","error","-show_entries","format=duration",
          "-of","default=noprint_wrappers=1:nokey=1",str(media)]
    r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     text=True,timeout=45,check=False)
    if r.returncode!=0:raise ValueError("Cannot probe local source")
    try:duration=float(r.stdout.strip())
    except Exception as exc:raise ValueError("Invalid duration from ffprobe") from exc
    if not number(duration) or duration<=0:raise ValueError("Invalid probed duration")
    return duration


def extract_window(media,start,end,out_wav,ffmpeg):
    args=[str(ffmpeg),"-nostdin","-hide_banner","-loglevel","error",
          "-y","-ss",format(start,".3f"),"-i",str(media),
          "-t",format(end-start,".3f"),"-vn","-ac","1","-ar","16000",
          "-c:a","pcm_s16le",str(out_wav)]
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     timeout=240,check=False)
    if p.returncode!=0 or not out_wav.is_file() or out_wav.stat().st_size<=44:
        raise ValueError("ffmpeg audio extraction failed")


def make_whisper(model_dir,device="cuda",compute_type="int8_float16"):
    model_dir=Path(model_dir)
    if not model_dir.is_dir() or not (model_dir/"model.bin").is_file():
        raise ValueError("Missing local preinstalled CTranslate2 Whisper model (no downloads)")
    from faster_whisper import WhisperModel
    model=WhisperModel(str(model_dir),device=device,compute_type=compute_type)
    def transcribe(wav):
        segments,info=model.transcribe(str(wav),language=None,task="transcribe",
            beam_size=5,temperature=0,condition_on_previous_text=False,
            word_timestamps=True,vad_filter=False)
        words=[]
        for segment in segments:
            for word in (getattr(segment,"words",None) or []):
                words.append({"start":float(word.start),"end":float(word.end),
                    "text":str(word.word),"probability":float(word.probability or 0.)})
        return {"language":str(info.language or "unknown"),"words":words}
    return transcribe


def repeated_phrases(words):
    terms=[str(w["text"]).lower().strip(".,!?:; \t") for w in words]
    ngrams=[tuple(terms[i:i+3]) for i in range(max(0,len(terms)-2))]
    return any(ngrams.count(triple)>=4 for triple in set(ngrams))


def execute(request,source_map,transcribe,*,ffmpeg="ffmpeg",ffprobe="ffprobe",
            probe_fn=actual_media_duration,extract_fn=extract_window,tempdir=None):
    """Inject transcribe/probe/extract in tests. No Premiere access, no cut plan."""
    resolved=validate(request,source_map)
    # Full preflight before first decoder/transcriber call.
    for code,path,expected,_ in resolved:
        measured=probe_fn(path,ffprobe)
        if not number(measured) or abs(measured-expected)>1.25:
            raise ValueError("Original source changed since ASR diagnostic: "+code)
    result={"schema":SCHEMA_OUT,"safeToModifyPremiereTimeline":False,
            "automaticCuttingAllowed":False,"sourceDiagnosticSHA256":request.get("sourceDiagnosticSHA256"),
            "rescans":[],"blocked":request.get("blocked",[])}
    with tempfile.TemporaryDirectory(prefix="aive_r206_",dir=tempdir) as directory:
        folder=Path(directory)
        for code,path,duration,windows in resolved:
            src_stat=path.stat()
            source_result={"sourceCode":code,"sizeBytes":src_stat.st_size,
                           "mtimeNs":src_stat.st_mtime_ns,"windows":[]}
            for idx,(start,end,ids) in enumerate(windows):
                wav=folder/(code+"_"+str(idx)+".wav")
                extract_fn(path,start,end,wav,ffmpeg)
                if not wav.is_file() or wav.stat().st_size<4:
                    raise ValueError("Decoder did not create an audio window")
                t=transcribe(wav)
                if not isinstance(t,dict) or not isinstance(t.get("words"),list):
                    raise ValueError("Invalid ASR candidate response")
                words=[]
                for word in t["words"]:
                    a,b=word.get("start"),word.get("end")
                    if not number(a) or not number(b) or a<0 or b<a or b>end-start+.35:
                        raise ValueError("ASR word timing outside requested audio")
                    if not isinstance(word.get("text"),str):
                        raise ValueError("ASR word text invalid")
                    probability=word.get("probability")
                    if probability is not None and (not number(probability) or not 0<=probability<=1):
                        raise ValueError("Invalid ASR word probability")
                    words.append({"startSeconds":round(start+a,3),
                                  "endSeconds":round(start+b,3),
                                  "text":word["text"],
                                  "probability":probability})
                flags=[]
                if not words:flags.append("ASR_EMPTY")
                elif repeated_phrases(words):flags.append("POSSIBLE_ASR_REPETITION")
                source_result["windows"].append({
                    "startSeconds":start,"endSeconds":end,"cutIds":ids,
                    "status":"REVIEW_REQUIRED","qualityFlags":flags,
                    "detectedLanguage":str(t.get("language") or "unknown"),
                    "words":words})
                wav.unlink(missing_ok=True)
            result["rescans"].append(source_result)
    return result


def save_report(report,destination):
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    tmp=destination.with_name(destination.name+".tmp")
    try:
        tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
        tmp.replace(destination)
    finally:
        tmp.unlink(missing_ok=True)


def main():
    a=argparse.ArgumentParser(description="R2.0.6 experimental offline ASR, never Premiere")
    a.add_argument("--request",type=Path,required=True)
    source_input=a.add_mutually_exclusive_group(required=True)
    source_input.add_argument("--source-map",type=Path,
                              help="Already resolved local source paths")
    source_input.add_argument("--project-inventory",type=Path,
                              help="Recursive Project Panel inventory from CEP; no manual mapping")
    a.add_argument("--output",type=Path,required=True)
    a.add_argument("--model-path",type=Path,required=True)
    a.add_argument("--ffmpeg",default="ffmpeg")
    a.add_argument("--ffprobe",default="ffprobe")
    a.add_argument("--temp",type=Path)
    a.add_argument("--device",choices=("cuda","cpu"),default="cuda")
    a.add_argument("--compute-type",default="int8_float16")
    a.add_argument("--execute",action="store_true",help="Requires explicit higher-level application action")
    p=a.parse_args()
    request=json.loads(p.request.read_text("utf8"))
    if p.project_inventory:
        from r206_source_inventory import sources_for_rescan
        inventory=json.loads(p.project_inventory.read_text("utf8"))
        source_map=sources_for_rescan(request,inventory)
    else:
        source_map=json.loads(p.source_map.read_text("utf8"))
    validated=validate(request,source_map)
    if not p.execute:
        print(json.dumps({"ok":True,"dryRun":True,"sourceCount":len(validated),
                         "automaticCuttingAllowed":False}))
        return
    transcription=make_whisper(p.model_path,p.device,p.compute_type)
    output=execute(request,source_map,transcription,ffmpeg=p.ffmpeg,ffprobe=p.ffprobe,tempdir=p.temp)
    save_report(output,p.output)
    print(json.dumps({"ok":True,"status":"LOCAL_ASR_REVIEW_REQUIRED",
                      "sources":len(output["rescans"]),"automaticCuttingAllowed":False}))

if __name__=="__main__":main()
