# -*- coding: utf-8 -*-
"""下载 Esri World Imagery 瓦片，做成本地离线瓦片包（z14-z18）。

- 宽区域：z14-z17（校园 + 周边）
- 核心区：z18（四个驿站所在范围，看得清楼）
"""
import json
import math
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import urllib.request

ROOT = r'D:\java大作业'
OUT = os.path.join(ROOT, 'frontend', 'public', 'tiles', 'sat')
TMP = os.path.join(ROOT, 'frontend', 'public', 'tiles', '_tmp')

BASE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CampusFlow/1.0'

# 宽区域：校园外扩约 1.5 km
WIDE = dict(lat0=34.2000, lat1=34.2320, lon0=117.1180, lon1=117.1620)
# 核心区：四个驿站 + 主要道路
CORE = dict(lat0=34.2040, lat1=34.2255, lon0=117.1260, lon1=117.1540)

PLAN = [(14, WIDE), (15, WIDE), (16, WIDE), (17, WIDE), (18, CORE)]

lock = threading.Lock()
done = [0, 0, 0]   # 成功, 失败, 字节


def deg2num(lat, lon, z):
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    lat_r = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n)
    return x, y


def tile_range(b, z):
    x0, y0 = deg2num(b['lat1'], b['lon0'], z)
    x1, y1 = deg2num(b['lat0'], b['lon1'], z)
    return range(x0, x1 + 1), range(y0, y1 + 1)


def fetch(z, x, y):
    path = os.path.join(OUT, str(z), str(x), '%d.jpg' % y)
    if os.path.exists(path) and os.path.getsize(path) > 500:
        with lock:
            done[0] += 1
            done[2] += os.path.getsize(path)
        return
    url = BASE.format(z=z, x=x, y=y)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = r.read()
            if len(data) < 400:
                raise IOError('tiny')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                f.write(data)
            with lock:
                done[0] += 1
                done[2] += len(data)
            return
        except Exception as e:
            if attempt == 2:
                with lock:
                    done[1] += 1
                return


jobs = []
for z, box in PLAN:
    xs, ys = tile_range(box, z)
    cnt = len(xs) * len(ys)
    print('z%-2d  %d x %d = %d tiles' % (z, len(xs), len(ys), cnt))
    for x in xs:
        for y in ys:
            jobs.append((z, x, y))

print('total jobs', len(jobs))
with ThreadPoolExecutor(max_workers=10) as ex:
    list(ex.map(lambda a: fetch(*a), jobs))

print('ok', done[0], 'fail', done[1], 'bytes', done[2], '=> %.2f MB' % (done[2] / 1048576))

meta = {
    'source': 'Esri World Imagery (World_Imagery MapServer)',
    'attribution': '影像 © Esri, Maxar, Earthstar Geographics',
    'downloaded_at': '2026-11-06',
    'zooms': [z for z, _ in PLAN],
    'extent': {'wide': WIDE, 'core': CORE},
    'tiles': done[0],
    'failed': done[1],
    'bytes': done[2],
    'note': '离线缓存，仅供课程演示；z14-17 覆盖校园与周边，z18 只覆盖核心区',
}
with open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
print('manifest written')
