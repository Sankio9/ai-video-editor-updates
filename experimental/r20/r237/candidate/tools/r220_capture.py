"""R2.2 one-click Montage analysis capture from original R143 plan.

Called ONLY inside patched r193_pipeline.guarded_write, *before* legacy
write_results. Raises R220Captured after saving a local analysis plan; the
legacy montage JSON is never overwritten by an incomplete plan.

Private DOCX, transcript, source paths and resulting JSON stay on workstation.
"""
from __future__ import annotations
import hashlib,json,math,os
from pathlib import Path
from r220_montage_plan import build,digest,save_private_report

class R220Captured(Exception):
    def __init__(self,detail):
        self.detail=detail
        super().__init__("R220_CAPTURE_COMPLETED")

def _finite(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)

def _media_inventory(source, mapping):
    entries=source.get("media")
    if not isinstance(entries,list):raise ValueError("R220_MEDIA_MANIFEST_MISSING")
    result={}
    for code,media in mapping.items():
        candidates=[v for v in entries if isinstance(v,dict) and
                    Path(str(v.get("path",""))).resolve()==Path(media).resolve()]
        if len(candidates)!=1:raise ValueError("R220_SOURCE_AMBIGUOUS: "+code)
        c=candidates[0]
        if not c.get("nodeId") or not c.get("name") or c.get("offline"):
            raise ValueError("R220_SOURCE_OFFLINE_OR_ID_MISSING "+code)
        result[code]={"state":"ONLINE","nodeId":str(c["nodeId"]),"name":c["name"]}
    return result

def _duration_voice(ev):
    # R143 VO card / vo_gap: editorial duration reserved, never source IN/OUT.
    # Honor explicit valid duration only if the legacy plan exposes it.
    for k in ("durationSeconds","estimatedDuration","duration","estimatedSeconds","seconds"):
        x=ev.get(k)
        if _finite(x) and 1<=x<=45:return round(x,3)
    return 7.

def capture(plan,mapping,docx,media_json,sequence_id):
    from r1911_speech_first import MIN_BOUNDARY_SCORE,MIN_FULL_TEXT_SCORE
    if not isinstance(plan,dict) or plan.get("aiAnalysis",{}).get("runtime",{}).get("mode")!="REAL_AUDIO":
        raise ValueError("R220_REQUIRES_REAL_ASR")
    original=plan.get("events")
    if not isinstance(original,list) or not original:raise ValueError("R220_NO_EVENTS")
    source=json.loads(Path(media_json).read_text(encoding="utf8"))
    if source.get("sequenceId")!=sequence_id:raise ValueError("R220_SEQUENCE_CHANGED")
    if not "[AIVE TEST]" in str(source.get("sequence") or ""):
        raise ValueError("R220_COPY_SEQUENCE_REQUIRED")
    strike_audit=None
    original=os.environ.get("AIVE_R237_SOURCE_DOCX")
    if original:
        from r237_strikethrough_docx import verify as verify_strike
        audit_file=os.environ.get("AIVE_R237_AUDIT_PATH")
        if not audit_file:raise ValueError("R237_STRIKE_AUDIT_MISSING")
        strike_audit=verify_strike(original,docx,audit_file)
        docs=Path(original).read_bytes()
    else:
        docs=Path(docx).read_bytes()
    identity={"docxSHA256":hashlib.sha256(docs).hexdigest(),
              "sequenceId":str(sequence_id)}
    diagnostic={"schema":"aive-match-diagnostic-v1","events":[]}
    passed=[]
    # Track all R143 events to preserve the original VO slots and order.
    for event in original:
        kind=event.get("kind")
        if kind=="cut":
            asr=dict(event.get("asr") or {})
            cid=str(event.get("id"))
            diagnostic["events"].append({
                "id":cid,"sourceCode":str(event.get("sourceCode")),
                "scriptText":event.get("text") or "",
                "scriptIn":event.get("inSeconds"),
                "scriptOut":event.get("outSeconds"),
                "asr":asr})
            if (asr.get("status")=="AI_MATCHED" and
                all(_finite(asr.get(k)) and asr[k]>=floor for k,floor in
                    (("startScore",MIN_BOUNDARY_SCORE),
                     ("endScore",MIN_BOUNDARY_SCORE),
                     ("fullTextScore",MIN_FULL_TEXT_SCORE)))):
                passed.append(cid)
        elif kind in ("vo","vo_gap","voice","voiceover","vo_card","card","narration"):
            pass
        else:
            raise ValueError("R220_UNKNOWN_EDITORIAL_EVENT_KIND:"+str(kind))
    if plan.get("review"):
        # Do not silently discard unmounted DOCX paragraphs.
        raise ValueError("R220_UNMOUNTED_DOCX_SEGMENTS: review original DOCX")
    if not diagnostic["events"]:raise ValueError("R220_NO_CUTS")
    diag_hash=digest(diagnostic)
    identity["diagnosticSHA256"]=diag_hash
    inventory=_media_inventory(source,mapping)
    generated,report=build(diagnostic,identity,inventory,passed)
    # Real R143 plan may contain voiceover cards. The earlier diagnostic
    # contains only CUTs, so reconstruct all original editoral events.
    by_id={v["cutId"]:dict(v) for v in generated["cuts"]}
    cursor=0.;combined=[];voice_index=0
    for original_event in original:
        if original_event.get("kind")=="cut":
            row=by_id[str(original_event["id"])]
        elif original_event.get("kind") in ("vo","vo_gap","voice","voiceover","vo_card","card","narration"):
            voice_index+=1
            seconds=_duration_voice(original_event)
            row={"cutId":"VO-%03d"%voice_index,"sourceCode":None,
                 "sourceName":None,"state":"VO_RESERVE",
                 "durationSeconds":seconds,"durationKind":"VO_EDITORIAL_RESERVED",
                 "estimated":True}
        else:
            raise ValueError("R220_UNKNOWN_EDITORIAL_EVENT_KIND:"+str(original_event.get("kind")))
        length=row["durationSeconds"]
        row["timelineStart"]=round(cursor,3)
        row["timelineEnd"]=round(cursor+length,3)
        combined.append(row)
        cursor+=length
        gap=original_event.get("gapAfterSeconds",0)
        if not _finite(gap) or gap<0 or gap>120:
            raise ValueError("R220_INVALID_EDITORIAL_GAP")
        cursor+=gap
    if len(combined)>2500:raise ValueError("R220_TOO_MANY_EVENTS")
    generated["cuts"]=combined
    generated["voReserveCount"]=voice_index
    generated["editorialEventCount"]=len(combined)
    generated["totalPlannedSeconds"]=round(cursor,3)
    if strike_audit:
        # Traceable decision attached BEFORE SHA of plan and report.
        # Original DOCX hash remains identity for all independent modules.
        generated["strikePolicy"]="OMIT_STRUCK"
        generated["strikeAudit"]={
            "originalSHA256":strike_audit["originalSHA256"],
            "filteredSHA256":strike_audit["filteredSHA256"],
            "removedCharacters":strike_audit["removedCharacters"],
            "changedParagraphs":strike_audit["changedParagraphs"],
            "auditSHA256":hashlib.sha256(json.dumps(strike_audit["audit"],
                 ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf8")).hexdigest()}
    generated.pop("planSHA256",None)
    generated["planSHA256"]=digest(generated)
    report["planSHA256"]=generated["planSHA256"]
    report["voReserveCount"]=voice_index
    report["identity"]=identity
    report["items"]=[dict(x) for x in combined if x["state"]=="PLACEHOLDER"]
    # Temporary file is local. A file can be read back / hash checked by CEP.
    root=Path(docx).resolve().parent
    if "AIVE_R220_HOME" in os.environ:
        root=Path(os.environ["AIVE_R220_HOME"])
    out=root/"Temp"/"R220"
    out.mkdir(parents=True,exist_ok=True)
    sequence_hash=hashlib.sha256(str(sequence_id).encode("utf8")).hexdigest()[:12]
    base=out/("montage_"+identity["docxSHA256"][:12]+"_"+sequence_hash)
    planfile=base.with_suffix(".plan.json")
    reportfile=base.with_suffix(".report.json")
    tmp=planfile.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(generated,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf8")
        tmp.replace(planfile)
    finally:tmp.unlink(missing_ok=True)
    save_private_report(report,reportfile)
    raise R220Captured({"ok":True,"phase":"ANALYSIS_ONLY","plan":str(planfile),
        "report":str(reportfile),"cutCount":generated["totalCuts"],
        "confirmedCount":generated["confirmedCount"],
        "placeholderCount":generated["placeholderCount"],
        "voReserveCount":voice_index,"sequenceId":str(sequence_id),
        "planSHA256":generated["planSHA256"],
        "planFileSHA256":hashlib.sha256(planfile.read_bytes()).hexdigest()})
