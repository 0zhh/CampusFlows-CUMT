# -*- coding: utf-8 -*-
"""把 ER 图渲染成 PNG（不是截图、不是 OCR，直接用 PIL 画）。"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = r'D:\java大作业'
OUT = os.path.join(ROOT, 'docs', 'db', 'ER-图.png')

W, H = 2400, 1560
BG = (250, 251, 253)
img = Image.new('RGB', (W, H), BG)
dr = ImageDraw.Draw(img)


def font(sz, bold=False):
    for p in (r'C:\Windows\Fonts\msyhbd.ttc' if bold else r'C:\Windows\Fonts\msyh.ttc',
              r'C:\Windows\Fonts\simhei.ttf'):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            continue
    return ImageFont.load_default()


F_TITLE = font(34, True)
F_SUB = font(17)
F_HEAD = font(17, True)
F_FIELD = font(14)
F_TAG = font(12, True)
F_LEG = font(15)

GROUPS = {
    'space':   dict(label='空间与设施', color=(61, 81, 112),  light=(232, 238, 247)),
    'entity':  dict(label='包裹与编码', color=(31, 122, 106), light=(228, 243, 240)),
    'time':    dict(label='场景与仿真', color=(176, 112, 32), light=(250, 240, 226)),
    'flow':    dict(label='流程与审计', color=(150, 62, 78),  light=(249, 233, 236)),
    'param':   dict(label='参数版本',   color=(102, 74, 148), light=(238, 233, 247)),
}

# name: (group, cn, fields[(tag, name, type)])
ENT = {
    'site': ('space', '站点', [
        ('PK', 'id', 'VARCHAR(32)'), ('', 'name', 'VARCHAR(64)'), ('', 'role', 'VARCHAR(16)'),
        ('', 'physical_slots', 'INT'), ('', 'kappa_i', 'INT'), ('', 'aisle_m', 'DECIMAL(3,2)'),
        ('', 'lat / lng', 'DECIMAL(9,6)')]),
    'rack_row': ('space', '货架排', [
        ('PK', 'id', 'VARCHAR(16)'), ('FK', 'site_id', 'VARCHAR(32)'), ('', 'zone_id', 'VARCHAR(8)'),
        ('', 'x_m / y_m', 'DECIMAL(6,2)'), ('', 'managed_by', 'VARCHAR(8)')]),
    'shelf': ('space', '货架', [
        ('PK', 'id', 'VARCHAR(24)'), ('FK', 'row_id', 'VARCHAR(16)'), ('UQ', 'bay_no', 'SMALLINT'),
        ('', 'tiers', 'TINYINT'), ('', 'slots_per_tier', 'SMALLINT')]),
    'slot': ('space', '储位', [
        ('PK', 'id', 'VARCHAR(32)'), ('FK', 'shelf_id', 'VARCHAR(24)'), ('', 'tier', 'TINYINT'),
        ('', 'cell_no', 'SMALLINT'), ('UQ', 'parcel_id', 'VARCHAR(32) NULL')]),

    'carrier': ('entity', '承运商', [
        ('PK', 'code', 'VARCHAR(8)'), ('UQ', 'name', 'VARCHAR(32)')]),
    'parcel': ('entity', '包裹', [
        ('PK', 'id', 'VARCHAR(32)'), ('FK', 'site_id', 'VARCHAR(32)'), ('FK', 'carrier_code', 'VARCHAR(8)'),
        ('', 'batch_id', 'VARCHAR(16)'), ('', 'status', 'VARCHAR(16)'), ('', 'shelved_at', 'DATETIME')]),
    'pickup_code': ('entity', '取件码', [
        ('PK', 'site_id', 'VARCHAR(32)'), ('PK', 'code', 'VARCHAR(16)'),
        ('FK', 'parcel_id', 'VARCHAR(32)'), ('', 'issued_at', 'DATETIME')]),

    'scenario': ('time', '场景', [
        ('PK', 'id', 'VARCHAR(16)'), ('', 'name', 'VARCHAR(64)'), ('', 'day_index', 'TINYINT')]),
    'scenario_site_param': ('time', '场景站点参数', [
        ('PK', 'scenario_id', 'VARCHAR(16)'), ('PK', 'site_id', 'VARCHAR(32)'),
        ('', 'capacity_per_bucket', 'INT'), ('', 'kappa_q / kappa_i', 'INT'), ('', 'i0', 'INT')]),
    'demand_bucket': ('time', '逐桶需求', [
        ('PK', 'scenario_id + site_id + bucket', ''),
        ('', 'arrivals', 'INT'), ('', 'capacity', 'INT'), ('', 'pickups', 'INT')]),
    'simulation_run': ('time', '仿真运行', [
        ('PK', 'id', 'BIGINT AI'), ('FK', 'scenario_id', 'VARCHAR(16)'), ('FK', 'param_version', 'VARCHAR(16)'),
        ('', 'seed', 'INT'), ('', 'peak_i / risk_buckets', 'INT')]),
    'sim_result': ('time', '逐桶结果', [
        ('PK', 'run_id + site_id + bucket', ''),
        ('', 'q / i / s / p / unmet', 'INT'), ('', 'risk_q / risk_i', 'BOOLEAN')]),

    'work_order': ('flow', '工单', [
        ('PK', 'id', 'VARCHAR(16)'), ('FK', 'site_id', 'VARCHAR(32)'), ('', 'kind / status', 'VARCHAR(16)'),
        ('', 'bucket', 'CHAR(5)'), ('', 'title / detail', 'TEXT')]),
    'workorder_event': ('flow', '工单事件', [
        ('PK', 'id', 'BIGINT AI'), ('FK', 'wo_id', 'VARCHAR(16)'),
        ('', 'from / to_status', 'VARCHAR(16)'), ('', 'actor', 'VARCHAR(32)'), ('', 'at_time', 'DATETIME(3)')]),

    'param_version': ('param', '参数版本', [
        ('PK', 'version', 'VARCHAR(16)'),
        ('', 'observed / public / assumed', 'SMALLINT'), ('', 'payload', 'JSON')]),
}

BOX_W = 392
TITLE_H = 40
ROW_H = 26
PAD = 10

POS = {
    'site': (60, 90), 'rack_row': (60, 380), 'shelf': (60, 620), 'slot': (60, 860),
    'carrier': (520, 90), 'parcel': (520, 300), 'pickup_code': (520, 640),
    'scenario': (1000, 90), 'scenario_site_param': (1000, 300), 'demand_bucket': (1000, 560),
    'simulation_run': (1000, 800), 'sim_result': (1000, 1060),
    'work_order': (1560, 90), 'workorder_event': (1560, 360), 'param_version': (1560, 620),
}


def box_h(name):
    return TITLE_H + ROW_H * len(ENT[name][2]) + PAD


def box_rect(name):
    x, y = POS[name]
    return (x, y, x + BOX_W, y + box_h(name))


# ---------- 标题 ----------
dr.text((60, 24), '驿链 CampusFlow · 数据库 ER 图', fill=(22, 28, 38), font=F_TITLE)
dr.text((640, 38), 'MySQL 8.4（Docker）· 15 张表 · v2.0  2026-11-04', fill=(110, 120, 136), font=F_SUB)

# ---------- 先画连线（在盒子下面） ----------
def side_pt(name, side):
    x0, y0, x1, y1 = box_rect(name)
    return {
        'l': (x0, (y0 + y1) // 2), 'r': (x1, (y0 + y1) // 2),
        't': ((x0 + x1) // 2, y0), 'b': ((x0 + x1) // 2, y1),
    }[side]


def link(a, sa, b, sb, label='1 : N', color=(140, 150, 168), dash=False):
    ax, ay = side_pt(a, sa)
    bx, by = side_pt(b, sb)
    pts = [(ax, ay)]
    if sa in 'lr' and sb in 'lr':
        if sa == sb:
            mx = (max(ax, bx) + 30) if sa == 'r' else (min(ax, bx) - 30)
        else:
            mx = (ax + bx) // 2
        pts += [(mx, ay), (mx, by)]
    elif sa in 'tb' and sb in 'tb':
        my = (ay + by) // 2
        pts += [(ax, my), (bx, my)]
    else:
        pts += [(ax, by)] if sa in 'lr' else [(bx, ay)]
    pts.append((bx, by))
    for i in range(len(pts) - 1):
        if dash:
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            seg = max(1, int(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 // 10))
            for k in range(0, seg, 2):
                t0, t1 = k / seg, min(1, (k + 1) / seg)
                dr.line([x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0,
                         x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1], fill=color, width=2)
        else:
            dr.line([pts[i], pts[i + 1]], fill=color, width=2)
    # 端点小圆
    for (px, py) in (pts[0], pts[-1]):
        dr.ellipse([px - 4, py - 4, px + 4, py + 4], fill=color)
    # 标签
    if label:
        mx, my = pts[len(pts) // 2]
        tw = dr.textlength(label, font=F_TAG)
        dr.rectangle([mx - tw / 2 - 5, my - 10, mx + tw / 2 + 5, my + 10], fill=BG)
        dr.text((mx - tw / 2, my - 8), label, fill=(120, 130, 146), font=F_TAG)


link('site', 'b', 'rack_row', 't')
link('rack_row', 'b', 'shelf', 't')
link('shelf', 'b', 'slot', 't')
link('carrier', 'b', 'parcel', 't', '1 : N')
link('parcel', 'r', 'pickup_code', 'r', '1 : 1')
link('site', 'r', 'parcel', 'l', '1 : N', (140, 150, 168), True)

link('scenario', 'b', 'scenario_site_param', 't')
link('scenario_site_param', 'b', 'demand_bucket', 't', '1 : N')
link('demand_bucket', 'b', 'simulation_run', 't', '1 : N')
link('simulation_run', 'b', 'sim_result', 't', '1 : N')

link('work_order', 'b', 'workorder_event', 't', '1 : N')
link('param_version', 'l', 'simulation_run', 'r', '1 : N', (140, 150, 168), True)

# ---------- 再画盒子 ----------
for name, (g, cn, fields) in ENT.items():
    x0, y0, x1, y1 = box_rect(name)
    pal = GROUPS[g]
    h = y1 - y0
    dr.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=(255, 255, 255), outline=pal['color'], width=2)
    dr.rounded_rectangle([x0, y0, x1, y0 + TITLE_H], radius=10, fill=pal['color'])
    dr.rectangle([x0, y0 + TITLE_H - 10, x1, y0 + TITLE_H], fill=pal['color'])
    dr.text((x0 + 12, y0 + 10), name, fill=(255, 255, 255), font=F_HEAD)
    tw = dr.textlength(name, font=F_HEAD)
    dr.text((x0 + 12 + tw + 10, y0 + 12), cn, fill=(255, 255, 255), font=F_SUB)

    yy = y0 + TITLE_H + 4
    for tag, fname, ftype in fields:
        if tag:
            tg = {'PK': (200, 70, 70), 'FK': (60, 110, 180), 'UQ': (140, 100, 40)}[tag]
            dr.rounded_rectangle([x0 + 10, yy + 3, x0 + 44, yy + 20], radius=4, fill=tg)
            dr.text((x0 + 16, yy + 5), tag, fill=(255, 255, 255), font=F_TAG)
            tx = x0 + 52
        else:
            tx = x0 + 52
        dr.text((tx, yy + 4), fname, fill=(30, 36, 46), font=F_FIELD)
        if ftype:
            tw2 = dr.textlength(ftype, font=F_FIELD)
            dr.text((x1 - 14 - tw2, yy + 4), ftype, fill=(130, 140, 156), font=F_FIELD)
        yy += ROW_H
    dr.rounded_rectangle([x0, y0, x1, y1], radius=10, outline=pal['color'], width=2)

# ---------- 图例 ----------
lx, ly = 1000, 1300
dr.rounded_rectangle([lx, ly, lx + 660, ly + 200], radius=10, fill=(255, 255, 255), outline=(210, 215, 224), width=2)
dr.text((lx + 16, ly + 12), '图例', fill=(30, 36, 46), font=F_HEAD)
rows = [
    ('PK', (200, 70, 70), '主键'),
    ('FK', (60, 110, 180), '外键'),
    ('UQ', (140, 100, 40), '唯一约束'),
]
for i, (tag, c, txt) in enumerate(rows):
    yy = ly + 46 + i * 30
    dr.rounded_rectangle([lx + 16, yy, lx + 50, yy + 18], radius=4, fill=c)
    dr.text((lx + 22, yy + 2), tag, fill=(255, 255, 255), font=F_TAG)
    dr.text((lx + 60, yy + 1), txt, fill=(60, 70, 84), font=F_LEG)

bx = lx + 200
for i, (key, pal) in enumerate(GROUPS.items()):
    yy = ly + 46 + i * 28
    dr.rounded_rectangle([bx, yy, bx + 18, yy + 18], radius=4, fill=pal['color'])
    dr.text((bx + 26, yy + 1), pal['label'], fill=(60, 70, 84), font=F_LEG)

dr.text((lx + 16, ly + 152), '实线＝强关联（外键 + 级联），虚线＝跨域引用', fill=(120, 130, 146), font=F_SUB)
dr.text((lx + 16, ly + 174), '三条不变式：储位唯一占用 / 取件码站内唯一 / 逐桶结果非负',
        fill=(120, 130, 146), font=F_SUB)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT)
print('saved', OUT, img.size)
