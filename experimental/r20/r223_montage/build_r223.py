"""R2.2.3: 7-file Montage update on top of R2.1.4 bootstrap.

Only the early bridge fixes updater; this R2.2.3 applies original R2.2.0
Montage engine to the user's verified R1.9.3 workflow. No updater regression.
"""
import argparse,hashlib,json,pathlib,zipfile
ZIP_R222="b0f1a567c2b29c882d1418cb5b7394c4ade8efa72508858ac7d6c93368d3909f"
WORKFLOW_BEFORE="b191306499a2fbb0077dd48e7e2d6b07c8f87075c9e03437e86a4cce0f611222"
FILENAMES={
 "cep/r193_workflow.js","tools/r193_pipeline.py",
 "tools/r220_montage_plan.py","tools/r220_capture.py",
 "tools/r220_montage_runner.py","cep/jsx/r220_montage_writer.jsx",
 "cep/jsx/r220_media_probe.jsx",
}
def sha(x):return hashlib.sha256(x).hexdigest()
def build(r222,output):
    raw=pathlib.Path(r222).read_bytes()
    if sha(raw)!=ZIP_R222:raise ValueError("Unexpected v2.2.2 SHA256")
    with zipfile.ZipFile(r222) as z:
        m=json.loads(z.read("manifest.json"))
        if m.get("version")!="2.2.2" or m.get("format")!=1:
            raise ValueError("Unexpected upstream release")
        allrows={r["path"]:r for r in m["files"]}
        if set(allrows)!=FILENAMES|{"updater/beta.py","cep/aive_updater_beta.js"}:
            raise ValueError("Unexpected upstream archive allowlist")
        blobs={}
        for name,row in allrows.items():
            b=z.read("payload/"+name)
            if sha(b)!=row["sha256"]:raise ValueError("Corrupt upstream file "+name)
            if name in FILENAMES:blobs[name]=b
    if allrows["cep/r193_workflow.js"]["before_sha256"]!=WORKFLOW_BEFORE:
        raise ValueError("Exact local workflow SHA no longer covered")
    if allrows["tools/r193_pipeline.py"]["before_sha256"] is None:
        raise ValueError("No original speech-first pipeline baseline")
    rows=[dict(allrows[p]) for p in sorted(FILENAMES)]
    m={"format":1,"version":"2.2.3","files":rows}
    out=pathlib.Path(output);out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(m,indent=2)+"\n")
        for p in sorted(blobs):z.writestr("payload/"+p,blobs[p])
    with zipfile.ZipFile(out) as z:
        assert json.loads(z.read("manifest.json"))==m
        assert set(z.namelist())=={"manifest.json",*(("payload/"+p) for p in blobs)}
        assert all(sha(z.read("payload/"+p))==allrows[p]["sha256"] for p in blobs)
    return {"version":"2.2.3","requires_bootstrap":"2.1.4",
            "fileCount":7,"archiveSHA256":sha(out.read_bytes()),
            "bytes":out.stat().st_size}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--r222",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    print(json.dumps(build(a.r222,a.out),indent=2))
