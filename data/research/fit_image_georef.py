# -*- coding: utf-8 -*-
"""把手册原图（1821x1123 网页地图截图）配准到 WGS84。

拿 OSM 的主干/次干/支路去匹配图中的白色道路像素。三条约束防跑飞：
  1) 比例尺限定在 1.8e-5 ~ 2.4e-5 度/像素（由校区 1.76 km 南北跨度必须装进 1123 px 推出）
  2) 只膨胀 1 像素，评分 = 命中率 - 掩膜密度（随机摆放得 0 分）
  3) 只用车行道路，不用人行小径（图上人行道不是白色，会拖低命中率）
"""
import json
import math

import numpy as np
from PIL import Image

IMG = r'D:\java大作业\data\maps\cumtlive_logistics_locations_reddots.png'
GEO = r'D:\java大作业\data\geo\cumt_nanhu_campus.geojson'
OUT = r'D:\java大作业\.probe\georef.json'

LON_PER_LAT = 110574.0 / (111320.0 * math.cos(math.radians(34.21)))
MAJOR = {'trunk', 'trunk_link', 'primary', 'primary_link', 'secondary', 'secondary_link',
         'tertiary', 'tertiary_link'}
MINOR = {'unclassified', 'residential', 'service', 'living_street', 'road'}

im = Image.open(IMG).convert('RGB')
W, H = im.size
arr = np.asarray(im).astype(np.int16)
R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
road = (R >= 244) & (G >= 244) & (B >= 244)


def dilate(m, r=1):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx or dy:
                out |= np.roll(np.roll(m, dy, axis=0), dx, axis=1)
    return out


road_d = dilate(road, 1)
DENS = float(road_d.mean())
print('road px %d (%.1f%%) dilated %.1f%%' % (road.sum(), 100 * road.mean(), 100 * DENS))

g = json.load(open(GEO, encoding='utf-8'))
major, minor = [], []
for f in g['features']:
    hw = f['properties'].get('highway')
    if not hw:
        continue
    geo = f['geometry']
    lines = [geo['coordinates']] if geo['type'] == 'LineString' else (
        geo['coordinates'] if geo['type'] == 'MultiLineString' else [])
    bucket = major if hw in MAJOR else (minor if hw in MINOR else None)
    if bucket is None:
        continue
    for ln in lines:
        for a, b in zip(ln[:-1], ln[1:]):
            d = math.hypot((b[0] - a[0]) * 92000, (b[1] - a[1]) * 110574)
            n = max(1, int(d // 10))
            for i in range(n):
                t = i / n
                bucket.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
major = np.array(major)
minor = np.array(minor)
print('major samples %d  minor samples %d' % (len(major), len(minor)))

CAMP_LON, CAMP_LAT = 117.13867, 34.21644


def ev(k, lon0, lat0):
    tot = 0.0
    n = 0
    for pts, w in ((major, 1.0), (minor, 0.35)):
        px = (pts[:, 0] - lon0) / (k * LON_PER_LAT)
        py = (lat0 - pts[:, 1]) / k
        ins = (px >= 0) & (px < W - 1) & (py >= 0) & (py < H - 1)
        if ins.mean() < 0.98:
            return -9.0, 0.0
        xi = px[ins].astype(int)
        yi = py[ins].astype(int)
        tot += w * road_d[yi, xi].mean()
        n += w
    hit = tot / n
    return hit - DENS, hit


best = (-9.0, None)
rows = []
for k in np.linspace(1.80e-5, 2.40e-5, 9):
    for cx in np.linspace(0.40, 0.80, 21):
        for cy in np.linspace(0.35, 0.75, 21):
            lon0 = CAMP_LON - cx * W * k * LON_PER_LAT
            lat0 = CAMP_LAT + cy * H * k
            s, hit = ev(k, lon0, lat0)
            rows.append((s, k, lon0, lat0, hit, cx, cy))
            if s > best[0]:
                best = (s, (k, lon0, lat0, hit))
rows.sort(key=lambda r: -r[0])
print('top 8 coarse:')
for r in rows[:8]:
    print('  score=%+.3f k=%.5e hit=%.3f cx=%.2f cy=%.2f' % (r[0], r[1], r[4], r[5], r[6]))

k, lon0, lat0, hit = best[1]
for step in (90, 30, 10, 3):
    b = (-9.0, hit)
    for dx in np.linspace(-step, step, 7):
        for dy in np.linspace(-step, step, 7):
            l0 = lon0 + dx * k * LON_PER_LAT
            t0 = lat0 + dy * k
            s, h = ev(k, l0, t0)
            if s > b[0]:
                b = (s, h)
                best = (s, (k, l0, t0, h))
    k, lon0, lat0, hit = best[1]
    print('refine %2d -> score=%+.3f hit=%.3f k=%.6e lon0=%.7f lat0=%.7f' % (step, best[0], hit, k, lon0, lat0))

DOTS = {'NH-TAOYUAN': (1396.5, 517.5), 'NH-SONGYUAN': (839.6, 297.5),
        'NH-MEIYUAN': (377.5, 576.5), 'NH-LANYUAN': (228.5, 977.5)}
res = {'transform': {'lon0': lon0, 'lat0': lat0, 'deg_lat_per_px': k,
                     'deg_lon_per_px': k * LON_PER_LAT, 'image': [W, H]},
       'quality': {'road_hit': hit, 'mask_density': DENS}, 'sites': {}}
for sid, (x, y) in DOTS.items():
    lon = lon0 + x * k * LON_PER_LAT
    lat = lat0 - y * k
    res['sites'][sid] = {'image_pixels': [x, y], 'wgs84': [round(lat, 6), round(lon, 6)]}
    print('%s px=(%.1f,%.1f) -> %.6f, %.6f' % (sid, x, y, lat, lon))
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('saved')
