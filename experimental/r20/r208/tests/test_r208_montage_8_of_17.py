"""R2.0.8 montage recovery regression from anonymized 8/17 panel failure.

Only CUT codes/review categories copied from the screenshot, NO editorial text,
ASR transcript, media file or person names. The plan is always non-destructive.
"""
from __future__ import annotations

import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"r206"/"tools"))
from r206_selective_asr import build,SCHEMA_IN,SCHEMA_OUT

SOURCE_DURATION={'9931':110.4,'9980':144.48,'9930':154.56,
                 '9937':130.08,'9974':88.32}

def ev(i,code,kind,start):
    a={"matchStatus":kind,"sourceDuration":SOURCE_DURATION[code],
       "source":code,"rawMatchedIn":start,"rawMatchedOut":start+7}
    return {"id":"CUT-%02d"%i,"sourceCode":code,
            "scriptIn":start+15,"scriptOut":start+22,"asr":a}

class TestR208PanelRecovery(unittest.TestCase):
    def test_rescan_targets_all_8_rejections_without_cutting(self):
        evidence=[
            ev(1,'9931','REVIEW_WEAK_BOUNDARY',5),
            ev(2,'9931','REVIEW_WEAK_BOUNDARY',40),
            ev(4,'9980','REVIEW_WEAK_BOUNDARY',32),
            ev(5,'9930','REVIEW_WEAK_BOUNDARY',10),
            ev(6,'9930','REVIEW_WEAK_BOUNDARY',42),
            ev(15,'9937','REVIEW_WEAK_BOUNDARY',85),
            ev(16,'9974','REVIEW_NO_MATCH',20),
            ev(17,'9974','REVIEW_NO_MATCH',61),
        ]
        result=build({"schema":SCHEMA_IN,"events":evidence})
        self.assertEqual(result["schema"],SCHEMA_OUT)
        self.assertEqual(result["summary"]["flaggedEvents"],8)
        self.assertEqual(result["summary"]["rescanSources"],5)
        self.assertEqual(result["blocked"],[])
        self.assertFalse(result["automaticCuttingAllowed"])
        self.assertFalse(result["safeToModifyPremiereTimeline"])
        self.assertFalse(result["reporterTimecodeUsedForCutting"])
        self.assertTrue(result["requiresNewASRAndEditorialValidation"])
        all_cuts={cut for source in result["rescans"] for w in source["windows"] for cut in w["cutIds"]}
        self.assertEqual(all_cuts,{e["id"] for e in evidence})
        amb=[s for s in result["rescans"] if s["sourceCode"]=="9974"]
        self.assertEqual(amb[0]["priority"],"HIGH")
        self.assertEqual(len(amb[0]["windows"]),1)
        self.assertEqual((amb[0]["windows"][0]["startSeconds"],amb[0]["windows"][0]["endSeconds"]),
                         (0,88.32))
        self.assertEqual(sorted(amb[0]["windows"][0]["cutIds"]),["CUT-16","CUT-17"])
        self.assertNotIn("proposedIn",str(result))
        self.assertNotIn("finalIn",str(result))
    def test_partial_old_diagnostic_not_substituted_for_current(self):
        # The prior full diagnostic from Library has 19 events; the screenshot
        # explicitly says 8/17 for the *current* run. The two are not identical.
        old={"schema":SCHEMA_IN,"events":[ev(1,'9931','REVIEW_WEAK_BOUNDARY',5)]}
        new={"schema":SCHEMA_IN,"events":[ev(1,'9931','REVIEW_WEAK_BOUNDARY',5),
                                          ev(17,'9974','REVIEW_NO_MATCH',45)]}
        first=build(old);second=build(new)
        self.assertNotEqual(first["summary"]["flaggedEvents"],second["summary"]["flaggedEvents"])
        self.assertNotEqual(first["summary"]["rescanSources"],second["summary"]["rescanSources"])
        self.assertFalse(second["automaticCuttingAllowed"])

if __name__=="__main__":unittest.main(verbosity=2)
