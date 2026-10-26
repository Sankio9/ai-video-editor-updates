"""Build update ZIPs for AI Video Editor from an explicit allowlist.
Public release artifacts: do not add proprietary code or editorial materials.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SUFFIXES = {'.js', '.jsx', '.html', '.css', '.json', '.py', '.md', '.txt'}
PROTECTED = {
    'cep/CSXS/manifest.xml', 'updater/config.json', 'updater/state.json',
    'cep/unified_panel.js', 'cep/main.js',
    'cep/jsx/captions.jsx', 'cep/jsx/fullsubs.jsx',
    'cep/jsx/nametag.jsx', 'cep/jsx/montage.jsx',
    'cep/jsx/r153.jsx', 'cep/jsx/r15.jsx',
    'tools/r141_match.py', 'tools/reportaj_r14_run.py',
}
VERSION = re.compile(r'^(?:v?)(\d+)\.(\d+)\.(\d+)$')
SHA = re.compile(r'^[a-f0-9]{64}$')
MAX_UNPACKED = 160 * 1024 * 1024
MAX_ZIP = 45 * 1024 * 1024

def version(v):
    m = VERSION.fullmatch(str(v))
    if not m:
        raise ValueError('Version must be X.Y.Z')
    return tuple(int(n) for n in m.groups())

def safe_path(rel):
    if not isinstance(rel, str) or len(rel) > 240 or '\\' in rel or '\x00' in rel:
        return False
    p = PurePosixPath(rel)
    if p.is_absolute() or p.as_posix() != rel:
        return False
    if any(x in ('', '.', '..') or x.startswith('.') or ':' in x for x in rel.split('/')):
        return False
    return p.suffix.lower() in ALLOWED_SUFFIXES and rel.casefold() not in {x.casefold() for x in PROTECTED} and len(p.parts) > 1 and p.parts[0] in ('cep', 'tools', 'updater')

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def build(root, outfile):
    root = Path(root).resolve()
    spec = json.loads((root / 'release' / 'next.json').read_text(encoding='utf-8'))
    target = spec['version']
    if version(target) <= version('1.8.9'):
        raise ValueError('Release version is not newer than 1.8.9')
    entries = spec.get('files')
    if not isinstance(entries, list) or not 1 <= len(entries) <= 100:
        raise ValueError('Invalid file list')
    seen, total, manifest_files, payload = set(), 0, [], []
    for ent in entries:
        rel = ent['path']
        if not safe_path(rel) or rel.casefold() in seen:
            raise ValueError('Blocked or duplicate path: ' + str(rel))
        seen.add(rel.casefold())
        before = ent.get('before_sha256')
        if before is not None and not SHA.fullmatch(str(before)):
            raise ValueError('Invalid previous hash for ' + rel)
        source = root.joinpath('release', 'files', *rel.split('/'))
        allowed_root = (root / 'release' / 'files').resolve()
        if not source.is_file() or source.is_symlink() or not source.resolve().is_relative_to(allowed_root):
            raise ValueError('Missing or redirected file: ' + rel)
        data = source.read_bytes()
        total += len(data)
        if total > MAX_UNPACKED:
            raise ValueError('Release too large')
        if ent.get('sha256') and ent['sha256'] != sha256(data):
            raise ValueError('Source digest mismatch: ' + rel)
        manifest_files.append({'path': rel, 'sha256': sha256(data), 'before_sha256': before})
        payload.append((rel, data))
    outfile = Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(outfile, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel, data in payload:
            z.writestr('payload/' + rel, data)
        z.writestr('manifest.json', json.dumps({'format': 1, 'version': target, 'files': manifest_files}, indent=2))
    if outfile.stat().st_size > MAX_ZIP:
        raise ValueError('Compressed archive too large')
    return {'version': target, 'files': len(payload), 'sha256': sha256(outfile.read_bytes())}

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', default=str(ROOT / 'dist' / 'AIVE_UPDATE.zip'))
    args = p.parse_args()
    print(json.dumps(build(ROOT, Path(args.output)), indent=2))
