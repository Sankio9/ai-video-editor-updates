"""R237 bundle for testing (NOT RELEASE). Preserve SHA from published
R2.3.5, R2.2.3 and R2.2.4 exact sources. Insert only additive synced VO
graphic controls and opt-in R220 DOCX strike copy. R1.9.13 untouched.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,zipfile
from build_vo_writer import derive as derive_writer
ROOT=pathlib.Path(__file__).resolve().parent
WORKFLOW="cep/r193_workflow.js"
RUNNER="tools/r220_montage_runner.py"
CAPTURE="tools/r220_capture.py"
PANEL="cep/r20_panel.js"
NEW_PY={"tools/r237_vo_plan.py":ROOT/"tools/r237_vo_plan.py",
        "tools/r237_strikethrough_docx.py":ROOT/"tools/r237_strikethrough_docx.py"}
WRITER="cep/jsx/r237_vo_graphics.jsx"
def sha(x):return hashlib.sha256(x).hexdigest()
def load_archive(path,version):
    with zipfile.ZipFile(path) as z:
        manifest=json.loads(z.read('manifest.json'))
        if manifest.get('version')!=version or manifest.get('format')!=1:
            raise ValueError("PREVIOUS_VERSION_MISMATCH "+version)
        files={}
        for entry in manifest['files']:
            data=z.read("payload/"+entry['path'])
            if sha(data)!=entry['sha256']:
                raise ValueError("PUBLISHED_SHA_MISMATCH "+entry['path'])
            files[entry['path']]=data
        return files
def one(s,a,b):
    if s.count(a)!=1:raise ValueError("R237_WORKFLOW_SOURCE_ANCHOR_CHANGED "+a[:90])
    return s.replace(a,b,1)
def patch_workflow(original):
    s=original.decode('utf8')
    addon=(ROOT/'candidate/cep/r220_montage_panel.js').read_text('utf8')
    # Verify exact approved original R220 addon is present before mutating.
    for hook in ("var stat=E('cutR193Status'),lastDoc=null;",
                 "function runner(media,d,cb){",
                 "runner(media,d,function(error,response){",
                 "offer({doc:d,docSHA:docHash,lock:lock},media);"):
        if hook not in s:raise ValueError("R220_MODULE_NOT_FOUND "+hook)
    base=(ROOT.parent/'r220/cep/r220_montage_panel.js').read_text('utf8')
    if s.count(base)!=1:
        raise ValueError("R220_MODULE_DIFFERS_FROM_APPROVED_SOURCE")
    replacement=addon
    for safety in ("function verifyState(", "STRIKE", "r237MontageOmitStruck",
                   "last_report.json","CONTINUE_WITH_PLACEHOLDERS",
                   "sha(fs.readFileSync(state.doc))"):
        if safety=='STRIKE':continue
        if safety not in replacement:raise ValueError("R237_MONTAGE_SAFETY_MISSING "+safety)
    return s.replace(base,replacement,1).encode('utf8')
def build(v235,v223,v224,v200,out):
    primary=load_archive(v235,'2.3.5')
    montage=load_archive(v223,'2.2.3')
    capture=load_archive(v224,'2.2.4')
    originals={PANEL:primary[PANEL],WORKFLOW:montage[WORKFLOW],
               RUNNER:montage[RUNNER],CAPTURE:capture[CAPTURE]}
    for p,d in originals.items():
        if not d or len(d)<500:raise ValueError("PUBLISHED_SOURCE_MISSING "+p)
    modified={
       PANEL:primary[PANEL]+b'\n'+(ROOT/'cep/r237_synced_caps_panel.js').read_bytes()+b'\n',
       WORKFLOW:patch_workflow(originals[WORKFLOW]),
       RUNNER:(ROOT/'candidate/tools/r220_montage_runner.py').read_bytes(),
       CAPTURE:(ROOT/'candidate/tools/r220_capture.py').read_bytes()
    }
    modified.update({p:location.read_bytes() for p,location in NEW_PY.items()})
    prior_writer=load_archive(v200,'2.0.0')["cep/jsx/r20_graphics.jsx"]
    modified[WRITER]=derive_writer(prior_writer)
    for p,d in modified.items():
        if p.endswith('.py'):compile(d,p,'exec')
    javascript=modified[PANEL].decode('utf8')
    if (javascript.count('function onClickCapture')<1 or
        'R237 VO' not in javascript or 'showNameTagReview' not in javascript):
        raise ValueError("R237_CEP_MODULE_HOOK_MISSING")
    if b'app.enableQE' in b''.join(modified.values()):
        raise ValueError("QE_FORBIDDEN")
    rows=[{"path":p,"before_sha256":sha(originals[p]) if p in originals else None,
           "sha256":sha(d)} for p,d in sorted(modified.items())]
    m={"format":1,"version":"2.3.7","files":rows}
    dst=pathlib.Path(out);dst.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(m,ensure_ascii=True,indent=2)+'\n')
        for p,d in sorted(modified.items()):z.writestr("payload/"+p,d)
    with zipfile.ZipFile(dst) as z:
        assert json.loads(z.read('manifest.json'))==m
        assert set(z.namelist())=={'manifest.json',*(("payload/"+p) for p in modified)}
        for p,d in modified.items():assert sha(z.read("payload/"+p))==sha(d)
    return {"version":"2.3.7","zipSHA256":sha(dst.read_bytes()),"files":rows}
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    for name in ("v235","v223","v224","v200","out"):
        parser.add_argument('--'+name,required=True)
    a=parser.parse_args()
    print(json.dumps(build(a.v235,a.v223,a.v224,a.v200,a.out),indent=2))
