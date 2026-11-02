"""R2 beta discovery for existing safe AI Video Editor updater.
Explicitly opt-in via CEP. Stable runner.py and its rollback engine remain intact.
"""
from __future__ import annotations
import argparse,json,re,sys,urllib.request
from pathlib import Path
import runner

ALLOWED_REPO='Sankio9/ai-video-editor-updates'
MAX_RESPONSE=2*1024*1024

def check(root:Path,opener=None):
    root=Path(root)
    cfg=runner.read_json(root/'updater'/'config.json',{})
    if cfg.get('repository')!=ALLOWED_REPO or cfg.get('provider')!='github-public-releases':
        raise ValueError('Beta permis doar din repository-ul oficial '+ALLOWED_REPO)
    state=runner.read_json(root/'updater'/'state.json')
    local=state.get('version','');version=runner.ver(local)
    if version<(1,9,13):raise ValueError('Este necesară minimum R1.9.13.')
    uri='https://api.github.com/repos/'+ALLOWED_REPO+'/releases?per_page=100'
    request=urllib.request.Request(uri,headers={'Accept':'application/vnd.github+json','User-Agent':'AIVE-Beta/2.0'})
    with (opener or urllib.request.urlopen)(request,timeout=15) as response:
        if response.status!=200:raise ValueError('GitHub a răspuns HTTP '+str(response.status))
        data=json.loads(response.read(MAX_RESPONSE))
    if not isinstance(data,list):raise ValueError('Format GitHub invalid.')
    choices=[]
    for r in data:
        if not isinstance(r,dict) or not r.get('prerelease') or r.get('draft'):continue
        tag=r.get('tag_name','')
        if not isinstance(tag,str) or not re.fullmatch(r'v2\.\d+\.\d+',tag):continue
        target=runner.ver(tag)
        if target<=version:continue
        assets=[x for x in r.get('assets',[]) if x.get('name')==runner.ASSET_NAME and x.get('state')=='uploaded']
        if len(assets)!=1:raise ValueError('Beta '+tag+': lipsește asset-ul unic.')
        a=assets[0]
        sha=a.get('digest','')
        if not isinstance(sha,str) or not sha.startswith('sha256:') or not runner.SHA_RE.fullmatch(sha[7:]):
            raise ValueError('Beta '+tag+': digest SHA-256 invalid.')
        size=a.get('size')
        if not isinstance(size,int) or not 0<size<=runner.MAX_ASSET:raise ValueError('Beta '+tag+': dimensiune invalidă.')
        url=f'https://github.com/{ALLOWED_REPO}/releases/download/{tag}/{runner.ASSET_NAME}'
        if a.get('browser_download_url')!=url:raise ValueError('Beta '+tag+': URL neautorizat.')
        choices.append((target,tag,{'url':url,'digest':sha[7:],'size':size}))
    if not choices:
        return {'ok':True,'new':False,'channel':'beta','current':local,'latest':local,'repository':ALLOWED_REPO}
    _,tag,asset=min(choices,key=lambda x:x[0])
    return {'ok':True,'new':True,'channel':'beta','current':local,'latest':tag,'repository':ALLOWED_REPO,'asset':asset}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default=r'D:\AI-Video-Editor')
    ap.add_argument('--installed',default=str(Path.home()/'AppData'/'Roaming'/'Adobe'/'CEP'/'extensions'/'com.kinom.aivideo.subtitles'))
    actions=ap.add_mutually_exclusive_group(required=True)
    actions.add_argument('--check-beta',action='store_true')
    actions.add_argument('--prepare-beta',action='store_true')
    args=ap.parse_args();root=Path(args.root)
    try:
        result=check(root)
        if args.prepare_beta:
            if not result['new']:raise ValueError('Nu există un update Beta nou.')
            result=runner.prepare(root,Path(args.installed),result)
        print(json.dumps(result,ensure_ascii=False))
    except Exception as exc:
        runner.set_status(root,'error',str(exc))
        print(json.dumps({'ok':False,'message':str(exc)},ensure_ascii=False))
        return 2
    return 0
if __name__=='__main__':raise SystemExit(main())
