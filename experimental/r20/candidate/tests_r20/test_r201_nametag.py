"""Safety regressions for R2.0.1 independent NameTag planner (synthetic DOCX only)."""
import sys, tempfile, unittest
from pathlib import Path
from docx import Document
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from r20_graphics_plans import build,_name_blocks
class TestR201(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
    def tearDown(self):
        self.t.cleanup()
    def test_inline_merged_headers(self):
        doc=Document();doc.add_paragraph('SCRIPT')
        doc.add_paragraph('SINCRON: Ana Ștefănescu, Directoare\n1234\n0:01-0:08\nPrima declarație despre școală.')
        doc.add_paragraph('0:09-0:13\nA doua declarație a aceleiași persoane.')
        doc.add_paragraph('AMB: Ion Popescu, Profesor\n5678\n0:02-0:05\nÎn atelier elevii lucrează.')
        doc.add_paragraph('SINCRON: Ana Ștefănescu, Directoare\n1234\n0:16-0:20\nAna a revenit.')
        p=Path(self.t.name)/'merged.docx';doc.save(p)
        data=build(p,'03')
        self.assertEqual(data['groups'],3)
        self.assertEqual([x['name'] for x in data['items']],['Ana Ștefănescu','Ion Popescu','Ana Ștefănescu'])
        self.assertEqual(data['timing'],'EDITORIAL_PREVIEW')
    def test_missing_first_header(self):
        def seg(i,p,code,name,role):
            return {'ordinal':i,'paragraph_start':p,'source_code':code,'speaker':name,'role':role}
        src=[seg(1,5,'9981','Elena','Director'),seg(2,7,'9981','Elena','Director'),
             seg(3,10,'9974','Ion','Profesor'),seg(4,12,'9981','Elena','Director')]
        self.assertEqual([r[2] for r in _name_blocks(src,[])],[1,1,2,3])
    def test_repeated_identity_new_header(self):
        src=[{'ordinal':i+1,'paragraph_start':p,'source_code':'1234',
              'speaker':'Ana','role':'Director'} for i,p in enumerate([3,4,7])]
        self.assertEqual([r[2] for r in _name_blocks(src,[(2,'editorial',None),(6,'editorial',None)])],[1,1,2])
    def test_conflicting_source_rejected(self):
        src=[{'ordinal':1,'paragraph_start':5,'source_code':'9981','speaker':'Ana','role':'Director'}]
        with self.assertRaisesRegex(ValueError,'REVIEW: cod sursă'):
            list(_name_blocks(src,[(4,'source','9974')]))
    def test_unknown_identity_no_fabrication(self):
        src=[{'ordinal':1,'paragraph_start':5,'source_code':'1234','speaker':'Ana','role':'Director'},
             {'ordinal':2,'paragraph_start':6,'source_code':'1234','speaker':None,'role':None},
             {'ordinal':3,'paragraph_start':7,'source_code':'1234','speaker':'Ana','role':'Director'}]
        rows=list(_name_blocks(src,[]))
        self.assertEqual([r[2] for r in rows],[1,None,2])
if __name__=='__main__':
    unittest.main(verbosity=2)
