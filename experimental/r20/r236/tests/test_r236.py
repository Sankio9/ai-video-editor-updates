"""R236: preserve confirmed NameTags when one DOCX source is contradictory;
avoid global V3 abort when one confirmed audio CUT cannot fit readable captions.
No Premiere writes, no source rewrite and no clip timecode fallback.
"""
import sys,types,hashlib,json,tempfile,unittest
from pathlib import Path
ROOT=Path('/tmp/r236_runtime/tools')
sys.path.insert(0,str(ROOT))
def clean(x):return " ".join(str(x).split())
def card_for(seg):
    return (seg['speaker'],seg['role'],False) if seg.get('speaker') and seg.get('role') else None
sys.modules['reportaj_r1_parse_docx']=types.SimpleNamespace(extract=lambda f:{'segments':[],'graphics':[]})
sys.modules['r193_docx_reader']=types.SimpleNamespace(read=lambda f:{'segments':[],'captions':[]})
sys.modules['r161_prepare_nametags']=types.SimpleNamespace(card_for=card_for)
sys.modules['r171_layout']=types.SimpleNamespace(clean=clean)
sys.modules['r204_carton_layout']=types.SimpleNamespace(build_pages=lambda t:[])
sys.modules['r207_docx_strike']=types.SimpleNamespace(extract_strike_policy=lambda *args:None)
sys.modules['r153_prepare']=types.SimpleNamespace(split_balanced=lambda txt,limit=74:[txt])
import r20_graphics_plans as G
import r226_partial_subtitles as S

def row(idx,source,name=None,title=None):
    return {'ordinal':idx,'source_code':source,'speaker':name,'role':title,
            'paragraph_start':idx,'paragraph_end':idx,'text':'Replica '+str(idx),
            'reporter_italic':False}
markers=[(0,'editorial',None),(1,'source','0034'),(3,'source','0007')]
class Tests(unittest.TestCase):
 def test_name_conflict_is_skipped_but_next_valid_name_is_created(self):
    seg=[row(1,'0034','Alexandru Prim','martor'),row(3,'0007','Maria Secund','pensionară'),
         row(4,'0007','Dumitru Tert','profesor')]
    # Last header for CUT03 is DOCX 0034; CUT has 0007. The mismatch
    # must be skipped/reviewed. A later header 0007 restores confidence.
    marks=[(0,'editorial',None),(1,'source','0034'),(4,'source','0007')]
    old_extract,old_mark=G._extract,G._editorial_markers
    try:
       G._extract=lambda doc:(seg,[],{})
       G._editorial_markers=lambda doc:marks
       with tempfile.TemporaryDirectory() as tmp:
          f=Path(tmp)/'source.docx';f.write_bytes(b'synthetic')
          result=G.build(f,'03')
       self.assertEqual([x['name'] for x in result['items']],['Alexandru Prim','Dumitru Tert'])
       self.assertEqual(len(result['skipped']),1)
       self.assertEqual(result['skipped'][0]['cutId'],'CUT-03')
       self.assertIn('COD_SURSĂ_CONTRADICTORIU',result['skipped'][0]['reason'])
       self.assertTrue(result['reviewRequired'])
       self.assertEqual(result['reviewPolicy'],'EXPLICIT_SKIP_APPROVAL')
       print('PASS V4 source contradiction at CUT-03 is explicit REVIEW; other NameTags survive')
    finally:
       G._extract=old_extract;G._editorial_markers=old_mark
 def test_all_name_conflicts_return_safe_empty_review_plan(self):
    seg=[row(3,'0007','Maria Secund','pensionară')]
    old_extract,old_mark=G._extract,G._editorial_markers
    try:
       G._extract=lambda doc:(seg,[],{})
       G._editorial_markers=lambda doc:[(1,'source','0034')]
       with tempfile.TemporaryDirectory() as tmp:
          f=Path(tmp)/'source.docx';f.write_bytes(b'synthetic')
          result=G.build(f,'03')
       self.assertEqual(result['totalItems'],0)
       self.assertTrue(result['reviewRequired'])
       self.assertEqual(result['skipped'][0]['kind'],'REVIEW_MISSING_IDENTITY')
       print('PASS all ambiguous NameTags: 0-item review rather than global Python error')
    finally:G._extract=old_extract;G._editorial_markers=old_mark
 def fixture(self,all_bad=False):
    temp=tempfile.TemporaryDirectory()
    root=Path(temp.name);doc=root/'fake.docx';doc.write_bytes(b'example-not-real-docx')
    hashword=hashlib.sha256(doc.read_bytes()).hexdigest()
    seq="TEST_AIVE_SEQ"
    cuts=[
      {'cutId':'CUT-01','sourceCode':'0007','sourceName':'A.mp4','sourceNodeId':'ID-1',
       'state':'CONFIRMED','timelineStart':0.,'timelineEnd':.45 if not all_bad else .35},
      {'cutId':'CUT-02','sourceCode':'0034','sourceName':'B.mp4','sourceNodeId':'ID-2',
       'state':'CONFIRMED','timelineStart':2.,'timelineEnd':10. if not all_bad else 2.4},
      {'cutId':'CUT-03','sourceCode':'9981','sourceName':'Missing.mp4',
       'state':'PLACEHOLDER','timelineStart':10.,'timelineEnd':14.}]
    montage={'schema':'aive-r220-montage-plan-v1','phase':'ANALYSIS_ONLY',
       'identity':{'docxSHA256':hashword,'sequenceId':seq,'diagnosticSHA256':'a'*64},
       'planSHA256':'d'*64,'totalCuts':3,'confirmedCount':2,'placeholderCount':1,'cuts':cuts}
    report={'schema':'aive-r220-missing-cuts-v1','phase':'POST_READBACK',
       'identity':montage['identity'],'planSHA256':'d'*64,
       'confirmedInsertedCount':2,'placeholderReservedCount':1,'items':[{'cutId':'CUT-03'}]}
    mp=root/'montage.json';rp=root/'report.json'
    mp.write_text(json.dumps(montage),encoding='utf8')
    rp.write_text(json.dumps(report),encoding='utf8')
    return temp,doc,mp,rp
 def test_short_confirmed_cut_is_reviewed_others_survive(self):
    temp,doc,mp,rp=self.fixture()
    old_ind,old_ex=S.independent_subtitles,S._extract
    try:
       S.independent_subtitles=lambda d,m,omit_struck=False:{
        'items':[{'groupId':f'CUT-{n:02d}','text':f'Declarația {n}.','fontStyle':'Regular'} for n in range(1,4)],
        'omittedStrikeCuts':[],'strikeCutsChanged':0,'removedStrikeCharacters':0}
       S._extract=lambda d:([row(1,'0007'),row(2,'0034'),row(3,'9981')],[],{})
       result=S.build(doc,mp,rp)
       self.assertEqual(result['confirmedCount'],2)
       self.assertEqual(result['reservedCount'],1)
       self.assertEqual(len(result['skippedConfirmedCuts']),1)
       self.assertEqual(result['skippedConfirmedCuts'][0]['cutId'],'CUT-01')
       self.assertEqual([x['groupId'] for x in result['items']],['CUT-02'])
       self.assertTrue(all(x['startSeconds']>=2 and
              x['startSeconds']+x['durationSeconds']<=10 for x in result['items']))
       self.assertTrue(all(x['groupId']!='CUT-03' for x in result['items']))
       self.assertEqual(result['contentSHA256'],hashlib.sha256(json.dumps(
         {k:v for k,v in result.items() if k!='contentSHA256'},ensure_ascii=False,
         sort_keys=True,separators=(',',':')).encode('utf8')).hexdigest())
       print('PASS subtitle confirmed CUT-01 too short reviewed, CUT-02 inserted, placeholder CUT-03 untouched')
    finally:S.independent_subtitles=old_ind;S._extract=old_ex;temp.cleanup()
 def test_no_confirmed_cut_eligible_stops_before_premiere(self):
    temp,doc,mp,rp=self.fixture(all_bad=True)
    old_ind,old_ex=S.independent_subtitles,S._extract
    try:
       S.independent_subtitles=lambda d,m,omit_struck=False:{
        'items':[{'groupId':f'CUT-{n:02d}','text':f'Replica {n}.','fontStyle':'Regular'} for n in range(1,4)],
        'omittedStrikeCuts':[],'strikeCutsChanged':0,'removedStrikeCharacters':0}
       S._extract=lambda d:([row(1,'0007'),row(2,'0034'),row(3,'9981')],[],{})
       with self.assertRaisesRegex(ValueError,'NO_ELIGIBLE_SUBTITLES'):
           S.build(doc,mp,rp)
       print('PASS all confirmed audio CUTs impossible -> fail safely before V3')
    finally:S.independent_subtitles=old_ind;S._extract=old_ex;temp.cleanup()
if __name__=='__main__':unittest.main(verbosity=2)
