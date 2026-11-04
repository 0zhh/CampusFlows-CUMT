# -*- coding: utf-8 -*-
"""校验 11 月流量数据，并画一张预览图。"""
import csv
import json
import os
from collections import defaultdict

from PIL import Image, ImageDraw, ImageFont

ROOT = r'D:\java大作业'
D = os.path.join(ROOT, 'data', 'demo')
rows = list(csv.DictReader(open(os.path.join(D, 'nov_inbound_outbound_10min.csv'), encoding='utf-8-sig')))
camp = list(csv.DictReader(open(os.path.join(D, 'nov_campus_inbound_10min.csv'), encoding='utf-8-sig')))
meta = json.load(open(os.path.join(D, 'nov_flow_summary.json'), encoding='utf-8'))

errs = []

# 1) 行数与结构
if len(rows) != 11 * 144 * 4:
    errs.append('rows %d' % len(rows))
if len(camp) != 11 * 144:
    errs.append('campus rows %d' % len(camp))

# 2) 非负
neg = [r for r in rows if int(r['inbound']) < 0 or int(r['outbound']) < 0]
if neg:
    errs.append('negative %d' % len(neg))

# 3) 营业时间外必须为 0
OPEN = {'NH-TAOYUAN': ('08:30', '18:30')}
for r in rows:
    t = r['time']
    o, c = OPEN.get(r['site_id'], ('07:00', '23:30'))
    out = int(r['outbound'])
    if (t < o or t >= c) and out != 0:
        errs.append('outbound outside hours %s %s %s' % (r['date'], r['site_id'], t))
        break
for r in rows:
    t = r['time']
    if (t < '06:00' or t >= '22:00') and int(r['inbound']) != 0:
        errs.append('inbound outside 06-22 %s %s' % (r['date'], t))
        break

# 4) 校园总量 = 四站之和
agg = defaultdict(int)
for r in rows:
    agg[(r['date'], r['time'])] += int(r['inbound'])
for c in camp:
    if agg[(c['date'], c['time'])] != int(c['total_inbound']):
        errs.append('campus mismatch %s %s' % (c['date'], c['time']))
        break

# 5) 日汇总与元数据一致
daily = defaultdict(lambda: {'in': 0, 'out': 0})
for r in rows:
    daily[r['date']]['in'] += int(r['inbound'])
    daily[r['date']]['out'] += int(r['outbound'])
for d in meta['daily']:
    if daily[d['date']]['in'] != d['arrivals'] or daily[d['date']]['out'] != d['pickups']:
        errs.append('daily mismatch %s' % d['date'])
        break

print('errors:', len(errs), errs[:3])
print('days', len(daily), 'total in', sum(v['in'] for v in daily.values()), 'out', sum(v['out'] for v in daily.values()))

# ---------- 预览图 ----------
W, H = 1800, 1100
BG = (250, 251, 253)
img = Image.new('RGB', (W, H), BG)
dr = ImageDraw.Draw(img)

def font(sz, bold=False):
    p = r'C:\Windows\Fonts\msyhbd.ttc' if bold else r'C:\Windows\Fonts\msyh.ttc'
    try:
        return ImageFont.truetype(p, sz)
    except Exception:
        return ImageFont.load_default()

F_T = font(34, True); F = font(17); F_S = font(14); F_B = font(15, True)
dr.text((60, 28), '11 月 1 日 — 11 日 到件与取件（10 分钟粒度）', fill=(24, 30, 40), font=F_T)
dr.text((60, 76), '到件合计 %s 件 · 取件合计 %s 件 · 每日 144 个 10 分钟桶' %
        (format(sum(v['in'] for v in daily.values()), ','), format(sum(v['out'] for v in daily.values()), ',')),
        fill=(110, 122, 140), font=F)

# 上图：每日总量柱状
x0, y0, w, h = 90, 150, 1620, 340
days = sorted(daily)
maxv = max(max(v['in'], v['out']) for v in daily.values())
dr.line([x0, y0 + h, x0 + w, y0 + h], fill=(210, 216, 226), width=2)
bw = w / len(days)
for i, d in enumerate(days):
    inb, outb = daily[d]['in'], daily[d]['out']
    bx = x0 + i * bw
    hin = inb / maxv * (h - 40)
    hout = outb / maxv * (h - 40)
    dr.rectangle([bx + bw * 0.12, y0 + h - hin, bx + bw * 0.44, y0 + h], fill=(58, 96, 168))
    dr.rectangle([bx + bw * 0.52, y0 + h - hout, bx + bw * 0.84, y0 + h], fill=(196, 132, 48))
    dr.text((bx + bw * 0.12, y0 + h + 8), d[5:], fill=(90, 100, 116), font=F_S)
dr.text((x0, y0 - 26), '每日合计', fill=(40, 50, 64), font=F_B)
dr.rectangle([x0 + 100, y0 - 30, x0 + 130, y0 - 14], fill=(58, 96, 168))
dr.text((x0 + 136, y0 - 32), '到件 inbound', fill=(70, 82, 100), font=F_S)
dr.rectangle([x0 + 270, y0 - 30, x0 + 300, y0 - 14], fill=(196, 132, 48))
dr.text((x0 + 306, y0 - 32), '取件 outbound', fill=(70, 82, 100), font=F_S)

# 下图：11-11 当日到件 vs 取件（10 分钟曲线）
x1, y1, w1, h1 = 90, 600, 1620, 380
day_sel = '2026-11-11'
sel = [r for r in rows if r['date'] == day_sel]
inb_s = [0] * 144
out_s = {s: [0] * 144 for s in set(r['site_id'] for r in sel)}
for r in sel:
    i = int(r['time'][:2]) * 6 + int(r['time'][3:]) // 10
    inb_s[i] += int(r['inbound'])
    out_s[r['site_id']][i] += int(r['outbound'])
out_tot = [sum(v[i] for v in out_s.values()) for i in range(144)]
mx = max(max(inb_s), max(out_tot))
dr.line([x1, y1 + h1, x1 + w1, y1 + h1], fill=(210, 216, 226), width=2)
for i in range(0, 144, 6):
    dr.text((x1 + i / 144 * w1 - 14, y1 + h1 + 8), '%02d:00' % (i // 6), fill=(120, 130, 146), font=F_S)
def curve(vals, color, width=3):
    pts = [(x1 + i / 143 * w1, y1 + h1 - v / mx * (h1 - 30)) for i, v in enumerate(vals)]
    dr.line(pts, fill=color, width=width, joint='curve')
curve(inb_s, (58, 96, 168))
curve(out_tot, (196, 132, 48))
dr.text((x1, y1 - 26), '11 月 11 日当天（10 分钟曲线）', fill=(40, 50, 64), font=F_B)
dr.text((x1 + 320, y1 - 30), '峰值到件 %d 件 / 10 分钟' % max(inb_s), fill=(70, 82, 100), font=F_S)

img.save(os.path.join(ROOT, 'docs', 'db', '11月流量-预览.png'))
print('saved preview')
