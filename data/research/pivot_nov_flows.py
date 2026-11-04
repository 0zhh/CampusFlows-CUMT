# -*- coding: utf-8 -*-
"""把长表转成宽表 CSV（每行一个 10 分钟时段，每列一个站点），方便直接看。"""
import csv
import os
from collections import OrderedDict

ROOT = r'D:\java大作业'
D = os.path.join(ROOT, 'data', 'demo')
SITES = ['NH-TAOYUAN', 'NH-SONGYUAN', 'NH-MEIYUAN', 'NH-LANYUAN']
CN = {'NH-TAOYUAN': '桃苑', 'NH-SONGYUAN': '松苑', 'NH-MEIYUAN': '梅苑', 'NH-LANYUAN': '兰苑'}

rows = list(csv.DictReader(open(os.path.join(D, 'nov_inbound_outbound_10min.csv'), encoding='utf-8-sig')))

inb = OrderedDict()
outb = OrderedDict()
for r in rows:
    k = (r['date'], r['time'])
    inb.setdefault(k, {s: 0 for s in SITES})
    outb.setdefault(k, {s: 0 for s in SITES})
    inb[k][r['site_id']] = int(r['inbound'])
    outb[k][r['site_id']] = int(r['outbound'])

# ---------- 宽表 1：到件 ----------
p1 = os.path.join(D, 'nov_inbound_wide.csv')
with open(p1, 'w', encoding='utf-8-sig', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['日期', '时间'] + [CN[s] for s in SITES] + ['全校合计'])
    for (d, t), v in inb.items():
        tot = sum(v[s] for s in SITES)
        w.writerow([d, t] + [v[s] for s in SITES] + [tot])

# ---------- 宽表 2：出库 ----------
p2 = os.path.join(D, 'nov_outbound_wide.csv')
with open(p2, 'w', encoding='utf-8-sig', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['日期', '时间'] + [CN[s] for s in SITES])
    for (d, t), v in outb.items():
        w.writerow([d, t] + [v[s] for s in SITES])

# ---------- 日汇总 ----------
p3 = os.path.join(D, 'nov_daily_summary.csv')
by_day = OrderedDict()
for (d, t), v in inb.items():
    by_day.setdefault(d, {'in': {s: 0 for s in SITES}, 'out': {s: 0 for s in SITES}})
    for s in SITES:
        by_day[d]['in'][s] += v[s]
        by_day[d]['out'][s] += outb[(d, t)][s]

with open(p3, 'w', encoding='utf-8-sig', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['日期'] + ['到件-' + CN[s] for s in SITES] + ['到件-全校']
               + ['出库-' + CN[s] for s in SITES] + ['出库-四站合计'])
    for d, v in by_day.items():
        w.writerow([d] + [v['in'][s] for s in SITES] + [sum(v['in'].values())]
                   + [v['out'][s] for s in SITES] + [sum(v['out'].values())])

for f in (p1, p2, p3):
    print(os.path.basename(f), os.path.getsize(f), 'bytes')

print()
print(open(p1, encoding='utf-8-sig').read().split('\n')[0])
for line in open(p1, encoding='utf-8-sig').read().split('\n')[1:4]:
    print(line)
print('...')
print(open(p3, encoding='utf-8-sig').read().split('\n')[0])
for line in open(p3, encoding='utf-8-sig').read().split('\n')[1:4]:
    print(line)
