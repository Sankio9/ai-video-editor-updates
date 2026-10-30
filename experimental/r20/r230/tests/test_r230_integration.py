"""R230 integration: authentic R2.1.2 wrapper + universal fallback, mock unavailable
legacy helper modules. No private newsroom scripts uploaded to the repository."""
from __future__ import annotations
import sys,types,tempfile,re
from pathlib import Path
from docx import Document

def mod(name,**members):sys.modules[name]=types.SimpleNamespace(**members)
def clean(t):return ' '.join(t.split())
def split(t,limit=74):
    r=[];a=''
    for w in t.split():
        if len(w)>limit:raise ValueError('word over 74')
        if not a:a=w
        elif len(a)+1+len(w)<=limit:a+=' '+w
        else:r.append(a);a=w
    if a:r.append(a)
    return r
def pages(t):
    words=t.split();lines=[];a=''
    for w in words:
        if len(w)>33:raise ValueError('word >33')
        if not a:a=w
        elif len(a)+len(w)+1<=33:a+=' '+w
        else:lines.append(a);a=w
    if a:lines.append(a)
    ret=[]
    for i in range(0,len(lines),4):
        chunk=lines[i:i+4];tt=clean(' '.join(chunk));ll=chunk+['']*(4-len(chunk))
        ret.append({'text':tt,'physicalLines':ll,'boldWords':{str(k):'' for k in range(4)},'emphasisPhrases':[]})
    return ret
mod('reportaj_r1_parse_docx',extract=lambda p:{'segments':[],'graphics':[]})
mod('r193_docx_reader',read=lambda p:{'segments':[],'captions':[]})
mod('r161_prepare_nametags',card_for=lambda s:None)
mod('r171_layout',clean=clean)
mod('r204_carton_layout',build_pages=pages)
mod('r207_docx_strike',extract_strike_policy=lambda *a:None)
mod('r153_prepare',split_balanced=lambda t,limit=74:split(t,limit))
sys.path.insert(0,'/tmp/aive_runtime/tools')
from r20_graphics_plans import build

def case(name,paragraphs):
    d=Document()
    for p in paragraphs:d.add_paragraph(p)
    return d
def verify(doc,expect):
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'reporter.docx';doc.save(path)
        for module in ('02','03','04'):
            if module not in expect:
                try:build(path,module)
                except ValueError as e:
                    assert 'Nu există' in str(e) or 'Nicio burtieră' in str(e) or 'Nu sunt declarații' in str(e),(module,str(e))
                else:raise AssertionError('unexpected invented data: '+module)
                continue
            p=build(path,module)
            assert p['mode']=='independent' and p['containsAudioSync'] is False
            assert p['generatorVersion']=='R2.3-UNIVERSAL-DOCX-9-FORMATS'
            assert len(p['items'])>0
            assert p['module']==module and p['totalItems']==len(p['items'])
            assert all(0.8<=x['durationSeconds']<=15 for x in p['items'])
            if module=='02':assert all(len(x['text'])<=74 for x in p['items'])
            if module=='04':assert all(len(y)<=33 for x in p['items'] for y in x['physicalLines'])
            if module=='03':assert all(x.get('name') and x.get('title') for x in p['items'])
            print('PASS',module,'count',len(p['items']),p['generatorVersion'])

# Each case includes only synthetic snippets that reflect editorial formats,
# not any real user's confidential DOCX text.
verify(case('native',['Titlu știre','SCENARIU','INFORMAȚII DESPRE SAT','0230','Ana Ionescu','farmacistă-diriginte',
  '01:01 Medicamentele sunt disponibile aici. 01:05','O FARMACIE NOUĂ PENTRU SAT']),('02','03','04'))
verify(case('vox',['VOX: MARIA, pensionară','0640','00:10–00:17',
  'Nu mai folosesc platforma digitală.','PLATFORMA ESTE ÎN CURS DE VERIFICARE']),('02','03','04'))
verify(case('carton',['AMBIANȚĂ: Imagini din localitate','SINCRON: Radu Ionescu, pensionar',
  'C9625','05:01 - 05:08','Nu am plecat nicăieri.','CARTON:','Oamenii au nevoie de ajutor.']),('02','03','04'))
verify(case('pkg_only',['PKG','UN PETROLIER A FOST VĂZUT ÎN LARG','ECHIPAJUL A FOST EVACUAT']),('04',))
verify(case('herson',['Script:','Geo: Herson','O NOUĂ ZI PENTRU OAMENI',
  'Evhen Exemplu, locuitor din Herson','Vreau să pot merge acasă.']),('02','03','04'))
verify(case('sot',['PKG','UN REPORTAJ DESPRE O COMUNITATE',
  'SOT [07:08] [07:18]\\nVera Exemplu\\nfiica unui localnic',
  'Oamenii obișnuiți au ajutat comunitatea.']),('02','03','04'))
verify(case('no_role',['PKG','MIHAIL EXEMPLU','Astăzi am venit aici pentru a discuta.',
  'O IDEE PENTRU COMUNITATE']),('02','04'))
# One script has named speakers only inside a 2-column editorial table.
d=Document(); d.add_paragraph('PKG')
t=d.add_table(rows=2,cols=2)
t.cell(0,0).text='Gulmira Exemplu\\nmamă'
t.cell(0,1).text='Cred că trebuie să protejăm copiii.'
t.cell(1,0).text='Reporter / Reuters'
t.cell(1,1).text='Narațiune de lucru fără marcaj de carton'
verify(d,('02','03'))
print('PASS R230 integration: original released wrapper + 8 distinct synthetic editorial shapes')
