# -*- coding: utf-8 -*-
"""道路配准：用"精确率与召回率的几何平均"做评分。

对二值图，重合格数 C 同时正比于精确率 (C/N_tmpl) 与召回率 (C/N_img)，
所以 F1 ∝ C / sqrt(N_tmpl)。这一步归一化是关键，
否则搜索会一路退化成"把矢量图缩成一个小点"。
"""
import json
import math

import numpy as np
from PIL import Image

IMG = r'D:\java大作业\data\maps\cumtlive_logistics_locations_reddots.png'
GEO = r'D:\java大作业\data\geo\cumt_nanhu_campus.geojson'
MLAT = 110574.0
MLON = 111320.0 * math.cos(math.radians(34.21))
STEP = 3

im = Image.open(IMG).convert('RGB')
W, H = im.size
a = np.asarray(im).astype(np.int16)
R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
white = (R >= 248) & (G >= 248) & (B >= 248)


def erode(m, r=1):
    o = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx or dy:
                o &= np.roll(np.roll(m, dy, axis=0), dx, axis=1)
    return o


def dilate(m, r=1):
    o = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx or dy:
                o |= np.roll(np.roll(m, dy, axis=0), dx, axis=1)
    return o


road = dilate(erode(white, 1), 2)

h2, w2 = H // STEP, W // STEP
img = road[:h2 * STEP, :w2 * STEP].reshape(h2, STEP, w2, STEP).mean(axis=(1, 3))
img = (img > 0.28).astype(np.float32)
N_IMG = float(img.sum())
print('road cells img=%d (%.1f%%)' % (N_IMG, 100 * N_IMG / (h2 * w2)))

g = json.load(open(GEO, encoding='utf-8'))
pts = []
for f in g['features']:
    if not f['properties'].get('highway'):
        continue
    geo = f['geometry']
    lines = [geo['coordinates']] if geo['type'] == 'LineString' else (
        geo['coordinates'] if geo['type'] == 'MultiLineString' else [])
    for ln in lines:
        for p, q in zip(ln[:-1], ln[1:]):
            d = math.hypot((q[0] - p[0]) * MLON, (q[1] - p[1]) * MLAT)
            n = max(1, int(d // 4))
            for t in range(n):
                k = t / n
                pts.append((p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k))
P = np.array(pts)
MX = P[:, 0] * MLON
MY = P[:, 1] * MLAT

FX = np.fft.rfft2(img, s=(2 * h2, 2 * w2))
res = []
for s in np.arange(0.5, 4.01, 0.05):
    u = (MX - MX.mean()) / (s * STEP)
    v = -(MY - MY.mean()) / (s * STEP)
    cell = np.zeros((2 * h2, 2 * w2), dtype=np.float32)
    iu = np.round(u + w2 / 2).astype(int)
    iv = np.round(v + h2 / 2).astype(int)
    ok = (iu >= 0) & (iu < w2) & (iv >= 0) & (iv < h2)
    np.add.at(cell, (iv[ok], iu[ok]), 1.0)
    cell = dilate(cell > 0, 1).astype(np.float32)
    n_t = float(cell.sum())
    if n_t < 200:
        continue
    F = np.fft.rfft2(cell)
    corr = np.fft.irfft2(FX * np.conj(F), s=(2 * h2, 2 * w2))
    k = int(np.argmax(corr))
    py, px = divmod(k, 2 * w2)
    c = corr[py, px]
    res.append((c / math.sqrt(n_t), float(s), px, py, float(c), n_t))

res.sort(reverse=True)
print('top 10 (score, s, shift, overlap, n_tmpl):')
for r in res[:10]:
    print('  score=%6.2f s=%.2f shift=(%d,%d) overlap=%5.0f  n_t=%5.0f  prec=%.2f rec=%.2f'
          % (r[0], r[1], r[2], r[3], r[4], r[5], r[4] / r[5], r[4] / N_IMG))

score, s, px, py, c, n_t = res[0]
shift_x = px - 2 * w2 if px > w2 else px
shift_y = py - 2 * h2 if py > h2 else py
px_img = (w2 / 2.0 + shift_x) * STEP
py_img = (h2 / 2.0 + shift_y) * STEP
tx = MX.mean() - px_img * s
ty = MY.mean() + py_img * s
print('\nbest s=%.3f  校区路网质心 -> (%.0f, %.0f) px   prec=%.2f rec=%.2f' % (s, px_img, py_img, c / n_t, c / N_IMG))

DOTS = {'NH-TAOYUAN': (1396.5, 517.5), 'NH-SONGYUAN': (839.6, 297.5),
        'NH-MEIYUAN': (377.5, 576.5), 'NH-LANYUAN': (228.5, 977.5)}
out = {'scale_m_per_px': float(s), 'osm_centroid_px': [float(px_img), float(py_img)],
       'precision': c / n_t, 'recall': c / N_IMG, 'sites': {}}
print()
for sid, (xx, yy) in DOTS.items():
    lon = (tx + xx * s) / MLON
    lat = (ty - yy * s) / MLAT
    out['sites'][sid] = {'image_pixels': [xx, yy], 'wgs84': [round(lat, 6), round(lon, 6)]}
    print('%s -> %.6f, %.6f' % (sid, lat, lon))
json.dump(out, open(r'D:\java大作业\.probe\georef_fft.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
