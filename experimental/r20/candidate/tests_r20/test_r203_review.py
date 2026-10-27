"""R2.0.3: incomplete editorial identities require EXPLICIT skip approval in CEP.

Synthetic input only. No user DOCX or private transcript enters public GitHub.
"""
import contextlib, io, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from docx import Document
from test_r201_nametag import planner, seg

class TestR203ReviewGate(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.doc=Path(self.t.name)/'synthetic.docx'
        d=Document()
        for i in range(10):d.add_paragraph('Fragment editorial de verificare '+str(i))
        d.save(self.doc)
    def tearDown(self):self.t.cleanup()
    def segments(self):
        return [seg(i+1,i,'1234','Persoana '+str(i+1) if i not in (4,8) else None,
                    'Funcție '+str(i+1) if i not in (4,8) else None)
                for i in range(10)]
    def test_eight_valid_two_review_without_fake_names(self):
        with patch.object(planner,'_extract',return_value=(self.segments(),[],{})):
            result=planner.build(self.doc,'03')
        self.assertEqual(result['totalItems'],8)
        self.assertEqual(result['groups'],8)
        self.assertEqual([x['cutId'] for x in result['skipped']],['CUT-05','CUT-09'])
        self.assertEqual([x['paragraph'] for x in result['skipped']],[4,8])
        self.assertTrue(result['reviewRequired'])
        self.assertEqual(result['reviewPolicy'],'EXPLICIT_SKIP_APPROVAL')
        self.assertEqual(result['timing'],'EDITORIAL_PREVIEW')
        self.assertTrue(all(x['name'] not in ('',None) and x['title'] not in ('',None) for x in result['items']))
        self.assertFalse(any('CUT-05' in x['groupId'] or 'CUT-09' in x['groupId'] for x in result['items']))
    def test_cli_persists_review_identically(self):
        target=Path(self.t.name)/'plan.json'
        with patch.object(planner,'_extract',return_value=(self.segments(),[],{})):
            with patch.object(sys,'argv',['r20_graphics_plans.py','--docx',str(self.doc),'--module','03','--output',str(target)]):
                log=io.StringIO()
                with contextlib.redirect_stdout(log):planner.main()
        signal=json.loads(log.getvalue())
        plan=json.loads(target.read_text('utf8'))
        self.assertTrue(signal['ok'])
        self.assertEqual(signal['skipped'],plan['skipped'])
        self.assertTrue(signal['reviewRequired'])
        self.assertEqual(signal['count'],8)
        self.assertEqual(signal['docx_sha256'],plan['docx_sha256'])
    def test_no_missing_no_extra_confirmation(self):
        all_named=[seg(1,0,'1234','Ana','Director'),seg(2,1,'5678','Ion','Profesor')]
        with patch.object(planner,'_extract',return_value=(all_named,[],{})):
            p=planner.build(self.doc,'03')
        self.assertEqual(p['skipped'],[])
        self.assertFalse(p['reviewRequired'])
        self.assertEqual(p['reviewPolicy'],'NONE')
    def test_all_unnamed_still_fails_closed(self):
        all_blank=[seg(1,0,'1234',None,None),seg(2,1,'5678',None,None)]
        with patch.object(planner,'_extract',return_value=(all_blank,[],{})):
            with self.assertRaisesRegex(ValueError,'Nu există elemente valide'):
                planner.build(self.doc,'03')
    def test_synced_executor_and_legacy_untouched(self):
        p=Path(__file__).resolve().parents[1]
        panel=(p/'cep/r20_panel.js').read_text('utf8')
        self.assertIn("if(!window.confirm(question))",panel)
        self.assertIn("Nicio inserare V4",panel)
        self.assertIn("[REVIEW / SKIP APROBAT]",panel)
        self.assertLess(panel.index("if(!window.confirm(question))"),panel.index("evalR20('validate'"))
        self.assertIn("if(mode.value==='independent')run(k);else if(old)old.call(btn);",panel)
if __name__=='__main__':unittest.main(verbosity=2)
