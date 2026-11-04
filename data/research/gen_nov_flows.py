# -*- coding: utf-8 -*-
"""生成 11 月 1 日 — 11 月 11 日的到件（入校）与取件（出库）10 分钟粒度数据。

口径与 data/demo/scenarios.json 保持一致：
  · 峰值日（11-11）四站到件合计 13,640 件、取件合计 9,300 件
  · 站点份额 桃苑 0.34 / 松苑 0.26 / 梅苑 0.22 / 兰苑 0.18
  · 到件日曲线呈"两波"：11/1—11/3 第一波回落，11/4—11/9 日常，11/11 峰值
  · 营业时间外到件/取件均为 0（到件允许 06:00 起，取件按各站营业时间）
"""
import csv
import json
import os
from datetime import date, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT_DIR = os.path.join(ROOT, 'data', 'demo')
os.makedirs(OUT_DIR, exist_ok=True)

START = date(2026, 11, 1)
DAYS = 11                      # 11-01 … 11-11
STEP_MIN = 10
SLOTS = 24 * 60 // STEP_MIN    # 144

PEAK_ARRIVALS = 17050
PEAK_PICKUPS = 11625
SHARE = {'NH-TAOYUAN': 0.34, 'NH-SONGYUAN': 0.26, 'NH-MEIYUAN': 0.22, 'NH-LANYUAN': 0.18}
NAMES = {'NH-TAOYUAN': '桃苑物流服务中心', 'NH-SONGYUAN': '松苑无人菜鸟驿站',
         'NH-MEIYUAN': '梅苑无人菜鸟驿站', 'NH-LANYUAN': '兰苑无人菜鸟驿站'}
HOURS = {'NH-TAOYUAN': ('08:30', '18:30'), 'NH-SONGYUAN': ('07:00', '23:30'),
         'NH-MEIYUAN': ('07:00', '23:30'), 'NH-LANYUAN': ('07:00', '23:30')}

# 日系数：两波 + 间歇 + 峰值
DAY_FACTOR = [0.95, 0.88, 0.72, 0.58, 0.56, 0.57, 0.59, 0.61, 0.60, 0.78, 1.00]

# 到件日内曲线（10 分钟粒度）：06:00—22:00 有车，早班/午间/傍晚三个波峰
def arrival_weights():
    w = []
    for i in range(SLOTS):
        h = (i * STEP_MIN) / 60.0
        if h < 6.0 or h >= 22.0:
            w.append(0.0)
        elif h < 9.0:
            w.append(0.35 + (h - 6) * 0.45)
        elif h < 11.0:
            w.append(1.70)
        elif h < 13.0:
            w.append(0.85)
        elif h < 15.0:
            w.append(1.55)
        elif h < 17.0:
            w.append(1.10)
        elif h < 19.0:
            w.append(1.45)
        else:
            w.append(max(0.15, 1.0 - (h - 19) * 0.28))
    return w

# 取件日内曲线：按课程表（8:00-12:00 / 14:00-18:00 / 19:00-20:45 上课）
# 学生只有课间才来取件 → 四个峰：早课前、午休、晚饭、晚课后；上课时段是低谷
CLASS_BLOCKS = [(8.0, 12.0), (14.0, 18.0), (19.0, 20.75)]
PEAK_WINDOWS = [
    (7.0, 8.0, 0.55, '早课前'),
    (12.0, 14.0, 1.00, '午休'),
    (18.0, 19.0, 0.85, '晚饭'),
    (20.75, 23.0, 0.95, '晚课后'),
]
TROUGH = 0.07          # 上课时段的基础流量
RAMP_MIN = 12          # 边界处 12 分钟内线性过渡，避免生硬的台阶


def base_weight(h):
    for a, b, w, _ in PEAK_WINDOWS:
        if a <= h < b:
            return w
    for a, b in CLASS_BLOCKS:
        if a <= h < b:
            return TROUGH
    return 0.0


def pickup_weights(open_h, close_h):
    raw = []
    for i in range(SLOTS):
        h = (i * STEP_MIN) / 60.0
        if h < open_h or h >= close_h:
            raw.append(0.0)
            continue
        # 在 ±RAMP_MIN 内对阶梯做线性过渡
        acc, n = 0.0, 0
        for k in range(-RAMP_MIN, RAMP_MIN + 1, 3):
            acc += base_weight(min(23.99, max(0.0, h + k / 60.0)))
            n += 1
        raw.append(acc / n)
    return raw


def parse_hhmm(s):
    h, m = s.split(':')
    return int(h) + int(m) / 60.0


def round_preserve(total, weights):
    raw = [total * x for x in weights]
    base = [int(x // 1) for x in raw]
    rest = total - sum(base)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - base[i], reverse=True)
    for k in range(rest):
        base[order[k % len(order)]] += 1
    return base


W_A = arrival_weights()
sum_wa = sum(W_A)
W_A = [x / sum_wa for x in W_A]

W_P = {}
for sid, (o, c) in HOURS.items():
    w = pickup_weights(parse_hhmm(o), parse_hhmm(c))
    s = sum(w)
    W_P[sid] = [x / s for x in w]


def hhmm(i):
    m = i * STEP_MIN
    return '%02d:%02d' % (m // 60, m % 60)


rows = []                 # (date, time, site, inbound, outbound)
campus = []               # (date, time, total_inbound)
daily = []

for d in range(DAYS):
    day = START + timedelta(days=d)
    f = DAY_FACTOR[d]
    a_total = int(round(PEAK_ARRIVALS * f))
    p_total = int(round(PEAK_PICKUPS * f))

    # 按份额拆到站，用最大余数保证合计精确
    a_sites = round_preserve(a_total, [SHARE[s] for s in SHARE])
    p_sites = round_preserve(p_total, [SHARE[s] for s in SHARE])

    per_site = {}
    for idx, sid in enumerate(SHARE):
        a_series = round_preserve(a_sites[idx], W_A)
        p_series = round_preserve(p_sites[idx], W_P[sid])
        per_site[sid] = (a_series, p_series)

    for i in range(SLOTS):
        total_a = 0
        for sid in SHARE:
            a, p = per_site[sid]
            total_a += a[i]
            rows.append((day.isoformat(), hhmm(i), sid, a[i], p[i]))
        campus.append((day.isoformat(), hhmm(i), total_a))

    daily.append({
        'date': day.isoformat(),
        'factor': f,
        'arrivals': a_total,
        'pickups': p_total,
        'by_site': {sid: {'arrivals': a_sites[k], 'pickups': p_sites[k]}
                    for k, sid in enumerate(SHARE)},
    })

# ---------- 输出 1：分站长表 ----------
p1 = os.path.join(OUT_DIR, 'nov_inbound_outbound_10min.csv')
with open(p1, 'w', encoding='utf-8-sig', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['date', 'time', 'site_id', 'site_name', 'inbound', 'outbound'])
    for (dd, tt, sid, a, p) in rows:
        w.writerow([dd, tt, sid, NAMES[sid], a, p])

# ---------- 输出 2：全校流入 ----------
p2 = os.path.join(OUT_DIR, 'nov_campus_inbound_10min.csv')
with open(p2, 'w', encoding='utf-8-sig', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['date', 'time', 'total_inbound'])
    for (dd, tt, a) in campus:
        w.writerow([dd, tt, a])

# ---------- 输出 3：元数据 + 日汇总 ----------
meta = {
    'schema_version': '1.0',
    'generated_at': '2026-11-04',
    'period': {'start': START.isoformat(), 'end': (START + timedelta(days=DAYS - 1)).isoformat(), 'days': DAYS},
    'granularity_minutes': STEP_MIN,
    'slots_per_day': SLOTS,
    'units': {'inbound': '件', 'outbound': '件'},
    'definition': {
        'inbound': '校外到件：当日进入校门并分配到该站的包裹数',
        'outbound': '出库：当日该站被取走的包裹数（不含退回与调拨）',
        'campus_inbound': '四站 inbound 之和',
    },
    'assumptions': [
        '峰值日（11-11）四站到件合计 13,640 件、取件合计 9,300 件，与 scenarios.json 的 S2 口径一致',
        '站点份额 桃苑 0.34 / 松苑 0.26 / 梅苑 0.22 / 兰苑 0.18',
        '日系数呈两波：11-01…11-03 第一波回落、11-04…11-09 日常、11-11 峰值',
        '到件只在 06:00—22:00 发生；取件只在各站营业时间内发生',
        '取件曲线按课程表设计：8:00-12:00、14:00-18:00、19:00-20:45 上课，这些时段是低谷',
        '取件高峰：07:00-08:00 早课前（次峰）、12:00-14:00 午休、18:00-19:00 晚饭、20:45-23:00 晚课后',
        '全部为演示数据，不代表真实业务量',
    ],
    'class_blocks': [{'start': '08:00', 'end': '12:00'}, {'start': '14:00', 'end': '18:00'},
                     {'start': '19:00', 'end': '20:45'}],
    'peak_windows': [{'start': '07:00', 'end': '08:00', 'weight': 0.55, 'label': '早课前 (次峰)'},
                     {'start': '12:00', 'end': '14:00', 'weight': 1.00, 'label': '午休 (主峰)'},
                     {'start': '18:00', 'end': '19:00', 'weight': 0.85, 'label': '晚饭 (次主峰)'},
                     {'start': '20:45', 'end': '23:00', 'weight': 0.95, 'label': '晚课后 (主峰)'}],
    'station_hours_effect': '桃苑 08:30-18:30，接不到 20:45 之后的晚课后峰；这一段全部由三个无人站承接',
    'daily': daily,
    'totals': {
        'arrivals': sum(d['arrivals'] for d in daily),
        'pickups': sum(d['pickups'] for d in daily),
    },
    'files': {
        'by_site': os.path.basename(p1),
        'campus_inbound': os.path.basename(p2),
    },
}
p3 = os.path.join(OUT_DIR, 'nov_flow_summary.json')
json.dump(meta, open(p3, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

print('rows', len(rows), 'campus rows', len(campus))
print('arrivals total', meta['totals']['arrivals'], 'pickups total', meta['totals']['pickups'])
print('peak day 11-11', [d for d in daily if d['date'] == '2026-11-11'][0])
for f in (p1, p2, p3):
    print(os.path.basename(f), os.path.getsize(f), 'bytes')
