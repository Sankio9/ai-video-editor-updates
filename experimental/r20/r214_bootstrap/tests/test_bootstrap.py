"""R2.1.4 regression: choosing newest Beta must not change SHA safety."""
import io,json,re,sys,types,unittest,zipfile,contextlib
from pathlib import Path

ZIP=Path(__file__).resolve().parents[4]/"dist"/"AIVE_UPDATE.zip"

class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    with zipfile.ZipFile(ZIP) as z:
      cls.beta=z.read("payload/updater/beta.py").decode("utf8")
      cls.js=z.read("payload/cep/aive_updater_beta.js").decode("utf8")
 def check(self,version,releases):
    previous=sys.modules.get("runner")
    fake=types.ModuleType("runner")
    fake.ASSET_NAME="AIVE_UPDATE.zip"
    fake.MAX_ASSET=30000000
    fake.SHA_RE=re.compile(r"[0-9a-f]{64}")
    fake.ver=lambda v:tuple(int(x) for x in str(v).lstrip("v").split(".")[:3])
    fake.read_json=lambda path,default=None:(
      {"repository":"Sankio9/ai-video-editor-updates","provider":"github-public-releases"} if "config.json" in str(path)
      else {"version":version})
    sys.modules["runner"]=fake
    module=types.ModuleType("test_aive_bootstrap")
    try:
      exec(compile(self.beta,"beta.py","exec"),module.__dict__)
      class Response:
        status=200
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,n):return json.dumps(releases).encode("utf8")
      return module.check(Path("/not/actual"),opener=lambda req,timeout:Response())
    finally:
      if previous is None:sys.modules.pop("runner",None)
      else:sys.modules["runner"]=previous
 def release(self,tag):
    digest="sha256:"+"a"*64
    return {"tag_name":tag,"draft":False,"prerelease":True,
      "assets":[{"name":"AIVE_UPDATE.zip","state":"uploaded",
        "digest":digest,"size":5000,
        "browser_download_url":
          "https://github.com/Sankio9/ai-video-editor-updates/releases/download/"+tag+"/AIVE_UPDATE.zip"}]}
 def test_select_newest_not_oldest(self):
    tags=["v2.2.2","v2.2.1","v2.2.0","v2.1.4","v2.1.3"]
    result=self.check("2.1.4",[self.release(x) for x in tags])
    self.assertEqual(result["latest"],"v2.2.2")
    self.assertEqual(result["asset"]["digest"],"a"*64)
 def test_bootstrap_selected_from_previous_broken_updater(self):
    # The OLD updater's min() will correctly select v2.1.4 first.
    tags=["v2.2.3","v2.2.0","v2.1.4"]
    self.assertEqual(min(tags,key=lambda x:tuple(map(int,x[1:].split(".")))),"v2.1.4")
    result=self.check("2.1.3",[self.release(x) for x in tags])
    self.assertEqual(result["latest"],"v2.2.3") # after bootstrap, new selection is max
 def test_skip_stable_and_older(self):
    releases=[self.release("v2.1.2"),dict(self.release("v2.2.4"),prerelease=False)]
    self.assertFalse(self.check("2.1.4",releases)["new"])
 def test_ascii_stdout_and_explicit_child_utf8(self):
    self.assertIn("ensure_ascii=True",self.beta)
    self.assertNotIn("ensure_ascii=False",self.beta)
    self.assertIn("PYTHONIOENCODING:'utf-8'",self.js)
    self.assertIn("PYTHONUTF8:'1'",self.js)
 def test_no_checksum_or_security_skip(self):
    self.assertIn("runner.prepare(",self.beta)
    self.assertIn("runner.SHA_RE.fullmatch",self.beta)
    self.assertIn("a.get('browser_download_url')!=url",self.beta)
if __name__=="__main__":unittest.main(verbosity=2)
