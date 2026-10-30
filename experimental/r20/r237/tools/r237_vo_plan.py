"""R237 independent VO graphics aligned to READBACK-verified R220 montage VO reserves.

This is a read-only plan generator. Existing audio placeholder CUTs are not a
prerequisite for VO graphics; never use interview timecodes as fallback.
DO NOT call Premiere from Python. Requires existing R220 plan and report.
"""
from __future__ import annotations
from collections import OrderedDict
from pathlib import Path
from math import isfinite
import hashlib,json
from r20_graphics_plans import build as editorial_plan
from r20_graphics_plans import SCHEMA as GRAPH_SCHEMA
from r171_layout import clean
import r204_carton_layout as carton

SCHEMA="aive-r237-vo-montage-v1"
HARD_CHARS=28
MAX_LINES=4

def require(ok,reason):
    if not ok:raise ValueError(reason)

def load(path):
    with Path(path).open(encoding="utf8") as f:return json.load(f)

def _digest(plan):
    from r220_montage_plan import digest
    return digest({k:v for k,v in plan.items() if k!='planSHA256'})

def validate(docx,montage,report):
    path=Path(docx)
    require(path.is_file() and path.suffix.lower()==".docx","R237_DOCX_NOT_FOUND")
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    require(isinstance(montage,dict) and montage.get("schema")=="aive-r220-montage-plan-v1" and
            montage.get("phase")=="ANALYSIS_ONLY","R237_INVALID_R220_PLAN")
    identity=montage.get("identity") or {}
    require(identity.get("docxSHA256")==digest and
            isinstance(identity.get("sequenceId"),str) and len(identity["sequenceId"])>=3,
            "R237_DOCX_OR_SEQUENCE_MISMATCH")
    require(isinstance(montage.get("planSHA256"),str) and
            montage["planSHA256"]==_digest(montage),"R237_PLAN_SHA_MISMATCH")
    cuts=montage.get("cuts") or []
    require(len(cuts)>0 and len(cuts)<=2500,"R237_PLAN_EVENTS_INVALID")
    require(isinstance(report,dict) and
            report.get("phase")=="POST_READBACK" and
            report.get("identity")==identity and
            report.get("planSHA256")==montage["planSHA256"],
            "R237_MONTAGE_READBACK_REQUIRED")
    confirmed=[c for c in cuts if c.get("state")=="CONFIRMED"]
    reserved=[c for c in cuts if c.get("state")=="PLACEHOLDER"]
    vo=[c for c in cuts if c.get("state")=="VO_RESERVE"]
    require(len(confirmed)==montage.get("confirmedCount")==report.get("confirmedInsertedCount"),
            "R237_CONFIRMED_AUDIO_COUNT_CHANGED")
    require(len(reserved)==montage.get("placeholderCount")==report.get("placeholderReservedCount"),
            "R237_PLACEHOLDER_COUNT_CHANGED")
    require(len(vo)==montage.get("voReserveCount") and len(vo)>=1,"R237_VO_RESERVATIONS_MISSING")
    require(len(vo)+len(confirmed)+len(reserved)==len(cuts),"R237_UNKNOWN_CUT_STATES")
    require(len({c.get("cutId") for c in cuts})==len(cuts),"R237_DUPLICATE_IDS")
    last=-1.
    for row in cuts:
        a,b=row.get("timelineStart"),row.get("timelineEnd")
        require(all(isinstance(v,(float,int)) and not isinstance(v,bool) and
                    isfinite(v) for v in (a,b)) and
                a>=0 and b>a and a>=last-0.01,"R237_INVALID_TIMELINE_INTERVAL")
        last=b
    for row in vo:
        require(str(row.get("cutId","")).startswith("VO-") and
                row.get("estimated") is True and
                row.get("sourceIn") is None and row.get("sourceOut") is None,
                "R237_NON_EDITORIAL_VO_SLOT")
    return digest,identity,vo

def _page(text):
    """Use already approved semantic accents with a stricter 9:16 wrap.
    This function runs in a new Python process and never changes the
    installed Independent V5 generator.
    """
    previous=carton.HARD_MAX
    try:
        carton.HARD_MAX=HARD_CHARS
        selected,spans=carton.semantic_emphasis(text)
        lines=carton.compact_lines(text,selected)
    finally:
        carton.HARD_MAX=previous
    assert len(lines)==MAX_LINES
    require(all(len(l)<=HARD_CHARS for l in lines),"R237_VERTICAL_LINE_OVERFLOW")
    tokens=text.split()
    word=0
    bold={str(i):"" for i in range(MAX_LINES)}
    for i,line in enumerate(lines):
        pieces=line.split()
        bold[str(i)]=" ".join(str(n+1) for n in range(len(pieces)) if word+n in selected)
        word+=len(pieces)
    require(word==len(tokens) and clean(" ".join(lines))==text,"R237_PAGE_TEXT_LOST")
    return {"text":text,"physicalLines":lines,"boldWords":bold,"emphasisPhrases":spans}

def split_pages(text):
    source=clean(text)
    require(source,"R237_EMPTY_CARD")
    words=source.split()
    require(all(len(w)<=HARD_CHARS for w in words),"R237_WORD_TOO_LONG_FOR_VERTICAL")
    pages=[];i=0
    while i<len(words):
        lo=i+1;hi=len(words);best=None
        # Greedy largest complete-word page that fits FOUR 28-char lines.
        while lo<=hi:
            mid=(lo+hi)//2
            candidate=" ".join(words[i:mid])
            try:page=_page(candidate)
            except ValueError:hi=mid-1
            else:best=(mid,page);lo=mid+1
        require(best is not None,"R237_CANNOT_FIT_VERTICAL_PAGE")
        pages.append(best[1]);i=best[0]
    require(clean(" ".join(p["text"] for p in pages))==source,"R237_CARD_TEXT_LOSS")
    return pages

def build(docx,montage_path,report_path):
    montage=load(montage_path);report=load(report_path)
    digest,identity,reserves=validate(docx,montage,report)
    plan=editorial_plan(Path(docx),"04")
    require(plan.get("schema")==GRAPH_SCHEMA and plan.get("module")=="04" and
            plan.get("docx_sha256")==digest,"R237_EDITORIAL_PLAN_INVALID")
    by_group=OrderedDict()
    for item in plan.get("items",[]):
        key=item.get("groupId")
        require(isinstance(key,str) and key.startswith("VO-"),"R237_EDITORIAL_GROUP_INVALID")
        by_group.setdefault(key,[]).append(item.get("text",""))
    require(len(by_group)==len(reserves),"R237_VO_BLOCKS_NOT_ALIGNED: %s în DOCX / %s spații VO în montaj" %
           (len(by_group),len(reserves)))
    items=[]
    for slot,(group,pieces) in zip(reserves,by_group.items()):
        whole=clean(" ".join(pieces))
        pages=split_pages(whole)
        length=slot["timelineEnd"]-slot["timelineStart"]
        each=length/len(pages)
        require(.8<=each<=15,"R237_VO_DURATION_REVIEW "+str(slot["cutId"]))
        for number,page in enumerate(pages):
            st=round(slot["timelineStart"]+each*number,4)
            end=round(slot["timelineEnd"],4) if number==len(pages)-1 else round(slot["timelineStart"]+each*(number+1),4)
            require(end-st>=.8-0.001,"R237_VO_DURATION_TOO_SHORT")
            items.append({"id":"R237-%04d"% (len(items)+1),"groupId":slot["cutId"],
                "text":page["text"],"physicalLines":page["physicalLines"],
                "textLine0":page["physicalLines"][0],
                "textLines123":'\r'.join(page["physicalLines"][1:]),
                "boldWords":page["boldWords"],"emphasisPhrases":page["emphasisPhrases"],
                "colorScheme":"Orange","sourceParagraph":None,
                "startSeconds":st,"durationSeconds":round(end-st,4),
                "timingKind":"VO_RESERVE_ESTIMATED","page":number+1,
                "pageCount":len(pages)})
    require(items and len(items)<=2000,"R237_NO_VO_CARDS")
    return {"schema":GRAPH_SCHEMA,"r237Schema":SCHEMA,
        "mode":"montage_vo","module":"04","timing":"VO_RESERVE_ESTIMATED",
        "docx_sha256":digest,"montagePlanSHA256":montage["planSHA256"],
        "sequenceId":identity["sequenceId"],"sourceDocx":Path(docx).name,
        "totalItems":len(items),"items":items,
        "totalVO":len(reserves),"confirmedCUTs":len([x for x in montage["cuts"] if x["state"]=="CONFIRMED"]),
        "reservedCUTs":len([x for x in montage["cuts"] if x["state"]=="PLACEHOLDER"]),
        "limits":{"charactersPerLine":HARD_CHARS,"lines":MAX_LINES},
        "editorialWarning":"timpi estimați din spațiile VO confirmate în plan, nu sincron audio ASR"}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--docx",required=True);p.add_argument("--montage",required=True)
    p.add_argument("--report",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        plan=build(a.docx,a.montage,a.report)
        dst=Path(a.output);dst.parent.mkdir(parents=True,exist_ok=True)
        temp=dst.with_suffix(".tmp")
        temp.write_text(json.dumps(plan,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf8")
        temp.replace(dst)
        print(json.dumps({"ok":True,"path":str(dst),
            "sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),
            "docxSHA256":plan["docx_sha256"],"sequenceId":plan["sequenceId"],
            "montagePlanSHA256":plan["montagePlanSHA256"],
            "items":plan["totalItems"],"voReserves":plan["totalVO"]},ensure_ascii=True))
    except Exception as e:
        print(json.dumps({"ok":False,"message":str(e)},ensure_ascii=True))
        return 2
    return 0
if __name__=="__main__":raise SystemExit(main())
