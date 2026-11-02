"""R245 NameTag independent audit, no fabricated people or functions.

Both layouts are accepted:
  7967 / VASILE / beneficiar / 00.10 ...
  SINCRON: ABDULLAH AL MAMUNM, muncitor în construcții
  8170 / 00.44–00.56 / speech
Also supports those lines embedded in one Word paragraph.
"""
from __future__ import annotations
from collections import Counter
import re
from docx import Document
from r230_universal import split_identity, clean, CODE
SYNC=re.compile(r'^SINCRON\s*[:–-]?\s*(.*)$',re.I)
def name_role(s):
    s=clean(s)
    if ',' in s:
        left,right=s.split(',',1)
        ident=split_identity(left)
        if ident and right.strip() and len(right)<116:
            return left.strip(),clean(right)
    return None
def normalized(a,b):
    return clean(a).casefold(),clean(b).casefold()
def check(docx,plan):
    lines=[]
    for p in Document(docx).paragraphs:
        lines.extend([clean(x) for x in p.text.splitlines() if clean(x)])
    for table in Document(docx).tables:
        for row in table.rows:
            for cell in row.cells:
                lines.extend([clean(x) for x in cell.text.splitlines() if clean(x)])
    anchors=[];source_codes=[];used=set()
    for i,s in enumerate(lines):
        m=SYNC.match(s)
        if m:
            pair=name_role(m.group(1))
            if pair and i not in used:
                anchors.append((pair[0],pair[1],i))
                used.add(i)
        if not CODE.fullmatch(s):continue
        source_codes.append(s)
        if i+2>=len(lines):continue
        a,b=lines[i+1],lines[i+2]
        n=split_identity(a)
        # Never infer a role from spoken text or uppercase narration.
        valid_role=(b and 1<=len(b.split())<=16 and len(b)<115 and
          not b.endswith(('.', '!', '?')) and not CODE.fullmatch(b) and
          not b.isupper() and not re.search(r'\d{1,2}[:.]\d{2}',b))
        if n and not n[1] and valid_role and i+1 not in used:
            anchors.append((a,b,i+1))
            used.add(i+1)
    if not anchors:raise ValueError('NAMETAG_REVIEW_NO_VERIFIED_DOCX_ANCHORS')
    emitted=plan.get('items') or []
    if not emitted:raise ValueError('NAMETAG_REVIEW_NO_VERIFIED_BURTIERE')
    allowed=Counter(normalized(a,b) for a,b,_ in anchors)
    requested=Counter(normalized(str(x.get('name','')),str(x.get('title','')))
                      for x in emitted)
    mismatches=[(a,b,need,allowed.get((a,b),0))
                for (a,b),need in requested.items() if need>allowed.get((a,b),0)]
    if mismatches:
        raise ValueError('NAMETAG_REVIEW_IDENTITY_MISMATCH: %s'%mismatches[:5])
    if len(emitted)>200:raise ValueError('NAMETAG_REVIEW_TOO_MANY')
    return {'verified':len(emitted),'explicitAnchors':len(anchors),
            'distinctPersons':len(set(normalized(a,b)[0] for a,b,_ in anchors)),
            'sourceCodes':sorted(set(source_codes))}
