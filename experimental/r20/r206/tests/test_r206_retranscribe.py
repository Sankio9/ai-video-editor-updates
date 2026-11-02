"""Synthetic tests for local GPU/ffmpeg adapter; no actual media/ASR required."""
from __future__ import annotations
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import r206_retranscribe as runner
from r206_selective_asr import SCHEMA_OUT as SCHEMA_REQUEST

def plan():
    return {"schema":SCHEMA_REQUEST,"action":"REQUEST_SELECTIVE_RETRANSCRIPTION_ONLY",
            "safeToModifyPremiereTimeline":False,"automaticCuttingAllowed":False,
            "rescans":[{"sourceCode":"9974","sourceDurationSeconds":88.32,
                        "windows":[{"startSeconds":10.0,"endSeconds":14.0,
                                    "cutIds":["CUT-18","CUT-19"]}]}],
            "blocked":[]}

class TestR206OfflineRunner(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.root=Path(self.t.name)
        self.media=self.root/"camera 9974.mov";self.media.write_bytes(b"synthetic-private-media-placeholder")
        self.map={"9974":str(self.media)}
        self.writes=0
    def tearDown(self):self.t.cleanup()
    def extract(self,media,start,end,wav,ffmpeg):
        self.writes+=1
        self.assertEqual(media,self.media)
        self.assertEqual((start,end),(10.,14.))
        wav.write_bytes(b"WAVE MOCK DATA")
    def transcribe(self,wav):
        self.assertTrue(wav.is_file())
        return {"language":"ro","words":[
            {"start":.5,"end":.9,"text":"Școala","probability":.92},
            {"start":1.1,"end":1.6,"text":"profesională","probability":.87}]}
    def probe(self,media,ffprobe):
        return 88.32
    def test_candidate_words_absolute_offsets_and_local_only(self):
        r=runner.execute(plan(),self.map,self.transcribe,probe_fn=self.probe,
                         extract_fn=self.extract,tempdir=self.root)
        self.assertEqual(r["schema"],runner.SCHEMA_OUT)
        self.assertFalse(r["safeToModifyPremiereTimeline"])
        self.assertFalse(r["automaticCuttingAllowed"])
        one=r["rescans"][0]["windows"][0]
        self.assertEqual(one["status"],"REVIEW_REQUIRED")
        self.assertEqual(one["detectedLanguage"],"ro")
        self.assertEqual(one["words"][0]["startSeconds"],10.5)
        self.assertEqual(one["words"][1]["endSeconds"],11.6)
        self.assertEqual(self.writes,1)
        self.assertEqual(list(self.root.glob("aive_r206_*")),[])
        self.assertNotIn(str(self.media),json.dumps(r))
    def test_offline_source_before_audio_extraction(self):
        with self.assertRaisesRegex(ValueError,"Offline/unmapped"):
            runner.execute(plan(),{},self.transcribe,probe_fn=self.probe,
                           extract_fn=self.extract,tempdir=self.root)
        self.assertEqual(self.writes,0)
    def test_changed_media_duration_before_audio_extraction(self):
        with self.assertRaisesRegex(ValueError,"changed"):
            runner.execute(plan(),self.map,self.transcribe,probe_fn=lambda p,f:99.,
                           extract_fn=self.extract,tempdir=self.root)
        self.assertEqual(self.writes,0)
    def test_block_auto_cut_true(self):
        p=plan();p["automaticCuttingAllowed"]=True
        with self.assertRaisesRegex(ValueError,"automatic-cut"):
            runner.execute(p,self.map,self.transcribe,probe_fn=self.probe,
                           extract_fn=self.extract,tempdir=self.root)
    def test_invalid_asr_word_timing_rejected(self):
        bad=lambda wav:{"language":"ro","words":[
            {"start":5.0,"end":6.0,"text":"Nonexistent"}]}
        with self.assertRaisesRegex(ValueError,"word timing"):
            runner.execute(plan(),self.map,bad,probe_fn=self.probe,
                           extract_fn=self.extract,tempdir=self.root)
        self.assertEqual(list(self.root.glob("aive_r206_*")),[])
    def test_empty_asr_marked_not_accepted(self):
        r=runner.execute(plan(),self.map,lambda wav:{"language":"unknown","words":[]},
                         probe_fn=self.probe,extract_fn=self.extract,tempdir=self.root)
        a=r["rescans"][0]["windows"][0]
        self.assertEqual(a["qualityFlags"],["ASR_EMPTY"])
        self.assertEqual(a["status"],"REVIEW_REQUIRED")
    def test_repetition_flags_not_auto_accepted(self):
        words=[{"start":i*.3,"end":i*.3+.22,"text":["Ana","are","mere"][i%3]}
               for i in range(12)]
        r=runner.execute(plan(),self.map,lambda wav:{"language":"ro","words":words},
                         probe_fn=self.probe,extract_fn=self.extract,tempdir=self.root)
        self.assertIn("POSSIBLE_ASR_REPETITION",r["rescans"][0]["windows"][0]["qualityFlags"])
        self.assertFalse(r["automaticCuttingAllowed"])
    def test_reject_unsupported_source_extension(self):
        self.media.rename(self.root/"camera.exe")
        with self.assertRaisesRegex(ValueError,"Missing/invalid"):
            runner.validate(plan(),{"9974":str(self.root/"camera.exe")})
    def test_reject_overlapping_windows(self):
        p=plan();p["rescans"][0]["windows"].append({
            "startSeconds":13.0,"endSeconds":16.0,"cutIds":["CUT-20"]})
        with self.assertRaisesRegex(ValueError,"overlap"):
            runner.validate(p,self.map)
    def test_atomic_local_save_roundtrip(self):
        report={"schema":runner.SCHEMA_OUT,"automaticCuttingAllowed":False,
                "rescans":[{"words":[{"text":"Școala"}]}]}
        dest=self.root/"private"/"asr.json"
        runner.save_report(report,dest)
        self.assertEqual(json.loads(dest.read_text("utf8")),report)
        self.assertFalse((dest.parent/"asr.json.tmp").exists())
    def test_no_model_name_download(self):
        with self.assertRaisesRegex(ValueError,"preinstalled"):
            runner.make_whisper(self.root/"missing_model")
    def test_no_window_survives_decoder_failure(self):
        def failing(media,a,b,wav,ffmpeg):
            wav.write_bytes(b"partial")
            raise ValueError("mock decoder error")
        with self.assertRaisesRegex(ValueError,"mock decoder"):
            runner.execute(plan(),self.map,self.transcribe,probe_fn=self.probe,
                           extract_fn=failing,tempdir=self.root)
        self.assertEqual(list(self.root.glob("aive_r206_*")),[])

if __name__=="__main__":unittest.main(verbosity=2)
