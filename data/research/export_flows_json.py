# -*- coding: utf-8 -*-
import csv, json, os
ROOT = r'D:\java大作业'
D = os.path.join(ROOT, 'data', 'demo')
OUT = os.path.join(ROOT, 'frontend', 'src', 'data', 'nov_flows_10min.json')

rows = list(csv.DictReader(open(os.path.join(D, 'nov_inbound_outbound_10min.csv'), encoding='utf-8-sig')))
times = sorted({r['time'] for r in rows})
dates = sorted({r['date'] for r in rows})
idx = {t: i for i, t in enumerate(times)}
SITES = ['NH-TAOYUAN', 'NH-SONGYUAN', 'NH-MEIYUAN', 'NH-LANYUAN']

data = {}
for d in dates:
    data[d] = {s: {'in': [0] * len(times), 'out': [0] * len(times)} for s in SITES}
for r in rows:
    i = idx[r['time']]
    cell = data[r['date']][r['site_id']]
    cell['in'][i] = int(r['inbound'])
    cell['out'][i] = int(r['outbound'])

out = {
    'schema_version': '1.0',
    'granularity_minutes': 10,
    'dates': dates,
    'times': times,
    'sites': SITES,
    'note': '11 月 1—11 日到件/取件，10 分钟一桶；到件=入校，取件=出库',
    'data': data,
}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
print('written', OUT, os.path.getsize(OUT), 'bytes', len(dates), 'days', len(times), 'slots')
