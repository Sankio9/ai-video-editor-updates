"""R2.0.2 beta channel tests without distributing private updater runner."""
import importlib, json, re, sys, tempfile, types, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO='Sankio9/ai-video-editor-updates'
runner=types.ModuleType('runner')
runner.ASSET_NAME='AIVE_UPDATE.zip'
runner.MAX_ASSET=45*1024*1024
runner.SHA_RE=re.compile(r'^[a-f0-9]{64}$')
runner.ver=lambda x:tuple(int(z) for z in re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)',x).groups())
runner.read_json=lambda path,default=None:json.loads(Path(path).read_text('utf-8'))
runner.prepare=lambda root,installed,info:{'ok':True,'action':'waiting_for_close'}
runner.set_status=lambda *a,**kw:None
sys.modules['runner']=runner
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'updater'))
beta=importlib.import_module('beta')

def release(tag, prerelease=True):
    return {'tag_name':tag,'draft':False,'prerelease':prerelease,
     'assets':[{'name':'AIVE_UPDATE.zip','state':'uploaded',
       'digest':'sha256:'+'f'*64,'size':2035,
       'browser_download_url':f'https://github.com/{REPO}/releases/download/{tag}/AIVE_UPDATE.zip'}]}
class Response:
    status=200
    def __init__(self,data):self.payload=json.dumps(data).encode('utf8')
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def read(self,n):return self.payload[:n]

class BetaTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        p=self.root/'updater';p.mkdir()
        (p/'config.json').write_text(json.dumps({'provider':'github-public-releases','repository':REPO}))
        (p/'state.json').write_text(json.dumps({'version':'v2.0.2'}))
    def tearDown(self):self.tmp.cleanup()
    def fetch(self,releases):return beta.check(self.root,lambda req,timeout:Response(releases))
    def test_next_incremental_beta(self):
        self.assertEqual(self.fetch([release('v2.0.8'),release('v2.0.3'),release('v2.0.1')])['latest'],'v2.0.3')
    def test_no_new(self):
        self.assertFalse(self.fetch([release('v2.0.2'),release('v2.0.1')])['new'])
    def test_stable_release_ignored(self):
        self.assertFalse(self.fetch([release('v2.0.4',False)])['new'])
    def test_reject_bad_digest(self):
        a=release('v2.0.3');a['assets'][0]['digest']='bad'
        with self.assertRaisesRegex(ValueError,'digest'):self.fetch([a])
    def test_reject_bad_link(self):
        a=release('v2.0.3');a['assets'][0]['browser_download_url']='https://example.org/unsafe.zip'
        with self.assertRaisesRegex(ValueError,'URL'):self.fetch([a])
    def test_reject_malicious_config(self):
        (self.root/'updater'/'config.json').write_text(json.dumps({'provider':'github-public-releases','repository':'fake/fork'}))
        with self.assertRaisesRegex(ValueError,'oficial'):self.fetch([])
    def test_stable_selected_by_default(self):
        js=(ROOT/'cep/aive_updater_beta.js').read_text('utf8')
        html=(ROOT/'cep/index.html').read_text('utf8')
        self.assertIn("['stable','Stable (recomandat)']",js)
        self.assertIn("beta.style.display='none'",js)
        self.assertIn('<script src="aive_updater_beta.js"></script>',html)
    def test_hash_pin_sources(self):
        from build_r202 import FILES,sha
        for path,(src,expected,before) in FILES.items():
            self.assertEqual(sha(src.read_bytes()),expected,path)
        self.assertEqual(FILES['tools/r20_graphics_plans.py'][2],
                         '37ec5e19ae2223d079263cbac9763fe2cb915593f9d4e37151cff7d522fa562f')
if __name__=='__main__':unittest.main(verbosity=2)
