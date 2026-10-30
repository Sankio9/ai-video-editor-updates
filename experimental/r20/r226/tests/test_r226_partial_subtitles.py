import hashlib,json,sys,tempfile,types,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))

def plan_stub(docx,module,omit_struck=False):
    assert module=="02"
    out=[]
    for i in range(1,20):
        if omit_struck and i==3:continue
        out.append({"groupId":f"CUT-{i:02d}","text":f"Text editorial numărul {i}",
                    "fontStyle":"Regular" if i!=9 else "Italic"})
    return {"items":out,"omittedStrikeCuts":["CUT-03"] if omit_struck else [],
            "strikeCutsChanged":1 if omit_struck else 0,
            "removedStrikeCharacters":15 if omit_struck else 0}
def extract_stub(docx):
    return ([{"ordinal":i,"source_code":"9981" if i%2 else "9931"}
             for i in range(1,20)],[],{})
sys.modules["r20_graphics_plans"]=types.SimpleNamespace(build=plan_stub,_extract=extract_stub)
sys.modules["r171_layout"]=types.SimpleNamespace(clean=lambda x:" ".join(str(x).split()))
import r226_partial_subtitles as R

class Tests(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory()
    self.root=Path(self.tmp.name)
    self.doc=self.root/"case.docx"
    self.doc.write_bytes(b"synthetic private document placeholder")
    self.sha=hashlib.sha256(self.doc.read_bytes()).hexdigest()
    self.identity={"docxSHA256":self.sha,"diagnosticSHA256":"c"*64,"sequenceId":"TEST_SEQ_1"}
    self.cuts=[]
    for i in range(1,20):
        state="PLACEHOLDER" if i<=10 else "CONFIRMED"
        self.cuts.append({"cutId":f"CUT-{i:02d}","sourceCode":"9981" if i%2 else "9931",
            "sourceName":"Original.mov","sourceNodeId":"NODE-1",
            "state":state,"timelineStart":(i-1)*8.,
            "timelineEnd":i*8.,"durationSeconds":8.})
    self.montage={"schema":"aive-r220-montage-plan-v1","phase":"ANALYSIS_ONLY",
       "identity":self.identity,"planSHA256":"d"*64,
       "totalCuts":19,"confirmedCount":9,"placeholderCount":10,"cuts":self.cuts}
    self.report={"schema":"aive-r220-missing-cuts-v1","phase":"POST_READBACK",
       "identity":self.identity,"planSHA256":"d"*64,"confirmedInsertedCount":9,
       "placeholderReservedCount":10,"items":[{"cutId":c["cutId"]} for c in self.cuts[:10]]}
    self.mf=self.root/"mount.json";self.rf=self.root/"readback.json"
    self.persist()
 def tearDown(self):self.tmp.cleanup()
 def persist(self):
    self.mf.write_text(json.dumps(self.montage))
    self.rf.write_text(json.dumps(self.report))
 def build(self,omit=False):
    self.persist()
    return R.build(self.doc,self.mf,self.rf,omit_struck=omit)
 def test_nine_confirmed_ten_reserved_correct_timing(self):
    p=self.build()
    self.assertEqual((p["confirmedCount"],p["reservedCount"],p["totalItems"]),(9,10,9))
    self.assertEqual([x["groupId"] for x in p["items"]],[f"CUT-{i:02d}" for i in range(11,20)])
    self.assertEqual(p["items"][0]["startSeconds"],80.0)
    self.assertEqual(p["items"][0]["durationSeconds"],8.0)
    self.assertEqual(p["timing"],"CUT_ALIGNED_ESTIMATED")
    self.assertTrue(all(x["fontStyle"]=="Regular" for x in p["items"]))
 def test_placeholder_never_subtitled_even_when_text_available(self):
    p=self.build()
    self.assertTrue(all(int(i["groupId"][-2:])>10 for i in p["items"]))
    self.assertEqual(len(p["reservedCuts"]),10)
 def test_accurate_docx_strikethrough_omission(self):
    self.cuts[2]["state"]="CONFIRMED"
    self.cuts[10]["state"]="PLACEHOLDER"
    self.montage["confirmedCount"]=9
    self.montage["placeholderCount"]=10
    self.report["items"]=[{"cutId":c["cutId"]} for c in self.cuts if c["state"]=="PLACEHOLDER"]
    p=self.build(True)
    self.assertIn("CUT-03",p["omittedStrikeCuts"])
    self.assertNotIn("CUT-03",[x["groupId"] for x in p["items"]])
    self.assertEqual(p["removedStrikeCharacters"],15)
 def test_refuses_unconfirmed_montage_readback(self):
    self.report["phase"]="ANALYSIS_ONLY"
    with self.assertRaisesRegex(ValueError,"READBACK_REQUIRED"):self.build()
 def test_refuses_changed_word(self):
    self.doc.write_bytes(b"changed")
    with self.assertRaisesRegex(ValueError,"MONTAGE_DOCX_CHANGED"):self.build()
 def test_refuses_source_code_conflict(self):
    self.cuts[10]["sourceCode"]="0000"
    with self.assertRaisesRegex(ValueError,"SOURCE_CODE_MISMATCH"):self.build()
 def test_refuses_missing_expected_subtitle(self):
    original=sys.modules["r20_graphics_plans"].build
    try:
       R.independent_subtitles=lambda d,m,omit_struck=False:{"items":[],"omittedStrikeCuts":[]}
       with self.assertRaisesRegex(ValueError,"CONFIRMED_CUT_HAS_NO_DOCX_TEXT"):self.build()
    finally:R.independent_subtitles=original
 def test_refuses_too_many_cues_in_short_clip(self):
    self.cuts[10]["timelineEnd"]=self.cuts[10]["timelineStart"]+.5
    with self.assertRaisesRegex(ValueError,"CUT_TOO_SHORT"):self.build()
 def test_no_report_misclassification(self):
    self.report["placeholderReservedCount"]=9
    with self.assertRaisesRegex(ValueError,"READBACK_COUNTS"):self.build()
 def test_persistent_utf8_and_hash(self):
    plan=self.build();out=self.root/"private.json"
    h=R.save(plan,out)
    self.assertEqual(hashlib.sha256(out.read_bytes()).hexdigest(),h)
    self.assertEqual(json.loads(out.read_text("utf8"))["contentSHA256"],plan["contentSHA256"])
if __name__=="__main__":unittest.main()
