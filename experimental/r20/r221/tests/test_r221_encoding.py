"""Windows CP1252 regression for packaged R2.2.1 Beta python updater."""
import importlib.util,io,json,sys,types,unittest,zipfile
from pathlib import Path

def artifact():
    return Path(__file__).resolve().parents[4]/"dist"/"AIVE_UPDATE.zip"

class EncodingSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(artifact()) as z:
            cls.source=z.read("payload/updater/beta.py").decode("utf8")
            cls.panel=z.read("payload/cep/aive_updater_beta.js").decode("utf8")

    def load(self):
        stub=types.ModuleType("runner")
        stub.read_json=lambda *args,**kwargs:{}
        stub.set_status=lambda *args,**kwargs:None
        sys.modules["runner"]=stub
        beta=types.ModuleType("r221_beta_test")
        exec(compile(self.source,"r221_beta_test.py","exec"),beta.__dict__)
        return beta

    def execute(self,result=None,error=None):
        beta=self.load()
        if error is not None:
            def cb(root):
                raise ValueError(error)
        else:
            def cb(root):
                return result
        beta.check=cb
        previous_out,previous_argv=sys.stdout,sys.argv
        buffer=io.BytesIO()
        try:
            sys.stdout=io.TextIOWrapper(buffer,encoding="cp1252",
                                        errors="strict",write_through=True)
            sys.argv=["r221_beta_test.py","--check-beta","--root","C:\\TEST"]
            code=beta.main()
            sys.stdout.flush()
            decoded=buffer.getvalue().decode("cp1252")
        finally:
            sys.stdout,sys.argv=previous_out,previous_argv
        return code,decoded,json.loads(decoded)

    def test_non_ascii_error_is_ascii_json_not_unicode_error(self):
        code,line,item=self.execute(error="Este necesară minimum R1.9.13.")
        self.assertEqual(code,2)
        self.assertEqual(item["message"],"Este necesară minimum R1.9.13.")
        self.assertTrue(line.isascii())
        self.assertIn("\\u0103",line)

    def test_non_ascii_success_is_ascii_json(self):
        code,line,item=self.execute(result={"ok":True,"new":True,
                                            "message":"Actualizare pregătită","latest":"v2.2.1"})
        self.assertEqual(code,0)
        self.assertEqual(item["message"],"Actualizare pregătită")
        self.assertTrue(line.isascii())

    def test_js_sets_utf8_for_child_process_and_no_old_spawn(self):
        self.assertIn("PYTHONIOENCODING:'utf-8'",self.panel)
        self.assertIn("PYTHONUTF8:'1'",self.panel)
        self.assertIn("env:betaEnv",self.panel)
        self.assertNotIn("cp.spawn(python,args,{cwd:root,windowsHide:true})",self.panel)

    def test_only_json_output_is_ascii_safe(self):
        self.assertEqual(self.source.count("ensure_ascii=True"),2)
        self.assertNotIn("ensure_ascii=False",self.source)

if __name__=="__main__":unittest.main(verbosity=2)
