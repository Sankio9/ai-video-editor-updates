"""Validate an encoded update ZIP and its allowlisted per-file manifest."""
from __future__ import annotations
import argparse,base64,hashlib,json,sys,zipfile
from pathlib import Path
from build_release import safe_path,version
ROOT=Path(__file__).resolve().parents[1]
def main(root:Path,output:Path):
    cfg=json.loads((root/'release/next.json').read_text('utf-8'))
    if 'encoded_archive' not in cfg:
        from build_release import build
        return build(root,output)
    rel=cfg['encoded_archive']
    expected='release/assets/v'+cfg['version']+'.zip.b64'
    if rel!=expected or not (root/rel).is_file():raise ValueError('Unexpected archive source path')
    raw=base64.b64decode((root/rel).read_text('ascii').strip(),validate=True)
    if len(raw)>45*1024*1024 or hashlib.sha256(raw).hexdigest()!=cfg['archive_sha256']:
        raise ValueError('ZIP is oversized or archive digest does not match')
    from io import BytesIO
    with zipfile.ZipFile(BytesIO(raw)) as z:
        names=z.namelist()
        if 'manifest.json' not in names or len(names)!=len(set(names)) or len(names)>110:raise ValueError('Invalid ZIP names')
        meta=json.loads(z.read('manifest.json'))
        if meta.get('format')!=1 or version(meta['version'])!=version(cfg['version']):raise ValueError('Version mismatch')
        items=meta['files']
        if not items or len(items)>100 or items!=cfg['files']:raise ValueError('ZIP does not match exact reviewed manifest')
        if set(names)!={'manifest.json',*[('payload/'+x['path']) for x in items]}:raise ValueError('Unannounced ZIP entry')
        total=0
        for x in items:
            if not safe_path(x['path']):raise ValueError('Invalid or protected path')
            info=z.getinfo('payload/'+x['path'])
            if ((info.external_attr>>16)&0o170000)==0o120000 or info.flag_bits&1:raise ValueError('Symlink or encrypted entry')
            b=z.read(info);total+=len(b)
            if total>160*1024*1024 or hashlib.sha256(b).hexdigest()!=x['sha256']:raise ValueError('Invalid payload hash/size')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(raw)
    return {'version':cfg['version'],'files':len(cfg['files']),'sha256':cfg['archive_sha256']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(ROOT));p.add_argument('--output',default=str(ROOT/'dist/AIVE_UPDATE.zip'));a=p.parse_args()
    print(json.dumps(main(Path(a.root),Path(a.output)),indent=2))
