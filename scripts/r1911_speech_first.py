"""R1.9.11: speech-led, script-validated boundary suggestions.

DOCX determines the utterance and approximate reporter TC. ASR determines
actual cut IN/OUT. Never use reporter timecode as an automatic fallback.
"""
from __future__ import annotations
from math import isfinite
from reportaj_r13_ai_match import tokens
from r141_match import similarity, suggest_boundaries as legacy_suggest

MATCHER_VERSION='r1911-speech-led-1'
SEARCH_WINDOW_SECONDS=90.
MAX_ACCEPTED_SHIFT_SECONDS=75.
MIN_FULL_TEXT_SCORE=.67
MIN_BOUNDARY_SCORE=.67

def suggest_boundaries(ev,words,time_offset=0.,max_search_s=50.):
    result=legacy_suggest(ev,words,time_offset=time_offset,max_search_s=SEARCH_WINDOW_SECONDS)
    start,end=result.get('proposedIn'),result.get('proposedOut')
    result['matchMethod']=MATCHER_VERSION
    result['searchRadiusSeconds']=SEARCH_WINDOW_SECONDS
    result['fullTextScore']=0.
    if not isinstance(start,(int,float)) or not isinstance(end,(int,float)):
        return result
    if not all(isfinite(x) for x in (start,end)) or end<=start:
        result['status']='REVIEW_INVALID_BOUNDS'
        result['reason']='Limitele ASR propuse sunt invalide.'
        return result
    query=tokens(str(ev.get('text') or ''))
    heard=[]
    for w in words:
        at=float(w['start'])+time_offset
        if start-.08<=at<end+.08:
            heard.extend(tokens(str(w.get('norm') or w.get('word') or '')))
    full=similarity(query,heard) if query and heard else 0.
    result['fullTextScore']=round(full,4)
    # A repeated utterance is ambiguous even when its timecode appears closer.
    if len(heard)>=5 and full>=MIN_FULL_TEXT_SCORE:
        anchor=heard[:min(3,len(heard))]
        normalized=[str(w.get('norm') or '') for w in words]
        length=len(heard)
        for i in range(max(0,len(normalized)-length+1)):
            at=float(words[i]['start'])+time_offset
            if abs(at-start)<7. or abs(at-float(ev.get('inSeconds',0.)))>SEARCH_WINDOW_SECONDS:
                continue
            if normalized[i:i+len(anchor)]!=anchor:continue
            alternative=similarity(heard,normalized[i:i+length])
            if alternative>=max(.78,full-.035):
                result['status']='REVIEW_ALTERNATIVE_OCCURRENCE'
                result['reason']='Aceeași declarație apare de mai multe ori în ASR; TC nu poate decide.'
                return result
    drift=max(0. if ev.get('inAssumed') else abs(start-float(ev['inSeconds'])),
              abs(end-float(ev['outSeconds'])))
    result['driftSeconds']=round(drift,3)
    beginning=float(result.get('startScore') or 0.)
    ending=float(result.get('endScore') or 0.)
    # Text-driven score; reporter timecode is not used as a score component.
    result['score']=round(.32*beginning+.32*ending+.36*full,4)
    if result['status']=='REVIEW_ALTERNATIVE_OCCURRENCE':return result
    if beginning<MIN_BOUNDARY_SCORE or ending<MIN_BOUNDARY_SCORE:
        result['status']='REVIEW_WEAK_BOUNDARY'
        result['reason']='Începutul/sfârșitul declarației nu corespunde clar cu ASR.'
    elif full<MIN_FULL_TEXT_SCORE:
        result['status']='REVIEW_WEAK_TRANSCRIPT'
        result['reason']='Textul complet nu corespunde suficient cu transcrierea audio.'
    elif drift>MAX_ACCEPTED_SHIFT_SECONDS:
        result['status']='REVIEW_OUTSIDE_SEARCH_RADIUS'
        result['reason']='Declarația este la peste 75 secunde de timecode; necesită verificare.'
    elif result['status'] not in ('REVIEW_SUGGESTED','REVIEW_LARGE_SHIFT'):
        return result
    else:
        result['status']='REVIEW_SUGGESTED'
        result['reason']='IN/OUT din ASR + text DOCX; timecode orientativ.'
    return result

def validate_speech_only(plan):
    cuts=[ev for ev in plan.get('events',[]) if ev.get('kind')=='cut']
    if not cuts:raise ValueError('OPRIT: planul nu conține sincronuri.')
    if plan.get('aiAnalysis',{}).get('runtime',{}).get('mode')!='REAL_AUDIO':
        raise ValueError('OPRIT: montajul necesită transcriere audio reală.')
    uncertain=[]
    for ev in cuts:
        asr=ev.get('asr') or {}
        valid=(asr.get('status')=='AI_MATCHED' and
               all(isinstance(asr.get(k),(int,float)) and isfinite(asr[k]) and asr[k]>=threshold
                   for k,threshold in [('startScore',MIN_BOUNDARY_SCORE),
                                       ('endScore',MIN_BOUNDARY_SCORE),
                                       ('fullTextScore',MIN_FULL_TEXT_SCORE)]))
        if not valid:
            uncertain.append(str(ev.get('id'))+' ['+str(ev.get('sourceCode'))+']: '+
                             str(asr.get('reason') or 'fără potrivire audio sigură'))
    if uncertain:
        raise ValueError('OPRIT: '+str(len(uncertain))+'/'+str(len(cuts))+
                         ' sincronuri fără potrivire audio sigură. NU modificăm timeline-ul. '+
                         'Timecode-ul reporterului nu este fallback. Verifică: '+
                         '; '.join(uncertain[:12]))
    return len(cuts)
