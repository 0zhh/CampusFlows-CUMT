# -*- coding: utf-8 -*-
"""算出院内配送路径并把折线存成 JSON，供前端 P6 页渲染。"""
import heapq
import json
import math
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
GEO = os.path.join(ROOT, 'data', 'geo', 'cumt_nanhu_campus.geojson')
OUT = os.path.join(ROOT, 'data', 'geo', 'station_routes.json')
MLAT = 110574.0
MLON = 111320.0 * math.cos(math.radians(34.21))
DRIVE = {'trunk', 'trunk_link', 'primary', 'primary_link', 'secondary', 'secondary_link',
         'tertiary', 'tertiary_link', 'unclassified', 'residential', 'service', 'living_street'}

g = json.load(open(GEO, encoding='utf-8'))
adj, coords = {}, {}
for f in g['features']:
    if f['properties'].get('highway') not in DRIVE:
        continue
    geo = f['geometry']
    lines = [geo['coordinates']] if geo['type'] == 'LineString' else (
        geo['coordinates'] if geo['type'] == 'MultiLineString' else [])
    for ln in lines:
        for a, b in zip(ln[:-1], ln[1:]):
            ka, kb = (round(a[0], 6), round(a[1], 6)), (round(b[0], 6), round(b[1], 6))
            if ka == kb:
                continue
            d = math.hypot((b[0] - a[0]) * MLON, (b[1] - a[1]) * MLAT)
            adj.setdefault(ka, []).append((kb, d))
            adj.setdefault(kb, []).append((ka, d))
            coords[ka], coords[kb] = a, b


def nearest(lon, lat):
    return min(coords, key=lambda k: math.hypot((coords[k][0] - lon) * MLON, (coords[k][1] - lat) * MLAT))


def dijkstra(src):
    dist, prev = {src: 0.0}, {}
    pq = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18) + 1e-9:
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist.get(v, 1e18) - 1e-9:
                dist[v], prev[v] = nd, u
                heapq.heappush(pq, (nd, v))
    return dist, prev


GATE = {'name': '北门', 'lon': 117.14430, 'lat': 34.22119}
SITES = [
    ('NH-TAOYUAN', '桃苑主站', 117.1385, 34.2178),
    ('NH-SONGYUAN', '松苑', 117.1358, 34.2194),
    ('NH-MEIYUAN', '梅苑', 117.1322, 34.2120),
    ('NH-LANYUAN', '兰苑', 117.1318, 34.2090),
]
SPEED_KMH = 15.0
routes = []
gsnap = nearest(GATE['lon'], GATE['lat'])
dist, prev = dijkstra(gsnap)
for sid, name, lon, lat in SITES:
    node = nearest(lon, lat)
    if node not in dist:
        routes.append({'site_id': sid, 'name': name, 'reachable': False, 'note': '现有路网中不连通'})
        continue
    path = [node]
    while path[-1] != gsnap and path[-1] in prev:
        path.append(prev[path[-1]])
    pts = [[coords[p][0], coords[p][1]] for p in reversed(path)]
    routes.append({
        'site_id': sid, 'name': name, 'reachable': True,
        'length_m': round(dist[node]), 'points': len(pts),
        'minutes': round(dist[node] / (SPEED_KMH * 1000 / 60), 1),
        'polyline': [[round(x, 6), round(y, 6)] for x, y in pts],
    })

bundle = {
    'schema_version': '1.0',
    'generated_at': '2026-11-04',
    'gate': GATE,
    'speed_kmh': SPEED_KMH,
    'note': '路径由 OSM 道路中心线跑 Dijkstra 得到；兰苑在现有路网中不连通，需补连接段。',
    'routes': routes,
}
json.dump(bundle, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('written', OUT)
for r in routes:
    print(' ', r['name'], r.get('length_m'), 'm', r.get('minutes'), 'min', 'points', r.get('points'))
