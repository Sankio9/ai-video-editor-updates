"""R2.1.3 montage second-pass synthetic tests, no private media."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"candidate"/"tools"))
from r213_second_pass import recover,norm,MATCHER_VERSION

TEXT="Vreau să învăț o profesie deoarece în viitor voi lucra cu plăcere într-o bucătărie profesională"
def event(text=TEXT,start=25,end=34):
    return {"id":"CUT-01","sourceCode":"9931","text":text,
            "inSeconds":start,"outSeconds":end}
def words(text=TEXT,at=25):
    return [{"word":" "+w,"start":at+i*.47,"end":at+i*.47+.4}
            for i,w in enumerate(text.split())]
BAD={"status":"REVIEW_WEAK_BOUNDARY","reason":"Boundary weak",
     "startScore":.12,"endScore":.16,"fullTextScore":.4}
class SpeechTests(unittest.TestCase):
    def test_unique_speech_proposes_only_review_suggested(self):
        r=recover(event(),words(),BAD.copy())
        self.assertEqual(r["status"],"REVIEW_SUGGESTED")
        self.assertEqual(r["matchMethod"],MATCHER_VERSION)
        self.assertGreaterEqual(r["fullTextScore"],.88)
        self.assertEqual(r["proposedIn"],25.)
        self.assertGreater(r["proposedOut"],25.)
        self.assertNotEqual(r["status"],"AI_MATCHED")
    def test_romanian_diacritics(self):
        self.assertEqual(norm("Școală țară, șapte!"),["scoala","tara","sapte"])
        w=words(TEXT.replace("ă","a").replace("â","a").replace("î","i").replace("ș","s").replace("ț","t"))
        self.assertEqual(recover(event(),w,BAD.copy())["status"],"REVIEW_SUGGESTED")
    def test_zero_audio_words_stays_uncertain(self):
        self.assertEqual(recover(event(),[],BAD.copy()),BAD)
    def test_only_middle_phrase_fails_anchors(self):
        self.assertEqual(recover(event(),words(" ".join(TEXT.split()[2:-2])),BAD.copy()),BAD)
    def test_repeated_quote_requires_review(self):
        source=words(at=25)+words(at=62)
        self.assertEqual(recover(event(),source,BAD.copy())["status"],
                         "REVIEW_ALTERNATIVE_OCCURRENCE")
    def test_accepted_original_untouched(self):
        original={"status":"REVIEW_SUGGESTED","proposedIn":12}
        self.assertIs(recover(event(),words(),original),original)
    def test_no_timecode_fallback_with_empty_transcript(self):
        self.assertEqual(recover(event(start=95,end=100),[],BAD.copy()),BAD)
    def test_large_drift_stops_even_if_speech_matches(self):
        self.assertEqual(recover(event(),words(at=110),BAD.copy()),BAD)
    def test_outside_ninety_second_search_hints_stops(self):
        self.assertEqual(recover(event(start=300,end=310),words(at=25),BAD.copy()),BAD)
    def test_untimed_remains_separate_policy(self):
        e=event();e["timecodeHint"]="UNTIMED"
        self.assertEqual(recover(e,words(),BAD.copy()),BAD)
    def test_short_quote_never_auto_promoted(self):
        self.assertEqual(recover(event("Da, am înțeles."),words("Da am înțeles"),BAD.copy()),BAD)
    def test_different_speech_not_falsely_accepted(self):
        w=words("Am venit astăzi la școala profesională pentru o meserie complet diferită")
        self.assertEqual(recover(event(),w,BAD.copy()),BAD)
    def test_invalid_nan_timestamps_fail_closed(self):
        self.assertEqual(recover(event(),[{"word":"unu","start":float("nan"),"end":3}],BAD.copy()),BAD)
        self.assertEqual(recover(event(),words(),BAD.copy(),time_offset=float("nan")),BAD)
    def test_missing_out_hint_uses_only_audio_bounds(self):
        e=event();e.pop("outSeconds")
        self.assertEqual(recover(e,words(),BAD.copy())["status"],"REVIEW_SUGGESTED")
    def test_source_code_is_not_hardcoded(self):
        e=event();e["sourceCode"]="9974"
        self.assertEqual(recover(e,words(),BAD.copy())["status"],"REVIEW_SUGGESTED")
    def test_ambiguous_prior_must_stay_ambiguous(self):
        old={"status":"REVIEW_ALTERNATIVE_OCCURRENCE","reason":"repeated"}
        self.assertEqual(recover(event(),words(),old),old)
    def test_bad_word_timestamp_fails(self):
        w=words();w[0].pop("end")
        self.assertEqual(recover(event(),w,BAD.copy()),BAD)
    def test_original_diagnostic_not_mutated(self):
        old=BAD.copy();recover(event(),words(),old)
        self.assertEqual(old,BAD)
if __name__=="__main__":unittest.main(verbosity=2)
