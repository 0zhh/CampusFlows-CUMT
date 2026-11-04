# -*- coding: utf-8 -*-
"""从现有 JSON 生成 MySQL 种子脚本 V2（基础）与 V3（体量）。

保证：JSON 与库里的数一致；脚本结尾做总量校验。
"""
import json
import os
import random
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SC = os.path.join(ROOT, 'data', 'demo', 'scenarios.json')
LAY = os.path.join(ROOT, 'data', 'geo', 'station_layouts.json')
PRM = os.path.join(ROOT, 'data', 'params', 'param_registry.json')
OUT2 = os.path.join(ROOT, 'db', 'migration', 'V2__seed_base.sql')
OUT3 = os.path.join(ROOT, 'db', 'migration', 'V3__seed_volume.sql')

scen = json.load(open(SC, encoding='utf-8'))
lay = json.load(open(LAY, encoding='utf-8'))
prm = json.load(open(PRM, encoding='utf-8'))

SITES = [
    ('NH-TAOYUAN', '桃苑物流服务中心', 'main_hub', '08:30', '18:30', 19200, 16320, 14320, 298, 0.80, 2, 'observed', 34.2178, 117.1385),
    ('NH-SONGYUAN', '松苑无人菜鸟驿站', 'unmanned', '07:00', '23:30', 2500, 2125, 480, 197, 0.80, 1, 'assumed', 34.2194, 117.1358),
    ('NH-MEIYUAN', '梅苑无人菜鸟驿站', 'unmanned', '07:00', '23:30', 2230, 1895, 430, 167, 0.80, 1, 'assumed', 34.2120, 117.1322),
    ('NH-LANYUAN', '兰苑无人菜鸟驿站', 'unmanned', '07:00', '23:30', 1770, 1505, 350, 137, 0.80, 1, 'assumed', 34.2090, 117.1318),
]
CARRIERS = [
    ('SF', '顺丰'), ('JD', '京东'), ('ZT', '中通'), ('YT', '圆通'),
    ('YD', '韵达'), ('ST', '申通'), ('EMS', '邮政EMS'), ('OTHER', '其他'),
]
CARRIER_W = [0.12, 0.10, 0.18, 0.15, 0.14, 0.11, 0.08, 0.12]


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


def batch_insert(table, cols, rows, batch=500):
    out = []
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        out.append('INSERT INTO %s (%s) VALUES\n%s;' % (
            table, ', '.join(cols), ',\n'.join('(' + ', '.join(r) + ')' for r in chunk)))
    return '\n'.join(out)


# ---------------- V2：基础数据 ----------------
L2 = ['SET NAMES utf8mb4;', '']

L2.append('-- 站点')
L2.append(batch_insert('site',
    ['id', 'name', 'role', 'open_time', 'close_time', 'physical_slots', 'kappa_i', 'kappa_q',
     'capacity_per_bucket', 'aisle_m', 'counters', 'physical_source', 'lat', 'lng'],
    [[q(s[0]), q(s[1]), q(s[2]), q(s[3]), q(s[4]), str(s[5]), str(s[6]), str(s[7]),
      str(s[8]), str(s[9]), str(s[10]), q(s[11]), str(s[12]), str(s[13])] for s in SITES]))

L2.append('-- 承运商')
L2.append(batch_insert('carrier', ['code', 'name'], [[q(c[0]), q(c[1])] for c in CARRIERS]))

L2.append('-- 场景')
L2.append(batch_insert('scenario', ['id', 'name', 'day_index', 'note'],
    [[q(s['scenario_id']), q(s['name']), str(s.get('day_index', 1)), q(s.get('note', '')[:250])]
     for s in scen['scenarios']]))

L2.append('-- 场景站点参数')
rows = []
for s in scen['scenarios']:
    for site in s['sites']:
        p = site['params']
        rows.append([q(s['scenario_id']), q(site['site_id']), str(p['capacity_per_bucket']),
                     str(p['kappa_q']), str(p['kappa_i']), str(p['i0']), str(p.get('counters', 1))])
L2.append(batch_insert('scenario_site_param',
    ['scenario_id', 'site_id', 'capacity_per_bucket', 'kappa_q', 'kappa_i', 'i0', 'counters'], rows))

L2.append('-- 逐桶需求（396 行）')
rows = []
for s in scen['scenarios']:
    for site in s['sites']:
        for d in site['demand']:
            rows.append([q(s['scenario_id']), q(site['site_id']), q(d['bucket']),
                         str(d['arrivals']), str(d['capacity']), str(d['pickups'])])
L2.append(batch_insert('demand_bucket',
    ['scenario_id', 'site_id', 'bucket', 'arrivals', 'capacity', 'pickups'], rows))

L2.append('-- 参数版本')
stats = prm.get('stats', {})
payload = json.dumps(prm['params'], ensure_ascii=False)
L2.append(batch_insert('param_version',
    ['version', 'created_at', 'observed_cnt', 'public_cnt', 'assumed_cnt', 'total_cnt', 'payload'],
    [[q('1.0'), q('2026-11-04 00:00:00'), str(stats.get('observed', 0)), str(stats.get('public', 0)),
      str(stats.get('assumed', 0)), str(prm.get('count', 0)), q(payload)]]))

L2.append('-- 工单（演示初始四条）')
WOS = [
    ('WO-001', 'NH-SONGYUAN', 'exceed', 'open', '14:30', '松苑 待取区超限', '在架件数越过运营上限，需引导取件或扩临时周转区'),
    ('WO-002', 'NH-MEIYUAN', 'exceed', 'doing', '15:00', '梅苑 待取区超限', '已开放临时待取区，持续跟进'),
    ('WO-003', 'NH-LANYUAN', 'watch', 'closed', '16:00', '兰苑 待取区接近上限', '高峰平稳度过，工单闭环'),
    ('WO-004', 'NH-TAOYUAN', 'watch', 'open', '15:30', '桃苑 待取区接近上限', '按第 7 天水位预置的观察工单'),
]
L2.append(batch_insert('work_order',
    ['id', 'site_id', 'kind', 'status', 'bucket', 'title', 'detail', 'created_at', 'updated_at'],
    [[q(w[0]), q(w[1]), q(w[2]), q(w[3]), q(w[4]), q(w[5]), q(w[6]),
      q('2026-11-04 08:00:00'), q('2026-11-04 08:00:00')] for w in WOS]))

L2.append('-- 工单事件（每张工单的建立与流转）')
ev = []
for i, w in enumerate(WOS):
    ev.append([q(w[0]), 'NULL', q(w[3]), q('系统'), q('2026-11-04 08:00:00'), q('仿真监测自动建单')])
    if w[3] in ('doing', 'closed'):
        ev.append([q(w[0]), q('open'), q('doing'), q('调度员'), q('2026-11-04 09:15:00'), q('已安排人手')])
    if w[3] == 'closed':
        ev.append([q(w[0]), q('doing'), q('closed'), q('站点值守'), q('2026-11-04 17:40:00'), q('高峰平稳度过')])
L2.append(batch_insert('workorder_event',
    ['wo_id', 'from_status', 'to_status', 'actor', 'at_time', 'note'], ev))

L2.append('-- 一次历史仿真运行（S2 第 7 天）+ 逐桶结果')
s2 = next(s for s in scen['scenarios'] if s['scenario_id'] == 'S2-PEAK')
peak_i = max(r['i'] for r in s2['timeline'] for r in r['sites'])
risk = sum(1 for r in s2['timeline'] for x in r['sites'] if x['risk_q'] or x['risk_i'])
L2.append('INSERT INTO simulation_run (scenario_id, seed, param_version, created_at, peak_i, risk_buckets, note) '
          'VALUES (%s, 42, %s, %s, %d, %d, %s);' % (q('S2-PEAK'), q('1.0'), q('2026-11-04 08:00:00'), peak_i, risk, q('种子运行')))
L2.append('SET @run_id := LAST_INSERT_ID();')
res_rows = []
for t in s2['timeline']:
    for x in t['sites']:
        res_rows.append(['@run_id', q(x.get('site_id', '')), 'NULL', 'NULL', 'NULL', 'NULL', 'NULL', 'NULL', 'NULL'])
L2.append('-- 逐桶结果改用显式 run_id 生成，见下方 INSERT')
res_rows = []
for t in s2['timeline']:
    for idx, x in enumerate(t['sites']):
        sid = s2['sites'][idx]['site_id']
        res_rows.append(['@run_id', q(sid), q(t['bucket']), str(x['q']), str(x['i']), str(x['s']),
                         str(x['p']), str(x['unmet']), '1' if x['risk_q'] else '0', '1' if x['risk_i'] else '0'])
L2.append(batch_insert('sim_result',
    ['run_id', 'site_id', 'bucket', 'q', 'i', 's', 'p', 'unmet', 'risk_q', 'risk_i'], res_rows))

open(OUT2, 'w', encoding='utf-8').write('\n'.join(L2))
print('V2 written', os.path.getsize(OUT2), 'bytes')

# ---------------- V3：体量与空间 ----------------
L3 = ['SET NAMES utf8mb4;', '']
tao = next(s for s in lay['stations'] if s['station_id'] == 'NH-TAOYUAN')

L3.append('-- 货架排（48 排）')
rows = []
for r in tao['rows']:
    rows.append([q(r['row_id']), q('NH-TAOYUAN'), q(r['zone_id']), str(r['col']),
                 str(r['row_in_col']), str(r['x_m']), str(r['y_m']), str(r['length_m']),
                 str(round(r['depth_m'], 2)), q(r['managed_by'])])
L3.append(batch_insert('rack_row',
    ['id', 'site_id', 'zone_id', 'col_no', 'row_no', 'x_m', 'y_m', 'length_m', 'depth_m', 'managed_by'], rows))

L3.append('-- 货架（240 个）')
rows, bays = [], []
for r in tao['rows']:
    for b in (r['left_bays'] + r['right_bays']):
        bays.append(b)
        rows.append([q('S-%d' % b), q(r['row_id']), str(b), str(r['tiers']), str(r['slots_per_tier'])])
L3.append(batch_insert('shelf', ['id', 'row_id', 'bay_no', 'tiers', 'slots_per_tier'], rows))

L3.append('-- 包裹（2000 条抽样）')
rnd = random.Random(20261104)
CARRIER_CODES = [c[0] for c in CARRIERS]

def pick_carrier():
    return rnd.choices(CARRIER_CODES, weights=CARRIER_W, k=1)[0]

parcels = []
for i in range(2000):
    pid = 'P%06d' % (i + 1)
    parcels.append(pid)

slots = []
codes = []
bay_tier_cell = []
for r in tao['rows']:
    for b in (r['left_bays'] + r['right_bays']):
        for t in range(1, int(r['tiers']) + 1):
            for c in range(1, int(r['slots_per_tier']) + 1):
                bay_tier_cell.append((b, t, c))

occupied = rnd.sample(bay_tier_cell, 2000)
L3.append('-- 取件码与包裹：占用 2000 个储位')
pcols = ['id', 'site_id', 'carrier_code', 'size', 'batch_id', 'arrived_at', 'shelved_at', 'picked_at', 'status']
prow = []
ccols = ['code', 'site_id', 'parcel_id', 'issued_at']
crow = []
seq_by_rack = {}
for i, (b, t, c) in enumerate(sorted(occupied)):
    pid = parcels[i]
    car = pick_carrier()
    size = rnd.choice(['S', 'S', 'M', 'M', 'L'])
    batch = 'B%d' % rnd.randint(1, 3)
    arr = '2026-11-04 0%d:%02d:00' % (rnd.randint(8, 10), rnd.randint(0, 59))
    sh = '2026-11-04 1%d:%02d:00' % (rnd.randint(0, 2), rnd.randint(0, 59))
    prow.append([q(pid), q('NH-TAOYUAN'), q(car), q(size), q(batch), q(arr), q(sh), 'NULL', q('shelved')])
    seq = seq_by_rack.get((b, t), 0) + 1
    seq_by_rack[(b, t)] = seq
    code = '%d-%d-%04d' % (b, t, 1000 + (i % 9000))
    crow.append([q(code), q('NH-TAOYUAN'), q(pid), q(sh)])

L3.append(batch_insert('parcel', pcols, prow))
L3.append(batch_insert('pickup_code', ccols, crow))

L3.append('-- 储位（19200 个，其中 2000 个已占用）')
occ = {}
for i, (b, t, c) in enumerate(sorted(occupied)):
    occ[(b, t, c)] = parcels[i]

srows = []
for r in tao['rows']:
    for b in (r['left_bays'] + r['right_bays']):
        for t in range(1, int(r['tiers']) + 1):
            for c in range(1, int(r['slots_per_tier']) + 1):
                pid = occ.get((b, t, c))
                srows.append([q('S-%d-%d-%d' % (b, t, c)), q('S-%d' % b), str(t), str(c),
                              q(pid) if pid else 'NULL'])
L3.append(batch_insert('slot', ['id', 'shelf_id', 'tier', 'cell_no', 'parcel_id'], srows))

open(OUT3, 'w', encoding='utf-8').write('\n'.join(L3))
print('V3 written', os.path.getsize(OUT3), 'bytes')

# ---------------- 校验 ----------------
total_s2 = sum(d['arrivals'] for s in s2['sites'] for d in s['demand'])
print('check  demand_bucket rows  =', sum(len(s['demand']) for sc in scen['scenarios'] for s in sc['sites']))
print('check  shelf rows          =', len(bays), 'unique bays', len(set(bays)))
print('check  slot rows           =', len(srows))
print('check  parcels / codes     =', len(prow), '/', len(crow))
print('check  S2 arrivals total   =', total_s2)
print('check  demand rows written =', sum(len(s['demand']) for sc in scen['scenarios'] for s in sc['sites']))
jd_bays = sum(len(r['left_bays']) + len(r['right_bays']) for r in tao['rows'] if r['managed_by'] == 'JD')
print('check  JD shelves          =', jd_bays)
