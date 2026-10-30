"""R2.2.6: partial Montage R220 -> V3 subtitle plan, without pretending word-level sync.

No media writes or Premiere calls. All user scripts/data stay in local Temp.
Only CONFIRMED Montage CUTs may receive approximate inside-cut timing.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re, sys
from pathlib import Path

from r20_graphics_plans import build as independent_subtitles, _extract
from r171_layout import clean

SCHEMA="aive-r226-partial-subs-v1"
SHA_RE=re.compile(r"[a-f0-9]{64}\Z")
CUT_RE=re.compile(r"CUT-\d{1,4}\Z")

def sha(blob:bytes)->str:
    return hashlib.sha256(blob).hexdigest()

def read_json(path):
    value=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value,dict):raise ValueError("INVALID_JSON_OBJECT")
    return value

def require(cond,msg):
    if not cond:raise ValueError(msg)

def allocate(chunks,total):
    """Proportional read-only layout within an audio-confirmed source interval."""
    require(chunks and all(isinstance(s,str) and s.strip() for s in chunks),"EMPTY_SUBTITLE")
    n=len(chunks)
    require(math.isfinite(total) and .85*n<=total<=240,"CUT_TOO_SHORT_OR_LONG_FOR_SUBTITLES")
    weights=[max(1,len(s.strip())) for s in chunks]
    remaining=total-.85*n
    weights_total=sum(weights)
    values=[.85+remaining*w/weights_total for w in weights]
    require(all(.85-1e-6<=v<=18 for v in values),"SUBTITLE_DURATION_UNREADABLE")
    return values

def build(docx, montage_file, report_file, omit_struck=False):
    docx=Path(docx);montage_file=Path(montage_file);report_file=Path(report_file)
    require(docx.is_file() and docx.suffix.lower()==".docx","DOCX_INVALID")
    doc_sha=sha(docx.read_bytes())
    montage=read_json(montage_file);report=read_json(report_file)
    require(montage.get("schema")=="aive-r220-montage-plan-v1" and
            montage.get("phase")=="ANALYSIS_ONLY","MONTAGE_PLAN_INVALID")
    identity=montage.get("identity") or {}
    require(identity.get("docxSHA256")==doc_sha and SHA_RE.fullmatch(doc_sha),
            "MONTAGE_DOCX_CHANGED")
    require(isinstance(identity.get("sequenceId"),str) and len(identity["sequenceId"])>=3,
            "SEQUENCE_INVALID")
    require(SHA_RE.fullmatch(str(montage.get("planSHA256",""))) is not None,
            "MONTAGE_PLAN_SHA_INVALID")
    require(report.get("phase")=="POST_READBACK" and
            report.get("planSHA256")==montage["planSHA256"] and
            report.get("identity")==identity,"MONTAGE_READBACK_REQUIRED")
    cuts=montage.get("cuts")
    require(isinstance(cuts,list) and len(cuts)>0,"MONTAGE_EVENTS_MISSING")
    confirmed=[x for x in cuts if x.get("state")=="CONFIRMED"]
    placeholders=[x for x in cuts if x.get("state")=="PLACEHOLDER"]
    require(len(confirmed)==montage.get("confirmedCount")==
            report.get("confirmedInsertedCount") and
            len(placeholders)==montage.get("placeholderCount")==
            report.get("placeholderReservedCount"),
            "MONTAGE_READBACK_COUNTS_MISMATCH")
    require({x.get("cutId") for x in placeholders}==
            {x.get("cutId") for x in report.get("items",[])},
            "RESERVED_CUT_REPORT_MISMATCH")
    require(0<len(confirmed)<=2000 and len(confirmed)+len(placeholders)==montage.get("totalCuts"),
            "NO_CONFIRMED_OR_WRONG_COUNT")
    require(all(CUT_RE.fullmatch(str(x.get("cutId",""))) for x in confirmed+placeholders),
            "CUT_ID_INVALID")
    require(len({x["cutId"] for x in confirmed+placeholders})==len(confirmed)+len(placeholders),
            "DUPLICATE_CUT")

    source_plan=independent_subtitles(docx,"02",omit_struck=omit_struck)
    segments,_,_= _extract(docx)
    indexed={"CUT-%02d"%seg["ordinal"]:seg for seg in segments}
    require(len(indexed)==len(segments)==montage.get("totalCuts"),
            "DOCX_CUT_ORDINAL_MISMATCH")
    by_group={}
    for item in source_plan["items"]:
        by_group.setdefault(item["groupId"],[]).append(item)
    included=[];seen=set();layout=[];cursor=0;durationReview=[]
    for m in cuts:
        if m["state"]=="VO_RESERVE":continue
        cut=m["cutId"]
        require(cut in indexed,"DOCX_CUT_MISSING "+cut)
        seg=indexed[cut]
        require(str(seg.get("source_code"))==str(m.get("sourceCode")),
                "DOCX_SOURCE_CODE_MISMATCH "+cut)
        if m["state"]=="PLACEHOLDER":continue
        require(m["state"]=="CONFIRMED","UNKNOWN_CUT_STATE "+cut)
        st=m.get("timelineStart");ed=m.get("timelineEnd")
        require(all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
                    for x in (st,ed)) and 0<=st<ed,"INVALID_CONFIRMED_INTERVAL "+cut)
        require(m.get("sourceName") and m.get("sourceNodeId"),"CONFIRMED_SOURCE_ID_MISSING "+cut)
        group=by_group.get(cut,[])
        if not group:
            require(cut in source_plan.get("omittedStrikeCuts",[]),
                    "CONFIRMED_CUT_HAS_NO_DOCX_TEXT "+cut)
            continue
        text=clean(" ".join(x["text"] for x in group))
        require(text and len(text)<=15000,"SUBTITLE_TEXT_INVALID "+cut)
        # Reuse validated R2.1.2 readable layout and strikethrough policy.
        try:
            durations=allocate([v["text"] for v in group],ed-st)
        except ValueError as allocation_problem:
            # A short verified clip cannot safely display a long script at
            # acceptable reading speed. Do not block valid other CUTs.
            # Never shift these captions outside their confirmed V1/A1 clip.
            if str(allocation_problem) not in ("SUBTITLE_DURATION_UNREADABLE",
                        "CUT_TOO_SHORT_OR_LONG_FOR_SUBTITLES"):
                raise
            durationReview.append({"cutId":cut,
                "sourceCode":m["sourceCode"],"reason":str(allocation_problem),
                "intervalSeconds":round(ed-st,3),"subtitleParts":len(group),
                "action":"REVIEW_DURATION_ON_CONFIRMED_CUT"})
            continue
        progress=st
        for j,(item,duration) in enumerate(zip(group,durations)):
            finish=ed if j==len(group)-1 else progress+duration
            require(finish>progress and finish<=ed+.01,"TIMING_RANGE_INVALID "+cut)
            layout.append({"id":"R226-%04d"%(len(layout)+1),"groupId":cut,
                    "sourceCode":m["sourceCode"],"text":item["text"],
                    "fontStyle":item.get("fontStyle","Regular"),
                    "startSeconds":round(progress,4),"durationSeconds":round(finish-progress,4),
                    "timingKind":"CUT_ALIGNED_ESTIMATED"})
            progress=finish
        included.append(cut);seen.add(cut)
    require(layout and len(layout)<=2000,"NO_ELIGIBLE_SUBTITLES")
    require(all(1<=len(x["text"])<=74 for x in layout),"CAPTION_LIMIT_FAILED")
    require(all(layout[i]["startSeconds"]>=layout[i-1]["startSeconds"] for i in range(1,len(layout))),
            "SUBTITLE_ORDER_CHANGED")
    # No subtitles for any UNCERTAIN audio. This includes source 9974.
    require(not any(x["groupId"] in {r["cutId"] for r in placeholders} for x in layout),
            "UNCONFIRMED_CUT_MUST_NOT_RECEIVE_SUBTITLE")
    result={"schema":SCHEMA,"module":"02","mode":"montage_partial",
            "timing":"CUT_ALIGNED_ESTIMATED","docx_sha256":doc_sha,
            "montagePlanSHA256":montage["planSHA256"],
            "sequenceId":identity["sequenceId"],"sourceDocx":docx.name,
            "confirmedCount":len(confirmed),"reservedCount":len(placeholders),
            "confirmedCuts":[{"cutId":x["cutId"],"sourceCode":x["sourceCode"],
                "sourceName":x["sourceName"],"sourceNodeId":x["sourceNodeId"],
                "timelineStart":x["timelineStart"],"timelineEnd":x["timelineEnd"]}
                for x in confirmed],
            "reservedCuts":[{"cutId":x["cutId"],"sourceCode":x["sourceCode"],
                "timelineStart":x["timelineStart"],"timelineEnd":x["timelineEnd"]}
                for x in placeholders],
            "omittedStrikeCuts":source_plan.get("omittedStrikeCuts",[]),
            "strikeCutsChanged":source_plan.get("strikeCutsChanged",0),
            "removedStrikeCharacters":source_plan.get("removedStrikeCharacters",0),
            "items":layout,"totalItems":len(layout),"subtitledCuts":included,
             "durationReview":durationReview}
    # Unique SHA for each plan, retained on disk and checked by CEP.
    result["contentSHA256"]=sha(json.dumps(result,ensure_ascii=False,sort_keys=True,
                                  separators=(",",":")).encode("utf-8"))
    return result

def save(plan,out):
    out=Path(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_name(out.name+".tmp")
    try:
        tmp.write_text(json.dumps(plan,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
        tmp.replace(out)
    finally:tmp.unlink(missing_ok=True)
    return sha(out.read_bytes())

def main():
    ap=argparse.ArgumentParser()
    for name in ("docx","montage","report","output"):
        ap.add_argument("--"+name,required=True)
    ap.add_argument("--omit-struck",action="store_true")
    a=ap.parse_args()
    try:
        p=build(a.docx,a.montage,a.report,a.omit_struck)
        digest=save(p,a.output)
        print(json.dumps({"ok":True,"plan":str(Path(a.output)),"fileSHA256":digest,
            "docxSHA256":p["docx_sha256"],"sequenceId":p["sequenceId"],
            "montagePlanSHA256":p["montagePlanSHA256"],"items":p["totalItems"],
            "subtitledCuts":len(p["subtitledCuts"]),
            "reservedCuts":p["reservedCount"],"timing":p["timing"],
            "durationReview":p["durationReview"],
            "skippedConfirmed":len(p["durationReview"])},ensure_ascii=True))
    except Exception as e:
        print(json.dumps({"ok":False,"message":str(e)},ensure_ascii=True))
        return 2
    return 0
if __name__=="__main__":raise SystemExit(main())
