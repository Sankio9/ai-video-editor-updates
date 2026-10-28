"""R2.2 candidate — read-only Premiere montage plan, missing-CUT audit and gate.

Inputs are the current private R1.9.13 diagnostic, verified media inventory,
and a per-CUT explicit pass list from the existing legacy safe validator.
Nothing here writes Premiere, reads media/audio, or approves timeline edits.
"""
from __future__ import annotations
import hashlib,json,math,re
from pathlib import Path

SCHEMA="aive-r220-montage-plan-v1"
REPORT_SCHEMA="aive-r220-missing-cuts-v1"
_SHA=re.compile(r"[0-9a-f]{64}\Z")
_ID=re.compile(r"CUT-[0-9]{1,4}\Z")
_CODE=re.compile(r"[0-9]{4}\Z")
REASONS={
 "REVIEW_WEAK_BOUNDARY":"ASR_WEAK_BOUNDARY",
 "REVIEW_WEAK_TRANSCRIPT":"ASR_WEAK_TRANSCRIPT",
 "REVIEW_NO_MATCH":"AUDIO_NOT_FOUND",
 "REVIEW_ALTERNATIVE_OCCURRENCE":"ASR_AMBIGUOUS",
 "REVIEW_OUTSIDE_SEARCH_RADIUS":"OTHER_REVIEW",
 "REVIEW_LARGE_SHIFT":"TC_INCOMPLETE_OR_IMPLAUSIBLE",
 "REVIEW_INVALID_BOUNDS":"OTHER_REVIEW",
 "REVIEW_SUGGESTED":"ASR_REQUIRES_VALIDATION",
}
ACTIONS={
 "ASR_WEAK_BOUNDARY":"Verifică manual începutul și sfârșitul declarației.",
 "ASR_WEAK_TRANSCRIPT":"Verifică declarația; poate necesita retranscriere.",
 "AUDIO_NOT_FOUND":"Verifică audio; declarația nu este identificată.",
 "ASR_AMBIGUOUS":"Alege manual apariția corectă.",
 "ASR_REQUIRES_VALIDATION":"Confirmă limita audio înainte de inserare.",
 "SOURCE_NOT_FOUND":"Importă media în Project Panel.",
 "SOURCE_OFFLINE":"Reconectează fișierul offline.",
 "TC_INCOMPLETE_OR_IMPLAUSIBLE":"Verifică declarația și timecode-ul.",
 "OTHER_REVIEW":"Revizuiește sincronul.",
}
def finite(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
def rnd(x):
    return round(float(x),3)
def digest(obj):
    return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,
                separators=(",",":"),allow_nan=False).encode("utf8")).hexdigest()
def identity(context):
    if not isinstance(context,dict):raise ValueError("Missing document context")
    for key in ("docxSHA256","diagnosticSHA256"):
        if not isinstance(context.get(key),str) or not _SHA.fullmatch(context[key]):
            raise ValueError("Missing/invalid "+key)
    seq=context.get("sequenceId")
    if not isinstance(seq,str) or not 3<=len(seq)<=128:
        raise ValueError("Invalid active sequence")
    return {key:context[key] for key in ("docxSHA256","diagnosticSHA256","sequenceId")}
def estimate(e,a):
    # Estimated timeline SLOT ONLY; never used for source IN/OUT.
    first,last=a.get("rawMatchedIn"),a.get("rawMatchedOut")
    if finite(first) and finite(last) and 2.5<=last-first<=25.:
        return rnd(last-first),"ESTIMATED_WEAK_ASR"
    count=e.get("dialogueWordCount")
    if count is None:
        txt=e.get("text")
        if not isinstance(txt,str) or not txt.strip():
            raise ValueError("Cannot estimate duration without word count")
        count=len(txt.split())
    if not isinstance(count,int) or isinstance(count,bool) or not 1<=count<=2500:
        raise ValueError("Invalid dialogueWordCount")
    return rnd(max(2.5,min(25.,count/2.35+.8))),"ESTIMATED_WORD_COUNT"

def build(diagnostic,context,inventory,validated_cuts):
    """No source cut is trusted merely because ASR says AI_MATCHED."""
    ident=identity(context)
    if not isinstance(diagnostic,dict) or diagnostic.get("schema")!="aive-match-diagnostic-v1":
        raise ValueError("Wrong match diagnostic")
    events=diagnostic.get("events")
    if not isinstance(events,list) or not 0<len(events)<=2000:
        raise ValueError("Invalid event list")
    if not isinstance(inventory,dict) or not isinstance(validated_cuts,list):
        raise ValueError("Inventory and safe validator required")
    ids=[e.get("id") if isinstance(e,dict) else None for e in events]
    if any(not isinstance(i,str) or not _ID.fullmatch(i) for i in ids) or len(set(ids))!=len(ids):
        raise ValueError("Invalid/duplicate CUT identity")
    if len(validated_cuts)!=len(set(validated_cuts)) or not set(validated_cuts).issubset(set(ids)):
        raise ValueError("Inconsistent legacy safe validation list")
    verified=set(validated_cuts)
    cursor=0.;rows=[];missing=[]
    for e in events:
        cut=e["id"];code=e.get("sourceCode");a=e.get("asr")
        if not isinstance(code,str) or not _CODE.fullmatch(code):
            raise ValueError("Missing sourceCode for "+cut)
        if not isinstance(a,dict) or (a.get("source") is not None and str(a["source"])!=code):
            raise ValueError("Contradictory or missing ASR for "+cut)
        media=inventory.get(code)
        if not isinstance(media,dict):raise ValueError("Unscanned source "+code)
        state=media.get("state")
        if state=="AMBIGUOUS":raise ValueError("AMBIGUOUS_SOURCE_STOP "+code)
        if state not in ("ONLINE","OFFLINE","MISSING"):
            raise ValueError("Unknown media state")
        name=media.get("name")
        if name is not None and (not isinstance(name,str) or not name.strip() or len(name)>256):
            raise ValueError("Bad source name")
        if state=="ONLINE" and not name:raise ValueError("Source name not verified")
        status=a.get("matchStatus")
        if status not in set(REASONS)|{"AI_MATCHED"}:raise ValueError("UNKNOWN_MATCH_STATUS_STOP")
        is_valid=status=="AI_MATCHED" and cut in verified and state=="ONLINE"
        if is_valid:
            start,end,source_len=a.get("finalIn"),a.get("finalOut"),a.get("sourceDuration")
            if not (finite(start) and finite(end) and finite(source_len) and
                    0<=start<end<=source_len and end-start<=300):
                raise ValueError("MATCHED_BOUNDS_UNSAFE "+cut)
            length=rnd(end-start)
            row={"cutId":cut,"sourceCode":code,"sourceName":name,
                 "state":"CONFIRMED","timelineStart":rnd(cursor),
                 "timelineEnd":rnd(cursor+length),"durationSeconds":length,
                 "durationKind":"AUDIO_VERIFIED","sourceIn":rnd(start),"sourceOut":rnd(end)}
        else:
            reason=("SOURCE_NOT_FOUND" if state=="MISSING" else
                    "SOURCE_OFFLINE" if state=="OFFLINE" else
                    "ASR_REQUIRES_VALIDATION" if status=="AI_MATCHED" else REASONS[status])
            length,method=estimate(e,a)
            row={"cutId":cut,"sourceCode":code,"sourceName":name,
                 "state":"PLACEHOLDER","timelineStart":rnd(cursor),
                 "timelineEnd":rnd(cursor+length),"durationSeconds":length,
                 "durationKind":method,"estimated":True,"reason":reason,
                 "action":ACTIONS[reason]}
            missing.append(dict(row))
        rows.append(row);cursor+=length
        gap=e.get("gapAfterSeconds",0)
        if not finite(gap) or gap<0 or gap>120:raise ValueError("Unsafe editorial gap")
        cursor+=gap
    missing_sources=sorted({r["sourceCode"] for r in missing
                       if r["reason"] in ("SOURCE_NOT_FOUND","SOURCE_OFFLINE")})
    plan={"schema":SCHEMA,"phase":"ANALYSIS_ONLY","identity":ident,
          "safeToModifyPremiereTimeline":False,"approvalRequired":bool(missing),
          "reporterTimecodeUsedForCutting":False,"totalCuts":len(rows),
          "confirmedCount":len(rows)-len(missing),"placeholderCount":len(missing),
          "totalPlannedSeconds":rnd(cursor),"cuts":rows}
    plan["planSHA256"]=digest(plan)
    report={"schema":REPORT_SCHEMA,"phase":"ANALYSIS_ONLY","identity":ident,
            "planSHA256":plan["planSHA256"],
            "confirmedPlannedCount":plan["confirmedCount"],
            "placeholderPlannedCount":len(missing),
            "missingDistinctSourceCodes":missing_sources,"items":missing}
    return plan,report

def decide(plan,plan_sha,sequence_id,choice):
    """Explicit user decision and integrity test; no Premiere writes."""
    if plan.get("schema")!=SCHEMA or plan.get("phase")!="ANALYSIS_ONLY":
        raise ValueError("Invalid montage plan")
    if digest({k:v for k,v in plan.items() if k!="planSHA256"})!=plan.get("planSHA256"):
        raise ValueError("PLAN_CHANGED_STOP")
    if sequence_id!=plan["identity"]["sequenceId"] or plan_sha!=plan["planSHA256"]:
        raise ValueError("SEQUENCE_OR_PLAN_CHANGED_STOP")
    if choice=="STOP":return {"writeAuthorized":False,"decision":"USER_STOP"}
    required="CONTINUE_WITH_PLACEHOLDERS" if plan["approvalRequired"] else "COMPLETE_AFTER_PREFLIGHT"
    if choice!=required:raise ValueError("EXPLICIT_APPROVAL_OR_CORRECT_MODE_REQUIRED")
    return {"writeAuthorized":False,"decision":"PENDING_LIVE_PREFLIGHT",
            "approvedPlanSHA256":plan_sha,"sequenceId":sequence_id}

def verify_readback(plan,report,actual_clips,actual_markers,sequence_id):
    """Only real Premiere readback may change a plan into a success report."""
    if plan.get("planSHA256")!=report.get("planSHA256") or sequence_id!=plan["identity"]["sequenceId"]:
        raise ValueError("READBACK_IDENTITY_MISMATCH")
    clips={r["cutId"] for r in plan["cuts"] if r["state"]=="CONFIRMED"}
    slots={r["cutId"] for r in plan["cuts"] if r["state"]=="PLACEHOLDER"}
    if (not isinstance(actual_clips,list) or not isinstance(actual_markers,list) or
        len(actual_clips)!=len(set(actual_clips)) or
        len(actual_markers)!=len(set(actual_markers)) or
        set(actual_clips)!=clips or set(actual_markers)!=slots):
        raise ValueError("READBACK_OBJECT_MISMATCH")
    result=dict(report)
    result.update({"phase":"POST_READBACK","confirmedInsertedCount":len(clips),
                   "placeholderReservedCount":len(slots),
                   "message":("Montaj parțial: "+str(len(slots))+" sincronuri de verificat"
                              if slots else "Montaj complet verificat")})
    return result

def save_private_report(report,path):
    dest=Path(path)
    if report.get("schema")!=REPORT_SCHEMA:raise ValueError("Wrong report schema")
    dest.parent.mkdir(parents=True,exist_ok=True)
    temp=dest.with_name(dest.name+".tmp")
    try:
        temp.write_text(json.dumps(report,indent=2,ensure_ascii=False,
                         allow_nan=False),encoding="utf8")
        temp.replace(dest)
    finally:
        temp.unlink(missing_ok=True)
