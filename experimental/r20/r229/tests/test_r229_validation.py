"""Integration tests: actual R220 capture -> R229 authenticated plan ->
stale report rejected as source of truth, V1/A1 readback remains separate.
No access to Premiere; does not falsely claim host LIVE coverage.
"""
import hashlib,json,os,sys,tempfile,types,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"r220"/"tools"))
sys.path.insert(0,str(ROOT/"r229"/"tools"))
sys.modules["r1911_speech_first"]=types.SimpleNamespace(
    MIN_BOUNDARY_SCORE=.67,MIN_FULL_TEXT_SCORE=.67)
from r220_capture import capture,R220Captured
from r229_validate_r220 import validate

class RealCaptureRegression(unittest.TestCase):
 def setUp(self):
    self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
    self.old=os.environ.get("AIVE_R220_HOME")
    os.environ["AIVE_R220_HOME"]=str(self.root)
    self.doc=self.root/"Bubuieci.docx";self.doc.write_bytes(b"User private DOCX simulated bytes")
    self.clip=self.root/"ANMR_REL9981.MP4";self.clip.write_bytes(b"synthetic video")
    self.seq="PREMIERE_SEQ_BUBUIECI"
    self.media=self.root/"media.json"
    self.media.write_text(json.dumps({"sequenceId":self.seq,
      "sequence":"Bubuieci [AIVE TEST]",
      "media":[{"path":str(self.clip),"name":self.clip.name,"nodeId":"NODE9981","offline":False}]}))
    matched={"status":"AI_MATCHED","source":"9981","startScore":.94,
             "endScore":.91,"fullTextScore":.96,"sourceDuration":120.,
             "finalIn":10.,"finalOut":14.,"rawMatchedIn":10.,"rawMatchedOut":14.}
    weak={"status":"FALLBACK_SCRIPT_TC","source":"9981",
          "matchStatus":"REVIEW_WEAK_BOUNDARY","startScore":.2,
          "endScore":.3,"fullTextScore":.5,"sourceDuration":120.,
          "rawMatchedIn":20.,"rawMatchedOut":27.}
    self.events=[
       {"kind":"cut","id":"CUT-01","sourceCode":"9981","text":"Bună ziua la Bubuieci",
        "asr":matched,"inSeconds":10.,"outSeconds":14.},
       {"kind":"vo_gap","id":"VO-CARD-01","durationSeconds":7.},
       {"kind":"cut","id":"CUT-02","sourceCode":"9981","text":"O declarație încă neidentificată",
        "asr":weak,"inSeconds":20.,"outSeconds":27.}]
    legacy={"events":self.events,"review":[],"aiAnalysis":{"runtime":{"mode":"REAL_AUDIO"}}}
    with self.assertRaises(R220Captured) as e:
        capture(legacy,{"9981":self.clip},self.doc,self.media,self.seq)
    details=e.exception.detail
    self.plan=Path(details["plan"]);self.report=Path(details["report"])
 def tearDown(self):
    if self.old is None:os.environ.pop("AIVE_R220_HOME",None)
    else:os.environ["AIVE_R220_HOME"]=self.old
    self.t.cleanup()
 def read(self):return validate(self.doc,self.plan,self.seq)
 def test_original_capture_can_be_authenticated(self):
    result=self.read()
    self.assertEqual((result["confirmedCount"],result["placeholderCount"],
                     result["voReserveCount"]),(1,1,1))
    self.assertEqual(result["reportTemplate"]["phase"],"ANALYSIS_ONLY")
    self.assertEqual(len(result["reportTemplate"]["items"]),1)
    self.assertEqual(result["reportTemplate"]["items"][0]["cutId"],"CUT-02")
    self.assertEqual(result["planFileSHA256"],hashlib.sha256(self.plan.read_bytes()).hexdigest())
 def test_realistic_corrupt_sidecar_does_not_block_plan_validation(self):
    self.report.write_text(json.dumps({"schema":"OLD","phase":"POST_READBACK",
      "identity":{"sequenceId":"WRONG"},"items":[]}),encoding="utf8")
    x=self.read()
    self.assertEqual(x["confirmedCount"],1)
    self.assertEqual(x["reportTemplate"]["identity"]["sequenceId"],self.seq)
 def test_missing_report_sidecar_does_not_block_plan_validation(self):
    self.report.unlink()
    self.assertEqual(self.read()["placeholderCount"],1)
 def test_invalid_intrinsic_source_plan_sha_rejected(self):
    x=json.loads(self.plan.read_text())
    x["confirmedCount"]=99
    self.plan.write_text(json.dumps(x))
    with self.assertRaisesRegex(ValueError,"R220_PLAN_SHA_CHANGED"):self.read()
 def test_docx_changed_rejected(self):
    self.doc.write_bytes(b"changed DOCX")
    with self.assertRaisesRegex(ValueError,"R220_DOCX_CHANGED"):self.read()
 def test_active_sequence_changed_rejected(self):
    with self.assertRaisesRegex(ValueError,"R220_SEQUENCE_CHANGED"):
        validate(self.doc,self.plan,"OTHER_SEQUENCE")
 def test_valid_rehashed_plan_with_source_range_conflict_rejected(self):
    from r220_montage_plan import digest
    x=json.loads(self.plan.read_text())
    x["cuts"][0]["sourceOut"]=30.
    x["planSHA256"]=digest({k:v for k,v in x.items() if k!="planSHA256"})
    self.plan.write_text(json.dumps(x))
    with self.assertRaisesRegex(ValueError,"R220_CONFIRMED_SOURCE_INVALID"):self.read()
 def test_placeholders_cannot_have_reporter_fallback_source(self):
    from r220_montage_plan import digest
    x=json.loads(self.plan.read_text())
    x["cuts"][-1]["sourceIn"]=20.
    x["planSHA256"]=digest({k:v for k,v in x.items() if k!="planSHA256"})
    self.plan.write_text(json.dumps(x))
    with self.assertRaisesRegex(ValueError,"R220_PLACEHOLDER_INVALID"):self.read()
if __name__=="__main__":unittest.main()
