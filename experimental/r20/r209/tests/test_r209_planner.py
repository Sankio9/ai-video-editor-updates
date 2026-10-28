"""R2.0.9 integrated planner + R2.0.7 unchanged generator synthetic tests. Stub ONLY missing legacy parser imports;
the actual R2.0.7 plan generator and Word formatting filter run together.
"""
from __future__ import annotations
import hashlib,importlib.util,sys,tempfile,types,unittest
from pathlib import Path
from docx import Document

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"candidate"/"tools"))
STUBS={
    'reportaj_r1_parse_docx':{'extract':lambda p:None},
    'r193_docx_reader':{'read':lambda p:None},
    'r161_prepare_nametags':{'card_for':lambda x:None},
    'r171_layout':{'clean':lambda s:' '.join(str(s).split())},
    'r204_carton_layout':{'build_pages':lambda s:[{'text':s,'physicalLines':['','','',s],
                                      'boldWords':{str(i):'' for i in range(4)},'emphasisPhrases':[]}]},
    'r153_prepare':{'split_balanced':lambda s,n:[s] if len(s)<=n else
                    [s[:n].rsplit(' ',1)[0],s[len(s[:n].rsplit(' ',1)[0])+1:]]},
}
for key,entries in STUBS.items():
    mod=types.ModuleType(key)
    for name,func in entries.items():setattr(mod,name,func)
    sys.modules[key]=mod
spec=importlib.util.spec_from_file_location('r207_graphics',ROOT.parent/"r207"/"candidate"/"tools"/"r20_graphics_plans.py")
planner=importlib.util.module_from_spec(spec);spec.loader.exec_module(planner)

class R209Integrated(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/"Editorial.docx"
        self.doc=Document()
    def tearDown(self):self.tmp.cleanup()
    def prepare(self,segments,graphics=None):
        self.doc.save(self.path)
        # Generator imported the functions by value: patch its module globals,
        # not only the stub package attributes.
        planner.extract=lambda p:{'segments':segments,'graphics':graphics or []}
        planner.read_r193=lambda p:{'segments':[],'captions':[]}

    @staticmethod
    def cut(i,p,text,italic=False):
        return {'ordinal':i,'paragraph_start':p,'paragraph_end':p,
                'source_code':'9981','text':text,'reporter_italic':italic}
    def test_end_to_end_include_vs_omit(self):
        p=self.doc.add_paragraph()
        p.add_run('Vreau să mă dezvolt în profesia dată. ').font.strike=True
        p.add_run('Unde ai vrea să muncești? ').italic=True
        p.add_run('Să fiu bucătar în Anglia.')
        self.prepare([self.cut(2,0,p.text,italic=True)])
        before=hashlib.sha256(self.path.read_bytes()).hexdigest()
        full=planner.build(self.path,'02',omit_struck=False)
        short=planner.build(self.path,'02',omit_struck=True)
        self.assertIn('Vreau să mă dezvolt', ' '.join(x['text'] for x in full['items']))
        self.assertNotIn('Vreau să mă dezvolt',' '.join(x['text'] for x in short['items']))
        self.assertEqual(' '.join(x['text'] for x in short['items']),
                         'Unde ai vrea să muncești? Să fiu bucătar în Anglia.')
        self.assertEqual(full['strikePolicy'],'INCLUDE_STRUCK')
        self.assertEqual(short['strikePolicy'],'OMIT_STRUCK')
        self.assertTrue(all(x['fontStyle']=='Italic' for x in short['items']))
        self.assertEqual(before,hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(short['docx_sha256'],before)
        self.assertEqual(short['timing'],'SCRIPT_PREVIEW')
        self.assertEqual(short['omittedStrikeCuts'],[])
    def test_entire_struck_segment_skipped_and_next_kept(self):
        a=self.doc.add_paragraph()
        a.add_run('Replică tăiată.').font.strike=True
        b=self.doc.add_paragraph('Textul bun rămâne.')
        self.prepare([self.cut(1,0,a.text),self.cut(2,1,b.text)])
        output=planner.build(self.path,'02',omit_struck=True)
        self.assertEqual(output['omittedStrikeCuts'],['CUT-01'])
        self.assertEqual(len(output['items']),1)
        self.assertEqual(output['items'][0]['groupId'],'CUT-02')
        self.assertEqual(output['removedStrikeCharacters'],len('Replicătăiată.'))
    def test_module04_untouched_by_strike_flag(self):
        self.doc.add_paragraph('Așa rămâne.')
        self.prepare([self.cut(1,0,'Așa rămâne.')],[{'text':'CARTON','paragraph':0}])
        a=planner.build(self.path,'04',omit_struck=False)
        b=planner.build(self.path,'04',omit_struck=True)
        self.assertEqual(a['items'],b['items'])
        self.assertEqual(a['strikePolicy'],'NOT_APPLICABLE')
        self.assertEqual(b['strikePolicy'],'NOT_APPLICABLE')
        self.assertEqual(a['items'][0]['text'],'CARTON')
    def test_zero_crossed_with_enabled_checkbox_stops_all_insertion(self):
        p=self.doc.add_paragraph("Un text simplu, neformatat.")
        self.prepare([self.cut(1,0,p.text)])
        with self.assertRaisesRegex(ValueError,"STRIKETHROUGH_NOT_DETECTED"):
            planner.build(self.path,'02',omit_struck=True)

    def test_inherited_style_keeps_reporter_italic(self):
        from docx.enum.style import WD_STYLE_TYPE
        style=self.doc.styles.add_style("Crossed Word Style",WD_STYLE_TYPE.CHARACTER)
        style.font.strike=True
        p=self.doc.add_paragraph()
        crossed=p.add_run("De omis. ");crossed.style=style
        remaining=p.add_run("Ce se întâmplă? ");remaining.italic=True
        p.add_run("Răspunsul rămâne.")
        self.prepare([self.cut(2,0,p.text,italic=True)])
        plan=planner.build(self.path,'02',omit_struck=True)
        self.assertEqual(' '.join(item['text'] for item in plan['items']),
                         'Ce se întâmplă? Răspunsul rămâne.')
        self.assertEqual(plan['strikePolicy'],'OMIT_STRUCK')
        self.assertEqual(plan['strikeCutsChanged'],1)

    def test_ambiguous_style_does_not_generate_subtitles(self):
        self.doc.add_paragraph('Replica este diferită.')
        self.prepare([self.cut(1,0,'Nu există această propoziție.')])
        with self.assertRaisesRegex(ValueError,'STRIKE_FORMAT_AMBIGUOUS'):
            planner.build(self.path,'02',omit_struck=True)

if __name__=='__main__':unittest.main(verbosity=2)
