"""R2.2 synthetic plan, approval and missing-media report. NO Premiere writes."""
from __future__ import annotations
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from r220_montage_plan import build,decide,verify_readback,save_private_report,REPORT_SCHEMA

HASH="a"*64
CTX={"docxSHA256":HASH,"diagnosticSHA256":"b"*64,"sequenceId":"TEST_SEQ_03"}
MISSING={1,2,4,5,6,7,8,17,18,19}
CODES={"01":"9931","02":"9931","04":"9980","05":"9930","06":"9930",
       "07":"9930","08":"9981","17":"9937","18":"9974","19":"9974"}
def fixture(n=19):
    ev=[];media={}
    for i in range(1,n+1):
        cut="CUT-%02d"%i;code=CODES.get("%02d"%i,"9981")
        media[code]={"state":"ONLINE","name":"Original_"+code+".mov","nodeId":"PROJECT_NODE_"+code}
        review=i in MISSING
        status=("REVIEW_NO_MATCH" if i in (18,19) else
                "REVIEW_WEAK_TRANSCRIPT" if i==8 else
                "REVIEW_WEAK_BOUNDARY" if review else "AI_MATCHED")
        asr={"source":code,"sourceDuration":200.,
             "matchStatus":status,"rawMatchedIn":float(i*2),
             "rawMatchedOut":float(i*2+6),
             "finalIn":float(i*2),"finalOut":float(i*2+6)}
        ev.append({"id":cut,"sourceCode":code,"scriptIn":float(i*2),
                   "scriptOut":float(i*2+6),"dialogueWordCount":18,
                   "asr":asr})
    safe=[r["id"] for r in ev if r["asr"]["matchStatus"]=="AI_MATCHED"]
    return {"schema":"aive-match-diagnostic-v1","events":ev},media,safe

class PlanTests(unittest.TestCase):
    def setUp(self):self.d,self.media,self.safe=fixture()
    def make(self):return build(self.d,CTX,self.media,self.safe)
    def test_9_confirmed_10_reserved_with_missing_source_codes(self):
        p,r=self.make()
        self.assertEqual((p["totalCuts"],p["confirmedCount"],p["placeholderCount"]),(19,9,10))
        self.assertTrue(p["approvalRequired"])
        self.assertFalse(p["safeToModifyPremiereTimeline"])
        self.assertFalse(p["reporterTimecodeUsedForCutting"])
        self.assertEqual(len(r["items"]),10)
        self.assertEqual(r["phase"],"ANALYSIS_ONLY")
        self.assertEqual([x["cutId"] for x in r["items"]],
                         ["CUT-%02d"%i for i in sorted(MISSING)])
    def test_shared_9974_media_not_two_distinct_missing_files(self):
        p,r=self.make()
        rows=[x for x in r["items"] if x["sourceCode"]=="9974"]
        self.assertEqual(len(rows),2)
        self.assertEqual(set(x["reason"] for x in rows),{"AUDIO_NOT_FOUND"})
        self.assertEqual(r["missingDistinctSourceCodes"],[])
    def test_confirmed_audio_real_bounds_only(self):
        p,_=self.make()
        confirmed=[x for x in p["cuts"] if x["state"]=="CONFIRMED"]
        self.assertTrue(all(x["sourceIn"]<x["sourceOut"] for x in confirmed))
        self.assertTrue(all(x["durationKind"]=="AUDIO_VERIFIED" for x in confirmed))
        self.assertTrue(all("sourceIn" not in x and "sourceOut" not in x
                            for x in p["cuts"] if x["state"]=="PLACEHOLDER"))
    def test_plan_is_contiguous_and_preserves_docx_order(self):
        p,_=self.make()
        self.assertEqual([x["cutId"] for x in p["cuts"]],
                         ["CUT-%02d"%i for i in range(1,20)])
        self.assertTrue(all(p["cuts"][i]["timelineEnd"]==
                            p["cuts"][i+1]["timelineStart"] for i in range(18)))
    def test_weak_asr_estimate_is_not_a_final_source_cut(self):
        p,r=self.make()
        r0=r["items"][0]
        self.assertEqual(r0["durationKind"],"ESTIMATED_WEAK_ASR")
        self.assertEqual(r0["durationSeconds"],6.)
        self.assertNotIn("sourceIn",r0)
    def test_unreasonable_one_second_tc_ignored(self):
        self.d["events"][3]["scriptOut"]=self.d["events"][3]["scriptIn"]+1.
        p,_=self.make()
        self.assertEqual(p["cuts"][3]["durationSeconds"],6.)
        self.assertFalse(p["reporterTimecodeUsedForCutting"])
    def test_missing_source_is_a_distinct_reason_and_counted_once(self):
        self.media["9974"]={"state":"MISSING"}
        p,r=self.make()
        rows=[x for x in r["items"] if x["sourceCode"]=="9974"]
        self.assertEqual({x["reason"] for x in rows},{"SOURCE_NOT_FOUND"})
        self.assertEqual(r["missingDistinctSourceCodes"],["9974"])
    def test_offline_source_is_not_misclassified_as_audio_missing(self):
        self.media["9974"]={"state":"OFFLINE","name":"Original_9974.mov"}
        _,r=self.make()
        self.assertEqual({x["reason"] for x in r["items"] if x["sourceCode"]=="9974"},
                         {"SOURCE_OFFLINE"})
    def test_ambiguous_media_stops_without_plan(self):
        self.media["9974"]={"state":"AMBIGUOUS"}
        with self.assertRaisesRegex(ValueError,"AMBIGUOUS_SOURCE_STOP"):
            self.make()
    def test_unknown_match_status_stops(self):
        self.d["events"][0]["asr"]["matchStatus"]="UNKNOWN"
        with self.assertRaisesRegex(ValueError,"UNKNOWN_MATCH_STATUS_STOP"):
            self.make()
    def test_fake_matched_not_trusted_without_safe_validator(self):
        self.safe.remove("CUT-03")
        p,r=self.make()
        row=[x for x in r["items"] if x["cutId"]=="CUT-03"][0]
        self.assertEqual(row["reason"],"ASR_REQUIRES_VALIDATION")
        self.assertNotIn("sourceIn",row)
    def test_no_problems_needs_no_extra_prompt(self):
        d,m,v=fixture(1)
        p,r=build(d,CTX,m,v)
        self.assertEqual(p["confirmedCount"],0) # fixture #1 has review
        d["events"][0]["asr"]["matchStatus"]="AI_MATCHED"
        p,r=build(d,CTX,m,["CUT-01"])
        self.assertFalse(p["approvalRequired"])
        self.assertEqual(r["items"],[])
        self.assertEqual(decide(p,p["planSHA256"],CTX["sequenceId"],
                                "COMPLETE_AFTER_PREFLIGHT")["decision"],"PENDING_LIVE_PREFLIGHT")
    def test_real_r1913_diagnostic_schema_uses_asr_status_and_scriptText(self):
        for e in self.d["events"]:
            e["asr"]["status"]=e["asr"].pop("matchStatus")
            e["scriptText"]="Acesta este un exemplu sintetic cu suficiente cuvinte."
            e.pop("dialogueWordCount")
        p,r=self.make()
        self.assertEqual((p["confirmedCount"],p["placeholderCount"]),(9,10))
        self.assertEqual({x["reason"] for x in r["items"] if x["sourceCode"]=="9974"},
                         {"AUDIO_NOT_FOUND"})
    def test_conflicting_status_fields_are_blocked(self):
        self.d["events"][0]["asr"]["status"]="AI_MATCHED"
        with self.assertRaisesRegex(ValueError,"CONTRADICTORY_ASR_STATUS_STOP"):
            self.make()
    def test_user_stops_without_authorization(self):
        p,_=self.make()
        self.assertFalse(decide(p,p["planSHA256"],CTX["sequenceId"],"STOP")["writeAuthorized"])
    def test_partial_cannot_continue_without_explicit_choice(self):
        p,_=self.make()
        with self.assertRaisesRegex(ValueError,"EXPLICIT_APPROVAL"):
            decide(p,p["planSHA256"],CTX["sequenceId"],"COMPLETE_AFTER_PREFLIGHT")
        approved=decide(p,p["planSHA256"],CTX["sequenceId"],"CONTINUE_WITH_PLACEHOLDERS")
        self.assertFalse(approved["writeAuthorized"]) # still needs live preflight
        self.assertEqual(approved["decision"],"PENDING_LIVE_PREFLIGHT")
    def test_plan_change_requires_reapproval(self):
        p,_=self.make()
        p["cuts"][0]["durationSeconds"]=888
        with self.assertRaisesRegex(ValueError,"PLAN_CHANGED_STOP"):
            decide(p,p["planSHA256"],CTX["sequenceId"],"CONTINUE_WITH_PLACEHOLDERS")
    def test_sequence_switch_requires_reapproval(self):
        p,_=self.make()
        with self.assertRaisesRegex(ValueError,"SEQUENCE_OR_PLAN_CHANGED_STOP"):
            decide(p,p["planSHA256"],"OTHER_SEQ","CONTINUE_WITH_PLACEHOLDERS")
    def test_readback_is_only_success_source(self):
        p,r=self.make()
        with self.assertRaisesRegex(ValueError,"READBACK_OBJECT_MISMATCH"):
            verify_readback(p,r,[],[],CTX["sequenceId"])
        clips=[x["cutId"] for x in p["cuts"] if x["state"]=="CONFIRMED"]
        markers=[x["cutId"] for x in p["cuts"] if x["state"]=="PLACEHOLDER"]
        result=verify_readback(p,r,clips,markers,CTX["sequenceId"])
        self.assertEqual(result["phase"],"POST_READBACK")
        self.assertEqual((result["confirmedInsertedCount"],result["placeholderReservedCount"]),(9,10))
    def test_local_report_atomic_and_private(self):
        _,r=self.make()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"sequence"/"missing_sources_report.json"
            save_private_report(r,path)
            self.assertEqual(json.loads(path.read_text("utf8"))["schema"],REPORT_SCHEMA)
            self.assertFalse(path.with_name(path.name+".tmp").exists())
    def test_no_diagnostic_transcript_leaks_into_report(self):
        self.d["events"][0]["text"]="PRIVATE INTERVIEW TRANSCRIPT"
        _,r=self.make()
        self.assertNotIn("PRIVATE INTERVIEW TRANSCRIPT",json.dumps(r))
if __name__=="__main__":unittest.main(verbosity=2)
