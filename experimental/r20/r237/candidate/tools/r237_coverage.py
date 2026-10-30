"""Read-only editorial coverage gate for independent 02/03/04 Word plans.

R2.3.7 prevents silent omissions when older extraction recognizes only a
subset of a DOCX. Every timed editorial paragraph after AMB/PKG/VOX/SOT or
source markers must survive in universal audio segments. Every uppercase VO
paragraph must be represented in captions (after editorial section starts).
Word strike is honored for 02 if user selected omit-struck. No media writes.
"""
from __future__ import annotations
import re
from docx import Document
from r230_universal import paragraph_rows, clean, isupper, strip_tc, CODE, META

TC=re.compile(r'(?<!\d)\d{1,2}[:.]\d{2}(?!\d)')
WORD=re.compile(r'[^\W\d_]+',re.UNICODE)
HEADING=re.compile(r'^(?:AMB|AMBIAN[TȚ]Ă|PKG|SINCRON|SOT|VOX|SCRIPT)\b',re.I)
def norm(s):
    # Remove only clock tokens (not document prose and not 4-digit source IDs).
    return ' '.join(WORD.findall(TC.sub(' ',s).casefold()))
def eligible(docx):
    rows=paragraph_rows(Document(docx))
    started=False
    audio=[];graphics=[]
    for row in rows:
        s=row['text']
        if not s:continue
        if HEADING.match(s):
            started=True;continue
        if CODE.fullmatch(s):
            started=True;continue
        if not started:continue
        if row.get('table'):
            if TC.search(s) or (len(s.split())>=7 and row.get('bold')):
                audio.append(row)
            continue
        if META.match(s):continue
        if TC.match(s) and len(WORD.findall(TC.sub('',s)))>=5:
            audio.append(row)
        elif isupper(s) and len(WORD.findall(s))>=4:
            graphics.append(row)
    return audio,graphics

def verify(docx,parsed,omit_struck=False,module='02'):
    if module not in ('02','03','04'):raise ValueError('INVALID_EDITORIAL_MODULE')
    audio,graphics=eligible(docx)
    # For source dialogue compare on the exact DOCX paragraph idx; never
    # compare against an unrelated speaker's text or a cached plan.
    by_par={}
    for seg in parsed['segments']:
        i=seg['paragraph_start']
        txt=seg['text_without_strike'] if omit_struck else seg['text']
        by_par[i]=by_par.get(i,'')+' '+str(txt)
    missing_audio=[]
    for row in audio:
        expected=strip_tc(row.get('without_strike','') if omit_struck else row['text'])
        if not norm(expected):
            # An entirely struck CUT is deliberately excluded from V3.
            continue
        actual=by_par.get(row['idx'],'')
        if not actual or norm(expected) not in norm(actual):
            missing_audio.append(row['idx'])
    card_blob=norm(' '.join(c['text'] for c in parsed['captions']))
    missing_cards=[row['idx'] for row in graphics
                   if norm(row['text']) not in card_blob]
    # No selective omissions. Even for a subtitle-only run, keep VO coverage
    # checked: it identifies a structurally broken reader for this DOCX.
    if missing_audio or missing_cards:
        raise ValueError('EDITORIAL_COVERAGE_MISSING: declarații paragrafe %s; '
                         'cartoane paragrafe %s. Nu inserez materiale incomplete.' %
                         (missing_audio,missing_cards))
    return {'timedParagraphs':len(audio),'voParagraphs':len(graphics),
            'verifiedTimedParagraphs':len(audio)-len(missing_audio),
            'verifiedVoParagraphs':len(graphics)-len(missing_cards),
            'source':'UNIVERSAL_DOCX_COVERAGE_CHECK'}
