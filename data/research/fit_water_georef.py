# -*- coding: utf-8 -*-
"""用 OSM 水面多边形与图中水体色块求相似变换（允许旋转、镜像由符号吸收）。

两点即可确定 s / theta / tx / ty，然后统计内点数。
候选模型很多但每个都很便宜，直接全枚举再取内点最多的。
"""
import itertools
import json
import math

import numpy as np

MLAT = 110574.0
MLON = 111320.0 * math.cos(math.radians(34.21))

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

OSM = np.array([
    [20067.8, 117.140498, 34.217434],
    [13520.0, 117.145024, 34.220347],
    [7637.0, 117.151596, 34.224434],
    [6329.9, 117.139250, 34.215436],
    [5207.2, 117.147169, 34.223743],
    [5056.9, 117.139990, 34.215653],
    [1756.6, 117.150945, 34.223688],
    [434.3, 117.136516, 34.215554],
], dtype=float)

ox = OSM[:, 1] * MLON
oy = OSM[:, 2] * MLAT
oa = OSM[:, 0]
ipx = IMG[:, 1]
ipy = IMG[:, 2]
iap = IMG[:, 0]

models = []
for (i, j), (i2, j2) in itertools.permutations(itertools.product(range(8), range(8)), 2):
    if i == i2:
        continue
    dmx, dmy = ox[i] - ox[i2], oy[i] - oy[i2]
    dpx, dpy = ipx[j] - ipx[j2], -(ipy[j] - ipy[j2])  # 图像 y 向下
    n2 = dpx * dpx + dpy * dpy
    if n2 < 60 * 60:
        continue
    # 复数形式：(dm) = c * (dp)，c = s * e^{i theta}
    c = complex(dmx, dmy) / complex(dpx, dpy)
    s = abs(c)
    if s < 0.25 or s > 3.5:
        continue
    th = math.atan2(c.imag, c.real)
    # 平移： osm = c * px_complex + t,  px_complex = px + i*(-py)
    zp = complex(ipx[j], -ipy[j])
    t = complex(ox[i], oy[i]) - c * zp
    inl = 0
    resid = []
    zx = c.real * ipx + c.imag * ipy + t.real
    zy = c.real * (-ipy) - c.imag * ipx + t.imag
    for a in range(8):
        d = np.hypot(zx - ox[a], zy - oy[a]) / s  # 换算成像素
        k = int(np.argmin(d))
        if d[k] < 55:
            inl += 1
            resid.append(d[k])
    if not resid:
        continue
    models.append((inl - np.mean(resid) / 55.0, inl, float(np.mean(resid)), s, th, t, i, j))

models.sort(key=lambda m: -m[0])
print('models', len(models))
for m in models[:5]:
    score, inl, mr, s, th, t, bi, bj = m
    print('  inliers=%d mean_resid=%.1f  s=%.3f m/px  theta=%.1f deg  anchor osm%d<img%d'
          % (inl, mr, s, math.degrees(th), bi, bj))

best = models[0]
_, inl, mr, s, th, t, bi, bj = best
c = complex(s * math.cos(th), s * math.sin(th))
print('\nOSM 水面投影到图上的落点：')
for a in range(8):
    z = (complex(ox[a], oy[a]) - t) / c
    px, py = z.real, -z.imag
    d = np.hypot(px - ipx, py - ipy)
    k = int(np.argmin(d))
    print('  osm%02d area=%8.0f -> (%7.1f,%7.1f)  nearest img#%d  d=%6.1f px  m2/px=%.2f'
          % (a, oa[a], px, py, k, d[k], oa[a] / iap[k]))

DOTS = {'NH-TAOYUAN': (1396.5, 517.5), 'NH-SONGYUAN': (839.6, 297.5),
        'NH-MEIYUAN': (377.5, 576.5), 'NH-LANYUAN': (228.5, 977.5)}
print()
out = {'scale_m_per_px': s, 'theta_deg': math.degrees(th), 'inliers': inl,
       'mean_resid_px': mr, 'mlon': MLON, 'mlat': MLAT,
       't': [t.real, t.imag], 'sites': {}}
for sid, (xx, yy) in DOTS.items():
    z = c * complex(xx, -yy) + t
    lon, lat = z.real / MLON, z.imag / MLAT
    out['sites'][sid] = {'image_pixels': [xx, yy], 'wgs84': [round(lat, 6), round(lon, 6)]}
    print('%s  -> %.6f, %.6f' % (sid, lat, lon))
json.dump(out, open(r'D:\java大作业\.probe\georef_rot.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
