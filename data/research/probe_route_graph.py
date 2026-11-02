# -*- coding: utf-8 -*-
"""验证：只用现有的 OSM 道路中心线，能不能算出院内运输路径。

不引入任何新数据，看看图有多大、从校门到四站的可达性和里程。
"""
import heapq
import json
import math

MLAT = 110574.0
MLON = 111320.0 * math.cos(math.radians(34.21))

g = json.load(open(r'D:\java大作业\data\geo\cumt_nanhu_campus.geojson', encoding='utf-8'))
DRIVE = {'trunk', 'trunk_link', 'primary', 'primary_link', 'secondary', 'secondary_link',
         'tertiary', 'tertiary_link', 'unclassified', 'residential', 'service', 'living_street'}

def key(lon, lat):
    return (round(lon, 6), round(lat, 6))

adj = {}
coords = {}
n_edges = 0
for f in g['features']:
    hw = f['properties'].get('highway')
    if hw not in DRIVE:
        continue
    geo = f['geometry']
    lines = [geo['coordinates']] if geo['type'] == 'LineString' else (
        geo['coordinates'] if geo['type'] == 'MultiLineString' else [])
    for ln in lines:
        for a, b in zip(ln[:-1], ln[1:]):
            ka, kb = key(*a), key(*b)
            if ka == kb:
                continue
            d = math.hypot((b[0] - a[0]) * MLON, (b[1] - a[1]) * MLAT)
            adj.setdefault(ka, []).append((kb, d))
            adj.setdefault(kb, []).append((ka, d))
            coords[ka] = a
            coords[kb] = b
            n_edges += 1

print('可通行图：节点 %d，边 %d' % (len(adj), n_edges))

def nearest(lon, lat):
    best = None
    for k in coords:
        d = math.hypot((coords[k][0] - lon) * MLON, (coords[k][1] - lat) * MLAT)
        if best is None or d < best[0]:
            best = (d, k)
    return best

def dijkstra(src):
    dist = {src: 0.0}
    prev = {}
    pq = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18) + 1e-9:
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist.get(v, 1e18) - 1e-9:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    return dist, prev

GATES = {'北门': (117.14430, 34.22119), '南大门': (117.13412, 34.20866)}
SITES = {'桃苑': (117.1385, 34.2178), '松苑': (117.1358, 34.2194),
         '梅苑': (117.1322, 34.2120), '兰苑': (117.1318, 34.2090)}

for gname, (glon, glat) in GATES.items():
    dsnap, gnode = nearest(glon, glat)
    dist, prev = dijkstra(gnode)
    print()
    print('%s（吸附偏差 %.0f m，图节点 %s）' % (gname, dsnap, gnode))
    for sname, (slon, slat) in SITES.items():
        dsnap2, snode = nearest(slon, slat)
        if snode not in dist:
            print('  %s 不可达' % sname)
            continue
        # 还原路径长度与折点数
        path = [snode]
        while path[-1] != gnode and path[-1] in prev:
            path.append(prev[path[-1]])
        print('  %-3s 里程 %5.0f m，折点 %2d 个，站点吸附偏差 %.0f m，骑行 15km/h 约 %.1f 分钟'
              % (sname, dist[snode], len(path), dsnap2, dist[snode] / (15000 / 60)))
