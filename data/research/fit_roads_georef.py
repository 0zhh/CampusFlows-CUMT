# -*- coding: utf-8 -*-
"""道路配准：只保留"大连通域"的白色像素（文字白边都是小连通域，会被丢掉），
再用 OSM 车行道路去撞它。评分 = 命中率 - 掩膜密度。"""
import json
import math
from collections import deque

import numpy as np
from PIL import Image

IMG = r'D:\java大作业\data\maps\cumtlive_logistics_locations_reddots.png'
GEO = r'D:\java大作业\data\geo\cumt_nanhu_campus.geojson'
OUT = r'D:\java大作业\.probe\georef_roads.json'

MLAT = 110574.0
MLON = 111320.0 * math.cos(math.radians(34.21))

im = Image.open(IMG).convert('RGB')
W, H = im.size
a = np.asarray(im).astype(np.int16)
R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
white = (R >= 248) & (G >= 248) & (B >= 248)

# 连通域：保留大块
seen = np.zeros_like(white, dtype=bool)
keep = np.zeros_like(white, dtype=bool)
ys, xs = np.nonzero(white)
MIN = 500
for i in range(len(xs)):
    y0, x0 = ys[i], xs[i]
    if seen[y0, x0]:
        continue
    q = deque([(y0, x0)]); seen[y0, x0] = True; comp = []
    while q:
        cy, cx = q.popleft(); comp.append((cy, cx))
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < H and 0 <= nx < W and white[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; q.append((ny, nx))
    if len(comp) >= MIN:
        for cy, cx in comp:
            keep[cy, cx] = True
print('white %d (%.1f%%)  kept %d (%.1f%%)' % (white.sum(), 100 * white.mean(), keep.sum(), 100 * keep.mean()))


def dilate(m, r=2):
    o = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx or dy:
                o |= np.roll(np.roll(m, dy, axis=0), dx, axis=1)
    return o


mask = dilate(keep, 2)
DENS = float(mask.mean())
print('dilated density %.1f%%' % (100 * DENS))

g = json.load(open(GEO, encoding='utf-8'))
pts = []
for f in g['features']:
    if not f['properties'].get('highway'):
        continue
    geo = f['geometry']
    lines = [geo['coordinates']] if geo['type'] == 'LineString' else (
        geo['coordinates'] if geo['type'] == 'MultiLineString' else [])
    for ln in lines:
        for p, q2 in zip(ln[:-1], ln[1:]):
            d = math.hypot((q2[0] - p[0]) * MLON, (q2[1] - p[1]) * MLAT)
            n = max(1, int(d // 8))
            for t in range(n):
                k = t / n
                pts.append((p[0] + (q2[0] - p[0]) * k, p[1] + (q2[1] - p[1]) * k))
P = np.array(pts)
PX = P[:, 0] * MLON
PY = P[:, 1] * MLAT
print('road samples', len(P))

cx_img = (W - 1) / 2.0
cy_img = (H - 1) / 2.0


def ev(s, tx, ty):
    px = (PX - tx) / s
    py = (ty2 := (ty - PY)) / s
    ins = (px >= 1) & (px < W - 2) & (py >= 1) & (py < H - 2)
    if ins.mean() < 0.995:
        return -9.0, 0.0
    xi = px[ins].astype(int)
    yi = py[ins].astype(int)
    hit = mask[yi, xi].mean()
    return hit - DENS, hit


MX, MY = PX.mean(), PY.mean()
best = (-9.0, None)
for s in np.linspace(0.5, 2.6, 22):
    for ux in np.linspace(-0.5, 0.5, 15):
        for uy in np.linspace(-0.5, 0.5, 15):
            tx = MX - (cx_img + ux * W) * s
            ty = MY + (cy_img + uy * H) * s
            sc, hit = ev(s, tx, ty)
            if sc > best[0]:
                best = (sc, (s, tx, ty, hit))
print('coarse best score=%.3f s=%.3f hit=%.3f' % (best[0], best[1][0], best[1][3]))

s, tx, ty, hit = best[1]
for step in (60, 20, 6, 2):
    b = (-9.0, hit)
    for ds in np.linspace(-step * 0.004, step * 0.004, 5):
        for dx in np.linspace(-step, step, 7):
            for dy in np.linspace(-step, step, 7):
                ss = s + ds
                sc, h = ev(ss, tx + dx * ss, ty + dy * ss)
                if sc > b[0]:
                    b = (sc, h)
                    best = (sc, (ss, tx + dx * ss, ty + dy * ss, h))
    s, tx, ty, hit = best[1]
    print('refine %2d score=%+.3f s=%.4f hit=%.3f dens=%.3f' % (step, best[0], s, hit, DENS))

DOTS = {'NH-TAOYUAN': (1396.5, 517.5), 'NH-SONGYUAN': (839.6, 297.5),
        'NH-MEIYUAN': (377.5, 576.5), 'NH-LANYUAN': (228.5, 977.5)}
out = {'scale_m_per_px': s, 'tx': tx, 'ty': ty, 'road_hit': hit, 'mask_density': DENS, 'sites': {}}
print()
for sid, (xx, yy) in DOTS.items():
    lon = (tx + xx * s) / MLON
    lat = (ty - yy * s) / MLAT
    out['sites'][sid] = {'image_pixels': [xx, yy], 'wgs84': [round(lat, 6), round(lon, 6)]}
    print('%s -> %.6f, %.6f' % (sid, lat, lon))
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
