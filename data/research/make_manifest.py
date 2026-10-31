# -*- coding: utf-8 -*-
"""重新生成 data/research/file_manifest.json。

只收录"项目资产"：文档、数据、地理、图片、前端源码与脚本。
排除 node_modules / dist / .probe / .git / target，这些要么可重建，
要么体积巨大且对验收没有意义。
"""
import hashlib
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SKIP_DIRS = {
    'node_modules', 'dist', '.probe', '.git', 'target', 'coverage',
    '__pycache__', '.vite', 'profile2',
}
SKIP_EXT = {'.log', '.tmp', '.pyc', '.db', '.mv.db', '.trace.db'}


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


files = []
for base, dirs, names in os.walk(ROOT):
    dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
    for n in sorted(names):
        ext = os.path.splitext(n)[1].lower()
        if ext in SKIP_EXT:
            continue
        full = os.path.join(base, n)
        rel = os.path.relpath(full, ROOT).replace('\\', '/')
        files.append({
            'path': rel,
            'bytes': os.path.getsize(full),
            'sha256': digest(full),
        })

out = {
    'generated_by': 'data/research/make_manifest.py',
    'root': '.',
    'count': len(files),
    'total_bytes': sum(f['bytes'] for f in files),
    'files': files,
}
dest = os.path.join(ROOT, 'data', 'research', 'file_manifest.json')
with open(dest, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print('files=%d total=%.1f MB -> %s' % (len(files), out['total_bytes'] / 1e6, dest))
