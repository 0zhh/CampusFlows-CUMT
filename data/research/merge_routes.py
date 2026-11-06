# -*- coding: utf-8 -*-
"""合并 8 条用户描的线路 → 去抖 + 抽稀 + 平滑 → 写进 station_routes.json。"""
import json, math, os

ROOT = r'D:\java大作业'
DOWN = os.path.join(os.path.expanduser('~'), 'Downloads')
OUT = os.path.join(ROOT, 'data', 'geo', 'station_routes.json')
OUT_FE = os.path.join(ROOT, 'frontend', 'src', 'data', 'station_routes.json')

SITES = {'NH-TAOYUAN': '桃苑主站', 'NH-SONGYUAN': '松苑', 'NH-MEIYUAN': '梅苑', 'NH-LANYUAN': '兰苑'}
GATES = [{'id': 'north', 'name': '北门', 'lon': 117.144061, 'lat': 34.220985},
         {'id': 'east', 'name': '东门', 'lon': 117.143900, 'lat': 34.213488}]

M_LAT = 110574.0
M_LON = 111320.0 * math.cos(math.radians(34.21))

def dist(a, b):
    return math.hypot((a[0] - b[0]) * M_LON, (a[1] - b[1]) * M_LAT)

def dedupe(pts, min_m=2.0):
    out = [pts[0]]
    for p in pts[1:]:
        if dist(out[-1], p) >= min_m:
            out.append(p)
    if len(out) == 1 and len(pts) > 1:
        out.append(pts[-1])
    return out

def dp(pts, eps_m):
    if len(pts) < 3:
        return pts
    def perp(p, a, b):
        ax, ay = (a[0] - p[0]) * M_LON, (a[1] - p[1]) * M_LAT
        bx, by = (b[0] - p[0]) * M_LON, (b[1] - p[1]) * M_LAT
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 == 0:
            return math.hypot(ax, ay)
        t = max(0.0, min(1.0, -(ax * dx + ay * dy) / L2))
        cx, cy = ax + t * dx, ay + t * dy
        return math.hypot(cx, cy)
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = perp(pts[i], pts[0], pts[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps_m:
        left = dp(pts[:idx + 1], eps_m)
        right = dp(pts[idx:], eps_m)
        return left[:-1] + right
    return [pts[0], pts[-1]]

def catmull(pts, step_m=8.0):
    """Catmull-Rom 采样，输出连续平滑折线。"""
    if len(pts) < 3:
        return pts
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        seg = dist(p1, p2)
        n = max(2, int(seg / step_m) + 1)
        for s in range(n):
            t = s / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out

def length_m(pts):
    return sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))

def load(name):
    return json.load(open(os.path.join(DOWN, name), encoding='utf-8'))

SRC = []
for f, sid in [('route-NH-TAOYUAN.json', 'NH-TAOYUAN'), ('route-NH-SONGYUAN.json', 'NH-SONGYUAN'),
               ('route-NH-MEIYUAN.json', 'NH-MEIYUAN'), ('route-NH-LANYUAN.json', 'NH-LANYUAN')]:
    SRC.append(('north', sid, load(f)['points']))
for f, sid in [('campus-routes (3).json', 'NH-TAOYUAN'), ('campus-routes (2).json', 'NH-SONGYUAN'),
               ('campus-routes (1).json', 'NH-MEIYUAN'), ('campus-routes.json', 'NH-LANYUAN')]:
    SRC.append(('east', sid, load(f)['routes'][0]['polyline']))

routes = []
report = []
for gate, sid, pts in SRC:
    raw_n = len(pts)
    pts = [(float(p[0]), float(p[1])) for p in pts]
    a = dedupe(pts, 2.0)
    b = dp(a, 5.0)
    c = catmull(b, 8.0)
    d = [(round(x, 6), round(y, 6)) for x, y in c]
    routes.append({
        'gate_id': gate,
        'site_id': sid,
        'name': SITES[sid],
        'polyline': [[p[0], p[1]] for p in d],
        'length_m': round(length_m(d)),
        'points': len(d),
    })
    report.append((gate, sid, raw_n, len(a), len(b), len(d), round(length_m(d))))

data = {
    'schema_version': '2.1',
    'generated_at': '2026-11-06',
    'status': 'annotated',
    'source': '用户在地图上手绘的 8 条线，经去重 + Douglas-Peucker(5 m) + Catmull-Rom(8 m) 平滑',
    'note': '只用于卫星底图展示；坐标为 WGS84。',
    'gates': GATES,
    'routes': routes,
}
json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(data, open(OUT_FE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

print('gate  site         raw  dedupe  dp  smooth  length_m')
for r in report:
    print('%-5s %-12s %3d  %5d %4d %6d  %6d' % r)
print('\nwritten', OUT)
