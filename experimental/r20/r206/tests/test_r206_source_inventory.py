"""R2.0.6 Project Panel strict media mapping synthetic tests."""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from r206_source_inventory import name_codes, resolve_project_panel, sources_for_rescan


class TestProjectPanelResolver(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.base=Path(self.tmp.name)
        self.m1=self.base/"CAM_9981_interview.MOV"
        self.m2=self.base/"SRC_9974_amb.wav"
        self.m1.write_bytes(b"a"*256)
        self.m2.write_bytes(b"b"*128)
        self.first={"type":"media","name":"CAM_9981_interview.MOV",
                    "mediaPath":str(self.m1),"offline":False,"nodeId":"node01"}
        self.second={"type":"media","name":"SRC_9974_amb.wav",
                     "mediaPath":str(self.m2),"offline":False,"nodeId":"node02"}
        self.inv={"schema":"aive-r206-project-panel-v1","items":[
            {"type":"bin","name":"Bubuieci","children":[
                {"type":"bin","name":"Camera A","children":[self.first]},
                {"type":"bin","name":"Audio","children":[self.second]}]}]}
    def tearDown(self):
        self.tmp.cleanup()

    def test_recursive_nested_bins(self):
        result=resolve_project_panel(self.inv,["9974","9981"])
        self.assertEqual(result["9981"],str(self.m1))
        self.assertEqual(result["9974"],str(self.m2))
    def test_extract_codes_from_basenames_not_folders(self):
        self.assertEqual(name_codes(r"D:\2026\CAM_9981_x.mov"),{"9981"})
        self.assertEqual(name_codes(r"C:\reports\2026\video.MOV"),set())
        self.assertEqual(name_codes("CAM_99811_x.mov"),set())
        self.assertEqual(name_codes("CAM_09981_x.mov"),set())
        self.assertEqual(name_codes("CAM_9981_x.mov"),{"9981"})
    def test_offline_is_error(self):
        self.second["offline"]=True
        with self.assertRaisesRegex(ValueError,"OFFLINE_OR_UNKNOWN"):
            resolve_project_panel(self.inv,["9974"])
    def test_unknown_offline_is_error(self):
        self.second.pop("offline")
        with self.assertRaisesRegex(ValueError,"OFFLINE_OR_UNKNOWN"):
            resolve_project_panel(self.inv,["9974"])
    def test_missing_required_red(self):
        with self.assertRaisesRegex(ValueError,"MISSING_RED.*9931"):
            resolve_project_panel(self.inv,["9931"])
    def test_duplicated_media_in_different_bins(self):
        self.inv["items"].append({"type":"media","name":"9981 copy",
            "mediaPath":str(self.m1),"offline":False,"nodeId":"node03"})
        with self.assertRaisesRegex(ValueError,"DUPLICATE_RED: 9981"):
            resolve_project_panel(self.inv,["9981"])
    def test_contradictory_codes_stop(self):
        self.first["name"]="CAM_9930.mov"
        with self.assertRaisesRegex(ValueError,"CONTRADICTORY_SOURCE_CODES"):
            resolve_project_panel(self.inv,["9981"])
    def test_ambiguous_filename_stop(self):
        self.first["name"]="CAM_9981_9931.mov"
        with self.assertRaisesRegex(ValueError,"AMBIGUOUS_MEDIA_FILENAME"):
            resolve_project_panel(self.inv,["9981"])
    def test_missing_file_stop(self):
        self.m1.unlink()
        with self.assertRaisesRegex(ValueError,"MEDIA_MISSING_OR_LINKED"):
            resolve_project_panel(self.inv,["9981"])
    def test_missing_media_path_stop(self):
        self.first.pop("mediaPath")
        with self.assertRaisesRegex(ValueError,"NO_REAL_MEDIA_PATH"):
            resolve_project_panel(self.inv,["9981"])
    def test_duplicate_node_id_stop(self):
        self.second["nodeId"]="node01"
        with self.assertRaisesRegex(ValueError,"Duplicate Project Panel nodeId"):
            resolve_project_panel(self.inv,["9981"])
    def test_unrelated_sequence_not_media(self):
        self.inv["items"].insert(0,{"type":"sequence","name":"Edit 9981"})
        self.assertEqual(resolve_project_panel(self.inv,["9981"])["9981"],str(self.m1))
    def test_invalid_codes_stop(self):
        with self.assertRaisesRegex(ValueError,"Invalid required"):
            resolve_project_panel(self.inv,["99818"])
    def test_no_required_codes_stop(self):
        with self.assertRaisesRegex(ValueError,"No required"):
            resolve_project_panel(self.inv,[])
    def test_duplicate_required_codes_stop(self):
        with self.assertRaisesRegex(ValueError,"Duplicate required"):
            resolve_project_panel(self.inv,["9981","9981"])
    def test_invalid_schema_stop(self):
        with self.assertRaisesRegex(ValueError,"Unknown Project Panel"):
            resolve_project_panel({"items":[]},["9981"])
    def test_source_map_for_rescan(self):
        self.assertEqual(sources_for_rescan({"rescans":[
            {"sourceCode":"9981"},{"sourceCode":"9974"}]},self.inv)["9974"],str(self.m2))

if __name__=="__main__":
    unittest.main(verbosity=2)
