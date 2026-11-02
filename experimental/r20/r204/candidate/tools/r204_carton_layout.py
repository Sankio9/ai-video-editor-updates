"""R2.0.4 candidate: deterministic editorial carton layout & semantic accents.

Additive module: NEVER rewrites script text, never changes MOGRTs or montage.
Bold Words are 1-based indices, scoped to physical MOGRT lines 0..3.
No cloud/ASR. Emphasis is a *suggestion* based on script text, not editorial fact.
"""
from __future__ import annotations

from functools import lru_cache
import math
import re
import unicodedata

from r171_layout import clean, split_cards

HARD_MAX = 33
MAX_LINES = 4
# A small generic vocabulary, not report-specific editorial truth.
TOPIC_PREFIXES = (
    'invatamant', 'educat', 'scoal', 'elev', 'student', 'profes', 'meser',
    'calific', 'locur', 'munc', 'salari', 'buget', 'investit', 'euro',
    'milion', 'miliard', 'procent', 'comun', 'primar', 'localit',
    'spital', 'medic', 'pacient', 'transport', 'energie', 'reforma',
    'dezvolt', 'proiect', 'rezultat', 'program', 'benefici', 'cost',
    'tiner', 'famil', 'finant', 'sigurant', 'infrastruct', 'agricult',
)
STOPWORDS = frozenset(('si cu in din de la pentru ca care un o au va vor a ale al sa dar pe iar ce'
                       ' este sunt prin spre cat catre doi doua unui unei dintre peste sub mai tot'
                       ' aceasta acest aceste acesti asa astfel despre doar dupa dintre').split())
CONNECTORS = STOPWORDS | frozenset(('le lor ai se isi ori intre fara pana fata intr pentru').split())
NUMERIC = re.compile(r'(?<!\w)(?:[€$£]?\d[\d.,]*\s?[%‰]?|\d+[–-]\d+)(?!\w)')


def _norm(word):
    x = unicodedata.normalize('NFKD', word.replace('ș','s').replace('Ș','S').replace('ț','t').replace('Ț','T'))
    return ''.join(c for c in x if not unicodedata.combining(c) and (c.isalnum() or c in '-%')).casefold()


def _key(word):
    x=_norm(word)
    return any(x.startswith(y) for y in TOPIC_PREFIXES)


def _candidate_spans(words):
    """(priority,start,end,reason), end exclusive; no paraphrasing or AI guesses."""
    normalized=[_norm(w) for w in words]
    spans=[]
    for i, w in enumerate(words):
        nw=normalized[i]
        if any(ch.isdigit() for ch in w) and NUMERIC.search(w):
            end=i+1
            if end<len(words) and words[end] in ('%', '‰'):
                end+=1
            # Preserve a compact number + unit phrase: '250 de elevi', '15 milioane de lei'.
            tail=normalized[end:end+3]
            if len(tail)>=2 and tail[0] in ('de', 'din', 'la') and (
                    _key(tail[1]) or tail[1] in ('lei','ani','persoane','oameni','case','elevi','euro','km')):
                end+=2
            elif tail and (tail[0] in ('lei','euro','ani','persoane','elevi','km') or _key(tail[0])):
                end+=1
            spans.append((135,i,end,'numeric'))
        if _key(w):
            # Pair topic noun and salient descriptor if naturally adjacent.
            a,b=i,i+1
            if i>0 and normalized[i-1] not in CONNECTORS and len(normalized[i-1])>=5 and not _key(words[i-1]):
                a=i-1
            if b<len(words) and normalized[b] not in CONNECTORS and len(normalized[b])>=5:
                b+=1
            if b-a>3:b=a+3
            spans.append((75 + (10 if b-a>1 else 0),a,b,'topic'))
    if not spans:
        # No domain keyword: choose a meaningful existing content word, not a generic preposition.
        meaningful=[(len(n),i) for i,n in enumerate(normalized) if len(n)>=6 and n not in CONNECTORS]
        if meaningful:
            _,i=max(meaningful)
            spans.append((40,i,i+1,'lexical'))
    return spans


def semantic_emphasis(text):
    """Return a conservative set of whole-token indexes + auditable span metadata."""
    words=clean(text).split()
    n=len(words)
    if not n:return set(),[]
    max_words=max(1, math.floor(n*.4))
    max_spans=1 if n<10 else 2
    candidates=_candidate_spans(words)
    # Numeric beats topical; stable index tie-break preserves deterministic results.
    candidates.sort(key=lambda x:(-x[0],x[2]-x[1],x[1]))
    selected=set(); reasons=[]
    for score,a,b,reason in candidates:
        block=set(range(a,b))
        if not block-selected:continue
        if len(selected|block)>max_words:continue
        if selected and min(abs(a-z) for z in selected)<=1:continue
        selected.update(block)
        reasons.append({'text':' '.join(words[a:b]),'reason':reason,'startWord':a,'endWordExclusive':b})
        if len(reasons)>=max_spans:break
    # For short numeric phrases, a single amount takes priority over the cap.
    if not selected:
        for _,a,b,reason in candidates:
            if reason=='numeric':
                selected={a}; reasons=[{'text':words[a],'reason':'numeric','startWord':a,'endWordExclusive':a+1}]
                break
    return selected,reasons


def compact_lines(text, selected):
    """Minimum feasible line count; balanced, syntax-aware, and respects highlights."""
    src=clean(text)
    if not src:raise ValueError('Carton gol')
    words=src.split()
    if any(len(w)>HARD_MAX for w in words):raise ValueError('Cuvânt peste 33 caractere')
    n=len(words)
    for lines_count in range(1,MAX_LINES+1):
        target=len(src)/lines_count
        @lru_cache(None)
        def solve(start, remaining):
            if remaining==0:return (0.0,()) if start==n else None
            if n-start<remaining:return None
            best=None
            for stop in range(start+1,n+1):
                line=' '.join(words[start:stop])
                if len(line)>HARD_MAX:break
                tail=solve(stop,remaining-1)
                if tail is None:continue
                score=(len(line)-target)**2*.6 + max(0,len(line)-31)**2*5
                if len(line)<8 and lines_count>1:score+=85
                if stop<n:
                    prev=_norm(words[stop-1]); nxt=_norm(words[stop])
                    if prev in CONNECTORS:score+=55
                    if nxt in CONNECTORS:score+=20
                    if words[stop-1].endswith(('.', '!', '?')):score-=40
                    elif words[stop-1].endswith((',', ';', ':')):score-=18
                    if stop-1 in selected and stop in selected:score+=160
                state=(score+tail[0],(line,)+tail[1])
                if best is None or state[0]<best[0]:best=state
            return best
        got=solve(0,lines_count)
        if got is not None:
            lines=list(got[1])
            if ' '.join(lines)!=src:raise AssertionError('Text loss while wrapping')
            return ['']*(MAX_LINES-len(lines))+lines
    raise ValueError('Text carton prea lung (>4x33)')


def build_pages(original):
    """Existing paragraph/page splitter retained; replace only layout & emphasis."""
    source=clean(original)
    pages=[]
    for page_text, _legacy_lines in split_cards(source):
        selected, spans=semantic_emphasis(page_text)
        slots=compact_lines(page_text,selected)
        word_idx=0
        bold={str(i):'' for i in range(MAX_LINES)}
        for i,line in enumerate(slots):
            if not line:continue
            tokens=line.split()
            bold[str(i)]=' '.join(str(j+1) for j in range(len(tokens)) if word_idx+j in selected)
            word_idx+=len(tokens)
        if word_idx!=len(page_text.split()):raise AssertionError('Word index drift')
        pages.append({'text':page_text,'physicalLines':slots,'boldWords':bold,'emphasisPhrases':spans})
    if clean(' '.join(p['text'] for p in pages))!=source:
        raise ValueError('Carton changed by page layout')
    return pages
