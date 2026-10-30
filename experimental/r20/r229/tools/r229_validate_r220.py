"""R2.2.9 read-only R220 plan validation and safe recovery report template.

Purpose: the original ANALYSIS_ONLY .report.json may be stale after the R220
post-readback persistence failure. Never trust that sidecar for authorization.
Strictly recompute the source plan SHA using the ORIGINAL R220 Python digest;
the CEP must still verify each actual Premiere V1/A1 clip + marker before
persisiting the template as POST_READBACK. No media, Timeline or JSON writes.
"""
from __future__ import annotations
import argparse,hashlib,json,math,re,sys
from pathlib import Path
from r220_montage_plan import SCHEMA,REPORT_SCHEMA,digest

SHA=re.compile(r"[0-9a-f]{64}\Z")
CUT=re.compile(r"CUT-[0-9]{1,4}\Z")
VO=re.compile(r"VO-[0-9]{1,4}\Z")
SOURCE=re.compile(r"[0-9]{4}\Z")
def valid(cond,message):
    if not cond:raise ValueError(message)
def finite(x):
    return isinstance(x,(float,int)) and not isinstance(x,bool) and math.isfinite(x)
def validate(docx,planfile,sequence):
    docx=Path(docx);planfile=Path(planfile)
    valid(docx.is_file() and docx.suffix.lower()==".docx","DOCX_NOT_FOUND")
    valid(planfile.is_file(),"R220_PLAN_NOT_FOUND")
    bytes_plan=planfile.read_bytes()
    valid(100<len(bytes_plan)<10_000_000,"R220_PLAN_SIZE_INVALID")
    plan=json.loads(bytes_plan.decode("utf-8-sig"))
    valid(isinstance(plan,dict) and plan.get("schema")==SCHEMA and
        plan.get("phase")=="ANALYSIS_ONLY","R220_PLAN_SCHEMA_INVALID")
    original=plan.get("planSHA256")
    valid(isinstance(original,str) and SHA.fullmatch(original),"R220_SHA_MISSING")
    computed=digest({key:value for key,value in plan.items() if key!="planSHA256"})
    valid(computed==original,"R220_PLAN_SHA_CHANGED")
    ident=plan.get("identity") or {}
    valid(isinstance(ident,dict) and isinstance(sequence,str) and
        3<=len(sequence)<=128 and ident.get("sequenceId")==sequence,
        "R220_SEQUENCE_CHANGED")
    doc_sha=hashlib.sha256(docx.read_bytes()).hexdigest()
    valid(ident.get("docxSHA256")==doc_sha,"R220_DOCX_CHANGED")
    valid(isinstance(ident.get("diagnosticSHA256"),str) and
        SHA.fullmatch(ident["diagnosticSHA256"]),"R220_DIAGNOSTIC_SHA_MISSING")
    cuts=plan.get("cuts")
    valid(isinstance(cuts,list) and 0<len(cuts)<=2500,"R220_NO_EVENTS")
    seen=set();matched=[];reserved=[];voice=[];last_end=0.
    for i,c in enumerate(cuts):
        valid(isinstance(c,dict),"R220_INVALID_ROW")
        cid=c.get("cutId");state=c.get("state")
        valid(isinstance(cid,str) and cid not in seen and
            ((CUT.fullmatch(cid) and state in ("CONFIRMED","PLACEHOLDER")) or
             (VO.fullmatch(cid) and state=="VO_RESERVE")),
            "R220_CUT_ID_OR_STATE_INVALID_"+str(i))
        seen.add(cid)
        start,end=c.get("timelineStart"),c.get("timelineEnd")
        valid(finite(start) and finite(end) and
            0<=start<end<=36000 and start>=last_end-0.001,
            "R220_RANGE_INVALID_"+cid)
        last_end=end
        if state=="VO_RESERVE":
            valid(c.get("sourceIn") is None and c.get("sourceOut") is None,
                  "R220_VO_SOURCE_BOUNDS_"+cid)
            voice.append(c)
            continue
        valid(isinstance(c.get("sourceCode"),str) and SOURCE.fullmatch(c["sourceCode"]),
              "R220_SOURCE_CODE_INVALID_"+cid)
        if state=="CONFIRMED":
            a,b=c.get("sourceIn"),c.get("sourceOut")
            valid(isinstance(c.get("sourceName"),str) and c["sourceName"].strip() and
                isinstance(c.get("sourceNodeId"),str) and c["sourceNodeId"].strip() and
                finite(a) and finite(b) and 0<=a<b<=36000 and
                abs((b-a)-(end-start))<=0.1,
                "R220_CONFIRMED_SOURCE_INVALID_"+cid)
            matched.append(c)
        else:
            valid("sourceIn" not in c and "sourceOut" not in c and
                c.get("estimated") is True and isinstance(c.get("reason"),str),
                "R220_PLACEHOLDER_INVALID_"+cid)
            reserved.append(c)
    valid(len(matched)==plan.get("confirmedCount") and
          len(reserved)==plan.get("placeholderCount") and
          len(matched)+len(reserved)==plan.get("totalCuts") and
          len(voice)==plan.get("voReserveCount",0),
          "R220_COUNTS_INVALID")
    valid(0<len(matched)<=2000,"R220_NO_CONFIRMED_AUDIO")
    report={"schema":REPORT_SCHEMA,"phase":"ANALYSIS_ONLY","identity":ident,
            "planSHA256":original,"confirmedPlannedCount":len(matched),
            "placeholderPlannedCount":len(reserved),"voReserveCount":len(voice),
            "missingDistinctSourceCodes":sorted({x["sourceCode"] for x in reserved
                if x.get("reason") in ("SOURCE_NOT_FOUND","SOURCE_OFFLINE")}),
            "items":reserved}
    return {"ok":True,"plan":str(planfile),"planFileSHA256":hashlib.sha256(bytes_plan).hexdigest(),
        "planSHA256":original,"docxSHA256":doc_sha,"sequenceId":sequence,
        "confirmedCount":len(matched),"placeholderCount":len(reserved),
        "voReserveCount":len(voice),"reportTemplate":report}

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--docx",required=True)
    ap.add_argument("--plan",required=True)
    ap.add_argument("--sequence-id",required=True)
    a=ap.parse_args(argv)
    try:
        result=validate(a.docx,a.plan,a.sequence_id)
        print("AIVE_R229_RESULT "+json.dumps(result,ensure_ascii=True,allow_nan=False),flush=True)
        return 0
    except Exception as exc:
        print("AIVE_R229_RESULT "+json.dumps({"ok":False,"message":str(exc)},ensure_ascii=True),
              flush=True)
        return 2
if __name__=="__main__":sys.exit(main())
