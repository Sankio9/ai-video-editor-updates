"""R2.3.3 safe no-content and plain-CN regression without actual user files.

If a Word document does not declare eligible graphics, the parser must NOT
invent them or throw an exception. 02 only offers a guarded CN preview when
a script heading or multiple narrative paragraphs support it.
"""
import sys,types,tempfile
from pathlib import Path
from docx import Document
root=Path(__file__).resolve().parents[1]/'candidate'/'tools'
sys.path.insert(0,str(root))
def splitter(text,limit=74):
 words=text.split();cur='';out=[]
 for w in words:
  if cur and len(cur)+1+len(w)>limit:out.append(cur);cur=w
  else:cur=(cur+' '+w).strip()
 if cur:out.append(cur)
 return out
sys.modules['r20_graphics_plans']=types.SimpleNamespace(split_subtitles_readable=splitter)
def build_pages(text):
 lines=[];line=''
 for w in text.split():
  if line and len(line)+1+len(w)>33:
   lines.append(line);line=w
  else:line=(line+' '+w).strip()
 if line:lines.append(line)
 return [{'text':' '.join(lines[i:i+4]),
          'physicalLines':(lines[i:i+4]+['','','',''])[:4],
          'boldWords':{'0':'','1':'','2':'','3':''},
          'emphasisPhrases':[]} for i in range(0,len(lines),4)]
sys.modules['r204_carton_layout']=types.SimpleNamespace(build_pages=build_pages)
from r230_universal import build,parse
def save(path,lines):
 d=Document()
 for line in lines:d.add_paragraph(line)
 d.save(path)
with tempfile.TemporaryDirectory() as folder:
 folder=Path(folder)
 p=folder/'metadata_only.docx'
 save(p,['TITLU: Proiect editorial','DURATION: 02:00','SOURCE: Producție',
         'ONLINE: https://example.org/story','GEO: Chișinău'])
 for m in ('02','03','04'):
  output=build(p,m)
  assert output['totalItems']==0 and output['items']==[]
  assert output['contentSummary']['message']
  assert output['contentSummary']['paragraphs']==5
  assert output['contentSummary']['autoCn'] is False
  assert output['reviewRequired'] is False
  print('PASS',m,'metadata only -> safe empty no invented graphics')
 p=folder/'plain_transcript.docx'
 save(p,['SCENARIU',
         'Am analizat documentele și am descoperit că unele date personale pot fi expuse.',
         'Autoritățile urmează să anunțe noi măsuri pentru securitatea sistemului.',
         'Reporterii au discutat cu mai mulți locuitori pentru a le afla opiniile.'])
 captions=build(p,'02')
 assert captions['totalItems']>0
 assert captions['contentSummary']['autoCn'] is True
 assert all(x['fontStyle']=='Italic' for x in captions['items'])
 assert all(len(x['text'])<=74 for x in captions['items'])
 assert build(p,'03')['totalItems']==0
 assert build(p,'04')['totalItems']==0
 print('PASS plain SCENARIU -> guarded Italic CN subtitles; 03/04 no fabricated content')
 p=folder/'title_and_teaser.docx'
 save(p,['Un titlu jurnalistic despre o situație complicată.',
         'Primul paragraf explică pe scurt evenimentul și prezintă câteva informații generale.'])
 for m in ('02','03','04'):
  assert build(p,m)['totalItems']==0
 print('PASS teaser/document without script marker -> no unapproved captions')
 p=folder/'full_markup.docx'
 save(p,['SINCRON: Ioana Exemplu, pensionară','0667','00:15–00:20',
         'Am primit o notificare și nu știam ce ar trebui să fac.',
         'CARTON:','VORBIM DESPRE SIGURANȚA DATELOR PERSONALE'])
 assert build(p,'02')['totalItems']>0
 assert build(p,'03')['totalItems']==1
 assert build(p,'04')['totalItems']==1
 assert not build(p,'02')['contentSummary']['autoCn']
 print('PASS explicit speaker/CARTON original 02/03/04 remains recognized')
print('R233 all scenarios passed')
