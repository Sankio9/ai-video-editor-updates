"""R2.1.3 — CONSERVATIVE second search on original ASR words for Montage 01.

This module is a local, deterministic second candidate matcher. It does NOT
rerun Whisper, lower any existing acceptance threshold, use raw reporter
timecodes as cut boundaries, generate audio, or touch Premiere.
Only a unique, nearly verbatim spoken passage with exact beginning AND end
anchors may be proposed; R1.9.13's existing safety and write gate still run.
"""
from __future__ import annotations

from difflib import SequenceMatcher
import math
import re
import unicodedata

MATCHER_VERSION="r213-unique-full-phrase-anchor-v1"
MIN_QUERY_WORDS=7
MIN_FULL_SCORE=.88
MAX_TC_DRIFT_SECONDS=75.
SEARCH_RADIUS=90.
MAX_UNTIMED_SECONDS=480.
MAX_WORDS=16000
MAX_SPAN_WORDS=240

def norm(text):
    """Permit punctuation and RO diacritic variants, never paraphrase text."""
    raw=unicodedata.normalize("NFKD",str(text or ""))
    raw="".join(ch for ch in raw if not unicodedata.combining(ch))
    raw=raw.replace("ș","s").replace("ş","s").replace("ț","t").replace("ţ","t")
    raw=raw.replace("Ș","S").replace("Ţ","T").replace("ț","t")
    return re.findall(r"[a-z0-9]+",raw.lower())

def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)

def _flatten(words,offset):
    flat=[]
    for w in words:
        if not isinstance(w,dict):raise ValueError("ASR_INVALID_WORD")
        start,end=w.get("start"),w.get("end")
        if not finite(start) or not finite(end) or start<0 or end<start:
            raise ValueError("ASR_INVALID_TIME")
        bits=norm(w.get("word") or w.get("text") or w.get("norm") or "")
        if len(bits)>8:raise ValueError("ASR_UNTRUSTED_WORD")
        for bit in bits:
            flat.append((bit,round(start+offset,3),round(end+offset,3)))
            if len(flat)>MAX_WORDS:raise ValueError("ASR_TOO_LARGE")
    return flat

def recover(ev,words,original,time_offset=0.,max_search_s=SEARCH_RADIUS):
    """Return original on uncertainty. Return enhanced proposal only if unique.

    The caller MUST still use the unchanged R1.9.13 r143_build.is_safe and
    r1911_speech_first.validate_speech_only before generating the plan.
    """
    if not isinstance(original,dict):return original
    state=original.get("status")
    if state not in ("REVIEW_WEAK_BOUNDARY","REVIEW_WEAK_TRANSCRIPT",
                     "REVIEW_NO_MATCH","REVIEW_LARGE_SHIFT",
                     "REVIEW_OUTSIDE_SEARCH_RADIUS"):
        return original
    if not finite(time_offset):return original
    if ev.get("timecodeHint"):
        # Untimed recovery is a separate independently certified algorithm.
        return original
    if not isinstance(words,(list,tuple)):return original
    query=norm(ev.get("text"))
    if not MIN_QUERY_WORDS<=len(query)<=MAX_SPAN_WORDS:return original
    try:asr=_flatten(words,time_offset)
    except ValueError:return original
    if len(asr)<len(query)-1:return original
    clock=ev.get("inSeconds")
    if not finite(clock):return original
    radius=min(SEARCH_RADIUS,float(max_search_s))
    if not finite(radius) or radius<=0:return original
    # TC guides only WHICH ASR words are searched, never resulting IN/OUT.
    start_hint=max(0.,clock-radius)
    stop_hint=clock+radius
    spans=[]
    tokens=[a[0] for a in asr]
    anchor=tuple(query[:2])
    tail=tuple(query[-2:])
    minimum=max(5,int(len(query)*.78))
    maximum=min(MAX_SPAN_WORDS,int(len(query)*1.24)+1)
    for i in range(len(tokens)-1):
        if tuple(tokens[i:i+2])!=anchor:continue
        if not start_hint<=asr[i][1]<=stop_hint:continue
        for end in range(i+minimum,min(len(tokens),i+maximum)+1):
            if tuple(tokens[end-2:end])!=tail:continue
            if asr[end-1][2]<=asr[i][1]:continue
            heard=tokens[i:end]
            score=SequenceMatcher(None,query,heard,autojunk=False).ratio()
            if score<MIN_FULL_SCORE:continue
            start,endtime=asr[i][1],asr[end-1][2]
            # Confirm both endpoints are plausible speech, not a fabricated
            # timecode interval. A >75s reporter shift cannot be auto-accepted.
            drift=max(abs(start-clock),abs(endtime-float(ev.get("outSeconds",endtime))))
            if drift>MAX_TC_DRIFT_SECONDS:continue
            spans.append((score,start,endtime,i,end))
    if not spans:return original
    spans.sort(key=lambda item:(-item[0],item[1]))
    best=spans[0]
    for alternative in spans[1:]:
        if alternative[0]>=best[0]-.045 and (
            abs(alternative[1]-best[1])>5. or abs(alternative[2]-best[2])>5.
        ):
            # Ambiguous repeated speech: never promote by TC proximity.
            copy=original.copy()
            copy["status"]="REVIEW_ALTERNATIVE_OCCURRENCE"
            copy["reason"]="Declarație repetată în ASR; nu aleg automat o apariție."
            return copy
    score,start,endtime,_,_=best
    proposal=original.copy()
    proposal.update({
        "proposedIn":start,
        "proposedOut":endtime,
        "rawMatchedIn":start,
        "rawMatchedOut":endtime,
        "startScore":1.0,
        "endScore":1.0,
        "fullTextScore":round(score,4),
        "score":round(.64+.36*score,4),
        "driftSeconds":round(max(abs(start-clock),
                abs(endtime-float(ev.get("outSeconds",endtime)))),3),
        "status":"REVIEW_SUGGESTED",
        "reason":"A doua căutare: text ASR integral cu început/sfârșit confirmat, unic.",
        "matchMethod":MATCHER_VERSION,
        "searchRadiusSeconds":radius,
    })
    return proposal
