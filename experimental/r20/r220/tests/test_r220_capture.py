"""R2.2: full legacy R143 plan capture preserves VO and rejects TC fallback."""
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"tools"
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path(__file__).resolve().parents[5]/"scripts"))
from r220_capture import capture,R220Captured

def make_plan(matched=True,with_voice=True):
    good={"status":"AI_MATCHED","source":"9981","startScore":.92,
         "endScore":.93,"fullTextScore":.92,"sourceDuration":120.,
         "finalIn":10.,"finalOut":15.,"rawMatchedIn":10.,"rawMatchedOut":15.}
    bad={"status":"FALLBACK_SCRIPT_TC","source":"9981","matchStatus":"REVIEW_WEAK_BOUNDARY",
         "startScore":.11,"endScore":.4,"fullTextScore":.44,"sourceDuration":120.,
         "finalIn":33.,"finalOut":36.,"rawMatchedIn":32.,"rawMatchedOut":38.}
    events=[{"id":"CUT-01","kind":"cut","sourceCode":"9981","text":"Bună ziua tuturor la școală.",
             "asr":good,"inSeconds":10,"outSeconds":15}]
    if with_voice:events.append({"id":"VO-CARD-01","kind":"vo","text":"VO editorial"})
    events.append({"id":"CUT-02","kind":"cut","sourceCode":"9981","text":"Vreau să învăț o meserie.",
                   "asr":good.copy() if matched else bad,"inSeconds":33,"outSeconds":36})
    if matched:
        events[-1]["asr"]["finalIn"]=30.;events[-1]["asr"]["finalOut"]=35.
    return {"events":events,"review":[],"aiAnalysis":{"runtime":{"mode":"REAL_AUDIO"}}}

class CaptureTests(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory()
    self.path=Path(self.tmp.name)
    self.docx=self.path/"original.docx"
    self.docx.write_bytes(b"synthetic editable docx content marker")
    self.clip=self.path/"Original_9981.mov"
    self.clip.write_bytes(b"synthetic clip marker")
    self.seq="TEST_SEQ_03"
    self.manifest=self.path/"inventory.json"
    self.manifest.write_text(json.dumps({
      "sequenceId":self.seq,"sequence":"Copied project [AIVE TEST]",
      "media":[{"path":str(self.clip),"name":"Original_9981.mov","nodeId":"NODE_9981","offline":False}]
    }),encoding="utf8")
    import os
    self.old_home=os.environ.get("AIVE_R220_HOME")
    os.environ["AIVE_R220_HOME"]=str(self.path)
 def tearDown(self):
    import os
    if self.old_home is None:os.environ.pop("AIVE_R220_HOME",None)
    else:os.environ["AIVE_R220_HOME"]=self.old_home
    self.tmp.cleanup()
 def analyze(self,plan):
    with self.assertRaises(R220Captured) as cap:
        capture(plan,{"9981":self.clip},self.docx,self.manifest,self.seq)
    details=cap.exception.detail
    return details,json.loads(Path(details["plan"]).read_text("utf8")),json.loads(Path(details["report"]).read_text("utf8"))
 def test_partial_with_editorial_vo(self):
    d,p,r=self.analyze(make_plan(matched=False))
    self.assertEqual(p["totalCuts"],2)
    self.assertEqual((p["confirmedCount"],p["placeholderCount"],p["voReserveCount"]),(1,1,1))
    self.assertEqual([x["state"] for x in p["cuts"]],["CONFIRMED","VO_RESERVE","PLACEHOLDER"])
    self.assertEqual(p["cuts"][0]["sourceNodeId"],"NODE_9981")
    self.assertEqual(p["cuts"][0]["timelineStart"],0.)
    self.assertEqual(p["cuts"][1]["durationSeconds"],7.)
    self.assertEqual(p["cuts"][2]["timelineStart"],12.)
    self.assertNotIn("sourceIn",p["cuts"][2])
    self.assertEqual(r["items"][0]["reason"],"ASR_WEAK_BOUNDARY")
    self.assertEqual(r["phase"],"ANALYSIS_ONLY")
 def test_zero_problems_hides_approval(self):
    d,p,r=self.analyze(make_plan())
    self.assertFalse(p["approvalRequired"])
    self.assertEqual(p["confirmedCount"],2)
    self.assertEqual(len(r["items"]),0)
 def test_r143_unknown_editorial_kind_stops(self):
    plan=make_plan();plan["events"][1]["kind"]="danger"
    with self.assertRaisesRegex(ValueError,"UNKNOWN_EDITORIAL_EVENT_KIND"):
      capture(plan,{"9981":self.clip},self.docx,self.manifest,self.seq)
 def test_copy_protection(self):
    src=json.loads(self.manifest.read_text("utf8"));src["sequence"]="Production"
    self.manifest.write_text(json.dumps(src),encoding="utf8")
    with self.assertRaisesRegex(ValueError,"COPY_SEQUENCE_REQUIRED"):
      capture(make_plan(),{"9981":self.clip},self.docx,self.manifest,self.seq)
 def test_no_real_audio_blocks(self):
    plan=make_plan();plan["aiAnalysis"]["runtime"]["mode"]="SCRIPT_TC"
    with self.assertRaisesRegex(ValueError,"REQUIRES_REAL_ASR"):
      capture(plan,{"9981":self.clip},self.docx,self.manifest,self.seq)
 def test_unmounted_docx_segments_stop(self):
    plan=make_plan();plan["review"]=[{"id":"CUT-23"}]
    with self.assertRaisesRegex(ValueError,"UNMOUNTED_DOCX"):
      capture(plan,{"9981":self.clip},self.docx,self.manifest,self.seq)
if __name__=="__main__":unittest.main(verbosity=2)
