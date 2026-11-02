"""R2.3.7 synthetic newsroom Word regression fixtures, based on layout,
not private user text. Mixed italic, strike, combined header/source/timecode.
"""
import sys,tempfile,types
from pathlib import Path
from docx import Document
ROOT=Path('/tmp/r245_runtime/tools');sys.path.insert(0,str(ROOT))
def split(txt,limit=74):
    out=[];cur=''
    for w in txt.split():
        if cur and len(cur)+len(w)+1>limit:out.append(cur);cur=w
        else:cur=(cur+' '+w).strip()
    if cur:out.append(cur)
    return out
def pages(t):
    words=t.split();pages=[];lines=[];cur=''
    for w in words:
        if cur and len(cur)+len(w)+1>28:lines.append(cur);cur=w
        else:cur=(cur+' '+w).strip()
    if cur:lines.append(cur)
    for i in range(0,len(lines),4):
        subset=lines[i:i+4]
        pages.append({'text':' '.join(subset),'physicalLines':(subset+['','','',''])[:4],
                      'boldWords':{},'emphasisPhrases':[]})
    return pages
sys.modules["r204_carton_layout"]=types.SimpleNamespace(build_pages=pages)
sys.modules["r153_prepare"]=types.SimpleNamespace(split_balanced=split)
sys.modules["reportaj_r1_parse_docx"]=types.SimpleNamespace(extract=lambda x:{"segments":[],"graphics":[]})
sys.modules["r193_docx_reader"]=types.SimpleNamespace(read=lambda x:{"segments":[],"captions":[]})
sys.modules["r161_prepare_nametags"]=types.SimpleNamespace(card_for=lambda x:None)
sys.modules["r171_layout"]=types.SimpleNamespace(clean=lambda x:' '.join(x.split()))
sys.modules["r207_docx_strike"]=types.SimpleNamespace(extract_strike_policy=lambda *x:None)
from r20_graphics_plans import build
from r230_universal import parse

with tempfile.TemporaryDirectory() as t:
    t=Path(t)
    angel=t/'angelus_layout.docx'
    d=Document();d.add_paragraph('An editorial headline for the story')
    d.add_paragraph('An opening article description that is not part of the filmed report.')
    d.add_paragraph('Ambianță');d.add_paragraph('7989')
    d.add_paragraph('00.06 Bună ziua, vreți ceai?')
    d.add_paragraph('Da');d.add_paragraph('Da. Ceaiul este dulce. 00.13')
    d.add_paragraph('COPIII SUNT ÎNGRIJIȚI CU ATENȚIE DE SPECIALIȘTII DIN CENTRU')
    d.add_paragraph('7967');d.add_paragraph('VASILE');d.add_paragraph('beneficiar')
    d.add_paragraph('00.10 Vin aici de mai multe ori pentru activitățile zilnice. 00.14')
    d.add_paragraph('00.26 Mă simt foarte bine cu colegii și cu personalul. 00.37')
    d.add_paragraph('7966');d.add_paragraph('MARIA');d.add_paragraph('beneficiară')
    d.add_paragraph('00.05 Eu apreciez activitățile și oamenii de aici. 00.25')
    d.save(angel)
    parsed=parse(angel)
    assert not any(x['text'] in ('VASILE','MARIA','beneficiar','beneficiară') for x in parsed['segments'])
    one=[x for x in parsed['segments'] if 'Vin aici' in x['text']]
    assert len(one)==1 and one[0]['speaker']=='VASILE' and one[0]['role']=='beneficiar'
    subtitles=build(angel,'02')
    assert all(x['text'] not in ('VASILE','MARIA','beneficiar','beneficiară') for x in subtitles['items'])
    tags=build(angel,'03')
    assert {(x['name'],x['title']) for x in tags['items']}=={('VASILE','beneficiar'),('MARIA','beneficiară')}
    assert tags['sourceNameReview']['verified']==2
    print('PASS Casa Angelus: one-word VASILE/beneficiar and MARIA/beneficiară only V4, no V3 metadata')
    foreign=t/'workers_layout.docx'
    d=Document();d.add_paragraph('Human-interest report about workers')
    d.add_paragraph('ABDULLAH ARE O EXPERIENȚĂ ÎN DOMENIUL CONSTRUCȚIILOR')
    p=d.add_paragraph()
    p.add_run('SINCRON: ABDULLAH AL MAMUNM, muncitor în construcții\n8170\n00.44–00.56\n')
    p.add_run('Am hotărât să lucrez aici. ')
    p.add_run('Ce ai aflat la universitate?').italic=True
    p.add_run(' Am studiat și am învățat mai multe.')
    d.add_paragraph('ALȚI COLEGI AU VENIT LA ACEASTĂ ȘCOALĂ DE EXPERIENȚĂ')
    d.add_paragraph('5.58–6.16')
    p=d.add_paragraph()
    p.add_run('În viitor mă voi întoarce în țara mea. ').font.strike=True
    q=p.add_run('Ce îți dorești să faci acolo?');q.italic=True;q.font.strike=True
    p.add_run('Când o să reușesc să strâng destui bani, mă întorc să deschid o afacere.')
    d.add_paragraph('SINCRON: OHE KHAN, curier')
    d.add_paragraph('8173')
    d.add_paragraph('00.07–00.21 Aici pot lucra și pot câștiga experiență de viață. 00.21')
    d.save(foreign)
    f=parse(foreign)
    assert len([x for x in f['segments'] if x['speaker']=='ABDULLAH AL MAMUNM'])>=3
    assert not any('SINCRON:' in x['text'] or x['text']=='8170' for x in f['segments'])
    assert any(x['reporter_italic'] and 'Ce ai aflat' in x['text'] for x in f['segments'])
    regular=[x for x in f['segments'] if 'Când o să reușesc' in x['text']]
    assert len(regular)==1 and not regular[0]['reporter_italic'],regular
    kept=build(foreign,'02',omit_struck=True)
    assert any('Când o să reușesc' in x['text'] and x['fontStyle']=='Regular' for x in kept['items'])
    assert not any('Ce îți dorești' in x['text'] for x in kept['items'])
    tags=build(foreign,'03')
    assert {(x['name'],x['title']) for x in tags['items']}=={
         ('ABDULLAH AL MAMUNM','muncitor în construcții'),('OHE KHAN','curier')}
    assert tags['sourceNameReview']['verified']==2
    print('PASS Muncitori: mixed-inline SINCRON/8170/timecode, reporter Italic then Regular, mixed-strike, V4 explicit marker')
print('R245 Word editorial structural test PASS')
