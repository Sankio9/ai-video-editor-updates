"""R2.0.7 — opt-in DOCX strikethrough removal for subtitle text ONLY.

Never modifies the DOCX or media; never touches Montage 01, NameTag 03, Cartoane 04.
Uses runs (including hyperlink runs), preserving whitespace, punctuation and italic
text. If a parsed dialogue cannot be mapped *unambiguously* back to formatted
DOCX characters, it fails closed rather than guessing which words were crossed out.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from docx import Document

def _is_struck(run, para):
    """Effective direct/style formatting; false overrides inherited true."""
    for font in (run.font, getattr(getattr(run,"style",None),"font",None),
                 getattr(getattr(para,"style",None),"font",None)):
        if font is None:
            continue
        strike=getattr(font,"strike",None)
        double=getattr(font,"double_strike",None)
        if strike is not None: return bool(strike)
        if double is not None:return bool(double)
    return False


def _run_pairs(paragraph):
    """Return (character, strike) pairs; refuse silently missed hyperlink text."""
    pairs=[]
    if hasattr(paragraph,"iter_inner_content"):
        for piece in paragraph.iter_inner_content():
            runs=piece.runs if hasattr(piece,"runs") else [piece]
            for run in runs:
                pairs.extend((char,_is_struck(run,paragraph)) for char in run.text)
    else:
        for run in paragraph.runs:
            pairs.extend((char,_is_struck(run,paragraph)) for char in run.text)
    if "".join(ch for ch,_ in pairs)!=paragraph.text:
        raise ValueError("DOCX text in hyperlink/field could not be mapped safely")
    return pairs


def _squash(pairs):
    """Whitespace-normalized text with per-character original strike provenance."""
    out=[];flags=[]
    for char,struck in pairs:
        if char.isspace():
            if out and out[-1]!=" ":
                out.append(" ");flags.append(False)
        else:
            out.append(char);flags.append(struck)
    if out and out[-1]==" ":
        out.pop();flags.pop()
    return "".join(out),flags


def _window(doc, first, last):
    if not isinstance(first,int) or not isinstance(last,int) or first<0 or last<=first or last>len(doc.paragraphs):
        raise ValueError("Invalid DOCX paragraph window")
    pairs=[]
    for para in doc.paragraphs[first:last]:
        if pairs:
            pairs.append((" ",False))
        pairs.extend(_run_pairs(para))
    return _squash(pairs)


def extract_strike_policy(docx, segments, omit_struck=False):
    """Return a list parallel to parser segments and transparent exclusion counts.

    segment 'text' is the authoritative editorial text. The original text is
    unchanged when option is off. When on, locate exact normalized text in its
    paragraph window (to the next segment header), and suppress only chars
    explicitly formatted as struck. If all dialogue was struck, omit the cue
    and record the CUT. No whole-word guessing.
    """
    if type(omit_struck) is not bool:
        raise ValueError("omit_struck must be explicit bool")
    if not isinstance(segments,list):
        raise ValueError("Invalid DOCX segments")
    if not omit_struck:
        return {"texts":[str(s["text"]) for s in segments],
                "cutIdsOmitted":[],"removedCharacters":0,"cutsChanged":0,
                "policy":"INCLUDE_STRUCK"}
    document=Document(str(docx))
    texts=[];all_omitted=[];removed=0;changed=0
    for i,seg in enumerate(segments):
        start=seg.get("paragraph_start")
        if not isinstance(start,int) or start<0 or start>=len(document.paragraphs):
            raise ValueError("CUT-%02d has invalid paragraph_start"%(i+1))
        next_start=(segments[i+1].get("paragraph_start")
                    if i+1<len(segments) else len(document.paragraphs))
        # A single paragraph may contain consecutive editorial headers/voices.
        if not isinstance(next_start,int) or next_start<start:
            raise ValueError("CUT-%02d has invalid paragraph ordering"%(i+1))
        end=max(start+1,next_start)
        if end>len(document.paragraphs):raise ValueError("Out-of-range DOCX paragraph")
        source,flags=_window(document,start,end)
        target=" ".join(str(seg["text"]).split())
        if not target:
            texts.append("");continue
        # If editorial text is repeated in a segment's source range with
        # different formatting, do not pick one at random.
        positions=[m.start() for m in re.finditer(re.escape(target),source)]
        if len(positions)!=1:
            raise ValueError("CUT-%02d: STRIKE_FORMAT_AMBIGUOUS (%d exact matches). "
                             "Cannot omit text safely."%(int(seg.get("ordinal",i+1)),len(positions)))
        offset=positions[0];region=source[offset:offset+len(target)]
        strike=flags[offset:offset+len(target)]
        remaining="".join(ch for ch,st in zip(region,strike) if not st)
        clean=" ".join(remaining.split())
        if region != clean:
            removed_chars=sum(1 for ch,st in zip(region,strike) if st and not ch.isspace())
            removed+=removed_chars
            if removed_chars:changed+=1
        if not clean:
            all_omitted.append("CUT-%02d"%int(seg.get("ordinal",i+1)))
        texts.append(clean)
    return {"texts":texts,"cutIdsOmitted":all_omitted,
            "removedCharacters":removed,"cutsChanged":changed,
            "policy":"OMIT_STRUCK"}
