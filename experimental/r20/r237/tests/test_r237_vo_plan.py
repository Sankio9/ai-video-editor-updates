"""R237 synthetic read-only VO alignment: no ASR requirement for cards;
missing interview sources remain placeholders, text unchanged and 28-char cap.
"""
import sys,types,json,hashlib,tempfile,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
sys.path.insert(0,str(Path('/tmp/r237_layout')))
def clean(s):return " ".join(str(s).split())
def split_cards(s):return [(s,[])]

sys.modules['r171_layout']=types.SimpleNamespace(clean=clean,split_cards=split_cards)
def editorial(doc,module):
    assert module=='04'
    text=['UN CARTON CU INFORMAȚII DESPRE UN PROIECT CARE AJUTĂ OAMENII DIN COMUNITATE.',
          'UN AL DOILEA CARTON CU DATE IMPORTANTE PENTRU PUBLICUL NOSTRU.']
    return {'schema':'aive-r20-graphics-v1','module':'04',
      'docx_sha256':hashlib.sha256(Path(doc).read_bytes()).hexdigest(),
      'items':[{'groupId':'VO-'+str(i),'text':t} for i,t in enumerate(text,1)]}
sys.modules['r20_graphics_plans']=types.SimpleNamespace(build=editorial,SCHEMA='aive-r20-graphics-v1')
from r220_montage_plan import digest
from r237_vo_plan import build
class Cases(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.root=Path(self.temp.name)
  self.doc=self.root/'example.docx';self.doc.write_bytes(b'fake deterministic DOCX test bytes')
  ident={'docxSHA256':hashlib.sha256(self.doc.read_bytes()).hexdigest(),
         'sequenceId':'ACTIVE_AIVE_TEST',
         'diagnosticSHA256':'0'*64}
  cuts=[
    {'cutId':'CUT-01','state':'CONFIRMED','sourceCode':'0007',
     'sourceName':'film.mov','sourceNodeId':'NODE-7','timelineStart':0.,'timelineEnd':4.,'durationSeconds':4.},
    {'cutId':'VO-001','state':'VO_RESERVE','estimated':True,'sourceCode':None,'sourceName':None,
     'durationSeconds':7.,'timelineStart':4.,'timelineEnd':11.},
    {'cutId':'CUT-02','state':'PLACEHOLDER','sourceCode':'0034',
     'sourceName':'missing.mov','estimated':True,'durationSeconds':5.,
     'timelineStart':11.,'timelineEnd':16.},
    {'cutId':'VO-002','state':'VO_RESERVE','estimated':True,'sourceCode':None,'sourceName':None,
     'durationSeconds':7.,'timelineStart':16.,'timelineEnd':23.}]
  self.m={'schema':'aive-r220-montage-plan-v1','phase':'ANALYSIS_ONLY',
          'identity':ident,'cuts':cuts,'totalCuts':2,'confirmedCount':1,
          'placeholderCount':1,'voReserveCount':2,'totalPlannedSeconds':23.}
  self.m['planSHA256']=digest(self.m)
  self.r={'schema':'aive-r220-missing-cuts-v1','phase':'POST_READBACK',
          'identity':ident,'planSHA256':self.m['planSHA256'],
          'confirmedInsertedCount':1,'placeholderReservedCount':1,
          'items':[{'cutId':'CUT-02'}]}
  self.mp=self.root/'plan.json';self.rp=self.root/'readback.json';self.save()
 def tearDown(self):self.temp.cleanup()
 def save(self):
  self.mp.write_text(json.dumps(self.m),encoding='utf8')
  self.rp.write_text(json.dumps(self.r),encoding='utf8')
 def test_partial_montage_cards_match_both_vo_reserves(self):
  p=build(self.doc,self.mp,self.rp)
  self.assertEqual(p['totalVO'],2)
  self.assertEqual((p['confirmedCUTs'],p['reservedCUTs']),(1,1))
  self.assertEqual([x['startSeconds'] for x in p['items']],[4.,16.])
  self.assertEqual([x['durationSeconds'] for x in p['items']],[7.,7.])
  self.assertTrue(all(len(line)<=28 for x in p['items'] for line in x['physicalLines']))
  self.assertEqual(p['limits']['charactersPerLine'],28)
  self.assertEqual(p['mode'],'montage_vo')
  self.assertEqual(p['timing'],'VO_RESERVE_ESTIMATED')
  print('PASS 2 VO cards V5 aligned 4s and 16s, 1 missing source allowed, max 28 chars')
 def test_missing_vo_slot_stops(self):
  self.m['cuts']=[x for x in self.m['cuts'] if x['cutId']!='VO-002']
  self.m['voReserveCount']=1
  self.m.pop('planSHA256',None)
  self.m['planSHA256']=digest(self.m)
  self.r['planSHA256']=self.m['planSHA256']
  self.save()
  with self.assertRaisesRegex(ValueError,'VO_BLOCKS_NOT_ALIGNED'):build(self.doc,self.mp,self.rp)
  print('PASS no guess when plan VO slot count differs from script')
 def test_invalid_sha_and_unreadback_stops(self):
  self.m['planSHA256']='a'*64;self.save()
  with self.assertRaisesRegex(ValueError,'PLAN_SHA_MISMATCH'):build(self.doc,self.mp,self.rp)
  self.m.pop('planSHA256',None)
  self.m['planSHA256']=digest(self.m);self.r['phase']='ANALYSIS_ONLY';self.save()
  with self.assertRaisesRegex(ValueError,'MONTAGE_READBACK_REQUIRED'):build(self.doc,self.mp,self.rp)
  print('PASS no VO graphics with changed plan or missing verified live readback')
if __name__=='__main__':unittest.main(verbosity=2)
