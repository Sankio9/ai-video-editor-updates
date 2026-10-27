"""R2.0.6 synthetic tests: no private DOCX/media/transcript in public CI."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from r206_selective_asr import build,run,merge,SCHEMA_IN,SCHEMA_OUT

def ev(n,source,status,duration=90,in_tc=18,out_tc=24,raw_in=17,raw_out=24,secret=None):
    return {
        "id":"CUT-%02d"%n,"sourceCode":source,
        "scriptText": secret or "SENZITIV NU EXPORTA",
        "scriptIn":in_tc,"scriptOut":out_tc,
        "asr":{"matchStatus":status,"status":"FALLBACK_SCRIPT_TC",
               "sourceDuration":duration,"rawMatchedIn":raw_in,"rawMatchedOut":raw_out,
               "startHeard":"PRIVATE ASR WORDS", "endHeard":"PRIVATE AUDIO"}}
def diag(*events):return {"schema":SCHEMA_IN,"sourceDocx":r"E:\private.docx","events":list(events)}

class TestR206(unittest.TestCase):
    def test_two_no_matches_same_source_one_full_retranscribe(self):
        result=build(diag(ev(1,'9974','REVIEW_NO_MATCH',88.32),
                          ev(2,'9974','REVIEW_NO_MATCH',88.32,in_tc=68,out_tc=75)))
        self.assertEqual(result["summary"]["flaggedEvents"],2)
        self.assertEqual(len(result["rescans"]),1)
        self.assertEqual(len(result["rescans"][0]["windows"]),1)
        w=result["rescans"][0]["windows"][0]
        self.assertEqual((w["startSeconds"],w["endSeconds"]),(0.0,88.32))
        self.assertEqual(w["cutIds"],["CUT-01","CUT-02"])
        self.assertEqual(result["rescans"][0]["priority"],"HIGH")
        self.assertFalse(result["safeToModifyPremiereTimeline"])
        self.assertFalse(result["automaticCuttingAllowed"])
        self.assertFalse(result["reporterTimecodeUsedForCutting"])

    def test_weak_boundary_uses_asr_anchor_for_search_not_reporter_tc(self):
        x=ev(1,'9931','REVIEW_WEAK_BOUNDARY',110.4,in_tc=90,out_tc=98,raw_in=11.8,raw_out=18.4)
        s=build(diag(x))["rescans"][0]["windows"][0]
        self.assertEqual(s["methods"],["AROUND_ASR_CANDIDATE"])
        self.assertEqual(s["startSeconds"],0.0)
        self.assertEqual(s["endSeconds"],38.4)
        self.assertNotEqual(s["startSeconds"],90.0)

    def test_no_asr_anchor_tc_hint_only_no_cut(self):
        s=build(diag(ev(1,'9930','REVIEW_WEAK_BOUNDARY',600,200,207,None,None)))
        a=s["rescans"][0]["windows"][0]
        self.assertEqual(a["methods"],["REPORTER_TC_SEARCH_HINT"])
        self.assertEqual((a["startSeconds"],a["endSeconds"]),(110.0,297.0))
        self.assertFalse(s["automaticCuttingAllowed"])

    def test_weak_transcript_full_if_eight_minutes_or_less(self):
        s=build(diag(ev(1,'9981','REVIEW_WEAK_TRANSCRIPT',480)))
        self.assertEqual(s["rescans"][0]["windows"][0]["methods"],["FULL_SOURCE"])
        self.assertEqual(s["rescans"][0]["windows"][0]["endSeconds"],480.0)
        self.assertEqual(s["rescans"][0]["priority"],"HIGH")

    def test_over_eight_minutes_without_timing_is_blocked(self):
        s=build(diag(ev(1,'9936','REVIEW_NO_MATCH',480.01,in_tc=None,out_tc=None,
                        raw_in=None,raw_out=None)))
        self.assertEqual(s["rescans"],[])
        self.assertEqual(s["blocked"][0]["cutIds"],["CUT-01"])
        self.assertEqual(s["blocked"][0]["requiredAction"],"EDITORIAL_SOURCE_REVIEW")

    def test_untimed_short_source_entire_source(self):
        s=build(diag(ev(1,'9936','REVIEW_WEAK_BOUNDARY',479.9,None,None,200,230)))
        self.assertEqual(s["rescans"][0]["windows"][0]["methods"],["FULL_SOURCE"])

    def test_suggested_not_rescanned_and_no_fake_success(self):
        s=build(diag(ev(1,'9980','REVIEW_SUGGESTED'),
                     ev(2,'9980','REVIEW_WEAK_BOUNDARY',90,35,42,34,44)))
        self.assertEqual(s["summary"]["flaggedEvents"],1)
        self.assertEqual(s["summary"]["skippedSuggestedForAudit"],1)
        self.assertNotIn("safeToCut",json.dumps(s))
        self.assertEqual(s["summary"]["statusCounts"]["REVIEW_SUGGESTED"],1)

    def test_merge_neighbours_and_preserve_cut_ids(self):
        s=build(diag(ev(1,'9930','REVIEW_WEAK_BOUNDARY',130,20,28,20,25),
                     ev(2,'9930','REVIEW_WEAK_BOUNDARY',130,45,49,47,54)))
        w=s["rescans"][0]["windows"]
        self.assertEqual(len(w),1)
        self.assertEqual(w[0]["cutIds"],["CUT-01","CUT-02"])

    def test_source_duration_conflict_stop(self):
        with self.assertRaisesRegex(ValueError,"Conflicting durations"):
            build(diag(ev(1,'9930','REVIEW_NO_MATCH',90),
                       ev(2,'9930','REVIEW_NO_MATCH',95)))

    def test_duplicate_cut_stop(self):
        with self.assertRaisesRegex(ValueError,"Duplicate CUT"):
            build(diag(ev(1,'9930','REVIEW_NO_MATCH'),
                       ev(1,'9931','REVIEW_NO_MATCH')))

    def test_source_code_not_four_digits_stop(self):
        with self.assertRaisesRegex(ValueError,"source code"):
            build(diag(ev(1,'999900','REVIEW_NO_MATCH')))

    def test_no_export_private_text_and_atomic_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/"input.json";o=Path(tmp)/"output.json"
            d.write_text(json.dumps(diag(ev(1,'9930','REVIEW_NO_MATCH',30,
                                          secret="STRICTLY CONFIDENTIAL DOCX"))),encoding="utf8")
            result=run(d,o)
            saved=o.read_text("utf8")
            self.assertEqual(result["schema"],SCHEMA_OUT)
            for forbidden in ("STRICTLY CONFIDENTIAL DOCX","PRIVATE ASR WORDS",
                              "PRIVATE AUDIO",r"E:\private.docx"):
                self.assertNotIn(forbidden,saved)
            self.assertFalse((Path(tmp)/"output.json.tmp").exists())
            self.assertEqual(json.loads(saved)["sourceDiagnosticSHA256"],result["sourceDiagnosticSHA256"])

    def test_never_overwrite_original_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/"input.json";d.write_text(json.dumps(diag(ev(1,'9930','REVIEW_NO_MATCH'))),"utf8")
            before=d.read_bytes()
            with self.assertRaisesRegex(ValueError,"overwrite original"):
                run(d,d)
            self.assertEqual(d.read_bytes(),before)

    def test_reject_nan_and_false_duration(self):
        for length in [float('nan'),False,0,-1,90000]:
            with self.subTest(duration=length):
                with self.assertRaisesRegex(ValueError,"duration"):
                    build(diag(ev(1,'9930','REVIEW_NO_MATCH',length)))

    def test_missing_asr_fails_closed(self):
        e=ev(1,'9930','REVIEW_NO_MATCH');e.pop('asr')
        with self.assertRaisesRegex(ValueError,"ASR diagnostic missing"):
            build(diag(e))

if __name__=="__main__":
    unittest.main(verbosity=2)
