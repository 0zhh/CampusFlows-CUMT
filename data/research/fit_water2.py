# -*- coding: utf-8 -*-
"""用更大范围的水面（含校区外的湖）跟图上的水体色块做 2 点相似变换拟合。"""
import itertools
import json
import math

import numpy as np

MLAT = 110574.0
MLON = 111320.0 * math.cos(math.radians(34.21))

d = json.load(open(r'D:\java大作业\.probe\water_api.json', encoding='utf-8'))
osm = []
for w in d['waters']:
    a = np.array(w['coords'], dtype=float)
    if len(a) < 4:
        continue
    x = a[:, 0] * MLON
    y = a[:, 1] * MLAT
    area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    if area < 1500:
        continue
    osm.append((area, a[:, 0].mean(), a[:, 1].mean(), w['name'] or '-'))
osm.sort(key=lambda r: -r[0])
print('OSM water polygons (area, lon, lat):')
for a, lon, lat, nm in osm:
    print('  %10.0f m2  %.6f %.6f  %s' % (a, lon, lat, nm))

IMG = np.array([
    [55378, 1587.2, 1027.6],
    [21787, 697.7, 961.7],
    [10195, 1251.0, 739.0],
    [6847, 1739.3, 765.4],
    [6093, 1071.6, 624.1],
    [4360, 805.5, 788.9],
    [2900, 1365.1, 884.0],
    [2804, 911.7, 701.1],
], dtype=float)

O = np.array([[a, lon, lat] for a, lon, lat, _ in osm], dtype=float)
ox = O[:, 1] * MLON
oy = O[:, 2] * MLAT
oa = O[:, 0]
NO = len(O)
NI = len(IMG)
print('OSM', NO, 'IMG', NI)

best = None
for i, i2 in itertools.permutations(range(NO), 2):
    for j, j2 in itertools.permutations(range(NI), 2):
        dxm, dym = ox[i] - ox[i2], oy[i] - oy[i2]
        dxp, dyp = IMG[j, 1] - IMG[j2, 1], -(IMG[j, 2] - IMG[j2, 2])
        if abs(dxp) < 50 or abs(dyp) < 50:
            continue
        sx = dxm / dxp
        sy = dym / dyp
        if sx <= 0.2 or sy <= 0.2:
            continue
        s = (sx + sy) / 2
        if abs(sx - sy) / s > 0.15 or s < 0.5 or s > 3.0:
            continue
        tx = ox[i] - IMG[j, 1] * s
        ty = oy[i] + IMG[j, 2] * s
        # 内点：OSM 点落到图上的位置附近要有水体色块，且面积量级要对得上
        inl = 0
        resid = []
        for a in range(NO):
            px = (ox[a] - tx) / s
            py = (ty - oy[a]) / s
            dist = np.hypot(px - IMG[:, 1], py - IMG[:, 2])
            k = int(np.argmin(dist))
            ratio = oa[a] / IMG[k, 0]
            if dist[k] < 70 and 0.25 <= ratio <= 1.6:
                inl += 1
                resid.append(dist[k])
        if not resid:
            continue
        score = inl - np.mean(resid) / 70.0
        if best is None or score > best[0]:
            best = (score, s, tx, ty, inl, float(np.mean(resid)), i, j)

score, s, tx, ty, inl, mres, bi, bj = best
print('\nBEST inliers=%d/%d  s=%.3f m/px  mean_resid=%.1f px  (osm#%d <-> img#%d)' % (inl, NO, s, mres, bi, bj))
for a in range(NO):
    px = (ox[a] - tx) / s
    py = (ty - oy[a]) / s
    dist = np.hypot(px - IMG[:, 1], py - IMG[:, 2])
    k = int(np.argmin(dist))
    print('  osm%02d %9.0f m2 -> (%7.1f,%7.1f)  img#%d d=%5.1f  ratio=%.2f'
          % (a, oa[a], px, py, k, dist[k], oa[a] / IMG[k, 0]))

DOTS = {'NH-TAOYUAN': (1396.5, 517.5), 'NH-SONGYUAN': (839.6, 297.5),
        'NH-MEIYUAN': (377.5, 576.5), 'NH-LANYUAN': (228.5, 977.5)}
out = {'scale_m_per_px': float(s), 'inliers': inl, 'mean_resid_px': mres, 'sites': {}}
print()
for sid, (xx, yy) in DOTS.items():
    lon = (tx + xx * s) / MLON
    lat = (ty - yy * s) / MLAT
    out['sites'][sid] = {'image_pixels': [xx, yy], 'wgs84': [round(lat, 6), round(lon, 6)]}
    print('%s -> %.6f, %.6f' % (sid, lat, lon))
json.dump(out, open(r'D:\java大作业\.probe\georef_water2.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
