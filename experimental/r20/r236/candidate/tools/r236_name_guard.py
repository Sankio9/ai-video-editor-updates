"""R236: resolve false NameTag legacy source-code mismatch ONLY against
explicit DOCX name, function and nearby four-digit source markers.

This is a read-only editorial source verification. Do NOT reinterpret media
source identity or infer speakers from audio; do NOT mask real contradictions.
"""
from __future__ import annotations
from collections import Counter
import re
from pathlib import Path
from docx import Document
CODE=re.compile(r"^[0-9]{4}$")

def check(docx,plan):
    docx=Path(docx)
    p=[x.text.strip() for x in Document(docx).paragraphs]
    anchors=[]
    for i,s in enumerate(p):
        if not CODE.fullmatch(s):continue
        code=s
        remaining=[(j,p[j]) for j in range(i+1,min(i+5,len(p))) if p[j]]
        if len(remaining)<2:continue
        j,name=remaining[0]
        k,role=remaining[1]
        if (j!=i+1 or k!=i+2 or not (2<=len(name.split())<=4) or
             not name[0].isupper() or any(c.isdigit() for c in name) or
             not role or len(role)>95 or CODE.fullmatch(role) or
             re.search(r"[.!?]$",role)):
            continue
        # Names and roles must be the exact visible DOCX text; never infer.
        anchors.append((name,role,code))
    if not anchors:raise ValueError("NAMETAG_REVIEW_NO_VERIFIED_DOCX_ANCHORS")
    content=plan.get("items") or []
    if not content:raise ValueError("NAMETAG_REVIEW_NO_VERIFIED_BURTIERE")
    valid=Counter((a,b) for a,b,c in anchors)
    emitted=Counter((str(x.get("name","")).strip(),
                     str(x.get("title","")).strip()) for x in content)
    if not all(valid.get(pair,0)>=count for pair,count in emitted.items()):
        raise ValueError("NAMETAG_REVIEW_IDENTITY_MISMATCH")
    if len(content)>len(anchors) or len(content)>200:
        raise ValueError("NAMETAG_REVIEW_DUPLICATE_OR_TOO_MANY")
    return {"verified":len(content),"explicitAnchors":len(anchors),
            "distinctPersons":len(set(a for a,b,c in anchors)),
            "sourceCodes":sorted(set(c for a,b,c in anchors))}
