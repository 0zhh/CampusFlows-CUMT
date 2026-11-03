# -*- coding: utf-8 -*-
"""桃苑主站室内布局生成器 v6 —— 六个竖着的货架长条

几何口径（用户 2026-11-03 连续三轮更正后的最终理解）：
  · 六个货架区是**六个竖着的长条**，并排布置，不是横着切
  · 每个长条 = 一条通道 + 两侧各 20 个货架号（40 号/条），6 条 × 40 = 240 号
  · 通道 0.8 m、货架深 0.6 m（双面 1.2 m）、单号 1.2 m
  · 顶部自外向内：顺丰独立收发区 → 扫码出库台；出入口在出库台左侧
  · 底部：人工服务台；191—240 号为京东管理（逐号染色）
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = r'D:\java大作业'
PARAMS = os.path.join(ROOT, 'data', 'params', 'param_registry.json')
OUT_JSON = os.path.join(ROOT, 'data', 'geo', 'station_layouts.json')
OUT_PNG = os.path.join(ROOT, '.probe', 'layout_taoyuan.png')

reg = json.load(open(PARAMS, encoding='utf-8'))
P = {p['id']: p for p in reg['params']}

BAYS = P['P-RACK-COUNT']['value']          # 240
TIERS = P['P-TIERS']['value']              # 4
PER_TIER = P['P-SLOTS-PER-TIER']['value']  # 20
AISLE = P['P-AISLE-WIDTH']['value']        # 0.8
DEPTH = P['P-SHELF-OBSERVED']['value']['depth_mm'] / 1000.0  # 0.6

RUNS = 6
BAYS_PER_SIDE = BAYS // (RUNS * 2)          # 20
BAY_LEN = 1.2
RUN_LEN = BAYS_PER_SIDE * BAY_LEN           # 24.0
RUN_W = DEPTH * 2                           # 1.2 双面
assert BAYS_PER_SIDE * RUNS * 2 == BAYS, (BAYS_PER_SIDE, RUNS, BAYS)

MARGIN = 2.0
SF_H = 2.4
SCAN_H = 3.2
BOTTOM = 4.6
SF_Y = MARGIN + 0.5
SCAN_Y = SF_Y + SF_H + 0.4
GRID_Y = SCAN_Y + SCAN_H + 0.8
W = MARGIN * 2 + RUNS * RUN_W + (RUNS - 1) * AISLE
D = GRID_Y + RUN_LEN + 1.0 + BOTTOM + MARGIN

runs = []
for r in range(RUNS):
    base = r * BAYS_PER_SIDE * 2
    left = []
    for i in range(BAYS_PER_SIDE):
        no = base + i + 1
        left.append({"no": no, "managed_by": "JD" if no >= 191 else "SELF"})
    right = []
    for i in range(BAYS_PER_SIDE):
        no = base + BAYS_PER_SIDE + i + 1
        right.append({"no": no, "managed_by": "JD" if no >= 191 else "SELF"})
    runs.append({
        "run_id": "RUN-%d" % (r + 1),
        "x_m": round(MARGIN + r * (RUN_W + AISLE), 2),
        "y_m": round(GRID_Y, 2),
        "length_m": RUN_LEN,
        "width_m": RUN_W,
        "aisle_m": AISLE,
        "bay_length_m": BAY_LEN,
        "left_bays": left,
        "right_bays": right,
        "tiers": TIERS,
        "slots_per_tier": PER_TIER,
    })

zones = [
    {"id": "Z-SF", "kind": "brand_sf", "label": "顺丰独立收发区",
     "x_m": MARGIN, "y_m": round(SF_Y, 2), "w_m": round(W - MARGIN * 2, 2), "h_m": SF_H},
    {"id": "Z-ENTRY", "kind": "entrance", "label": "出入口",
     "x_m": 0.2, "y_m": round(SCAN_Y, 2), "w_m": 1.6, "h_m": SCAN_H},
    {"id": "Z-SCAN", "kind": "counter", "label": "扫码出库台",
     "x_m": 2.2, "y_m": round(SCAN_Y, 2), "w_m": round(W - 4.2, 2), "h_m": SCAN_H},
    {"id": "Z-MANUAL", "kind": "manual", "label": "人工服务台",
     "x_m": round(W - MARGIN - 4.6, 2), "y_m": round(D - BOTTOM + 0.8, 2), "w_m": 4.6, "h_m": 3.0},
]

layout = {
    "schema_version": "1.2",
    "generated_at": "2026-11-03",
    "layout_version": "v6",
    "note": "六个竖着的货架长条并排；每条 20 号/侧 × 2 侧 = 40 号，6 条 = 240 号。"
            "货架数/层数/每层位数/通道宽来自参数表（实测档），排布为设计示意。",
    "stations": [
        {
            "station_id": "NH-TAOYUAN",
            "name": "桃苑物流服务中心",
            "truth_level": "public_structure + observed_counts + designed_arrangement",
            "floor": {"width_m": round(W, 1), "depth_m": round(D, 1),
                      "area_m2": round(W * D), "area_note": "按阵列与通道推算，非实测面积"},
            "params": {"bays": BAYS, "tiers": TIERS, "slots_per_tier": PER_TIER,
                       "runs": RUNS, "bays_per_side": BAYS_PER_SIDE, "bay_length_m": BAY_LEN,
                       "rack_depth_m": DEPTH, "aisle_m": AISLE,
                       "physical_slots": BAYS * TIERS * PER_TIER,
                       "code_format": "货架号-层号-序号"},
            "zones": zones,
            "runs": runs,
        },
        {
            "station_id": "NH-LANYUAN",
            "name": "兰苑无人菜鸟驿站",
            "status": "pending_photos",
            "note": "等用户提供实景照片后生成。"
        }
    ]
}
os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
json.dump(layout, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('floor %.1f x %.1f = %.0f m2 ; runs %d ; bays %d ; slots %d'
      % (W, D, W * D, RUNS, BAYS, BAYS * TIERS * PER_TIER))

# ---------------- 预览 ----------------
SCALE = 26
IMG_W, IMG_H = int(W * SCALE) + 90, int(D * SCALE) + 150
img = Image.new('RGB', (IMG_W, IMG_H), (250, 250, 252))
dr = ImageDraw.Draw(img)


def font(sz):
    for path in (r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf'):
        try:
            return ImageFont.truetype(path, sz)
        except Exception:
            continue
    return ImageFont.load_default()


F_T, F_L, F_S = font(24), font(14), font(10)
OX, OY = 45, 108
dr.text((OX, 18), '桃苑主站室内布局 v6 · 六个竖向货架长条 · %d 架 × %d 层 × %d 位 = %d 储位'
        % (BAYS, TIERS, PER_TIER, BAYS * TIERS * PER_TIER), fill=(18, 22, 30), font=F_T)
dr.text((OX, 50), '每条 20 号/侧 × 2 侧 = 40 号，6 条 = 240 号 · 通道 %.1f m · 单号 %.1f m · 占地约 %.0f m²'
        % (AISLE, BAY_LEN, W * D), fill=(90, 100, 118), font=F_L)
dr.text((OX, 70), '顶部：顺丰独立收发区 → 扫码出库台（出入口在其左侧）· 底部：人工服务台 · 紫色为京东管理 191—240',
        fill=(90, 100, 118), font=F_S)

dr.rectangle([OX, OY, OX + W * SCALE, OY + D * SCALE], fill=(240, 243, 248), outline=(160, 170, 186))

ZC = {"brand_sf": (150, 92, 128), "entrance": (63, 169, 124),
      "counter": (232, 163, 61), "manual": (91, 155, 213)}
for z in zones:
    x0, y0 = OX + z['x_m'] * SCALE, OY + z['y_m'] * SCALE
    x1, y1 = x0 + z['w_m'] * SCALE, y0 + z['h_m'] * SCALE
    dr.rectangle([x0, y0, x1, y1], fill=ZC[z['kind']], outline=(55, 65, 80))
    dr.text((x0 + 5, y0 + 5), z['label'], fill=(255, 255, 255), font=F_L)

for run in runs:
    x0 = OX + run['x_m'] * SCALE
    y0 = OY + run['y_m'] * SCALE
    hl = run['length_m'] * SCALE
    wl = run['width_m'] * SCALE
    # 左、右两侧货架，逐号染色
    for side, off in (("left", 0.0), ("right", (DEPTH + AISLE) * SCALE)):
        for i, bay in enumerate(run[side + '_bays']):
            bx = x0
            by = y0 + off + i * BAY_LEN * SCALE
            colour = (120, 78, 160) if bay['managed_by'] == 'JD' else (60, 80, 112)
            dr.rectangle([bx, by, bx + hl, by + DEPTH * SCALE], fill=colour, outline=(30, 40, 55))
    # 中间通道
    dr.rectangle([x0, y0 + DEPTH * SCALE, x0 + hl, y0 + (DEPTH + AISLE) * SCALE],
                 fill=(255, 255, 255), outline=(210, 216, 224))
    first = run['left_bays'][0]['no']
    last = run['right_bays'][-1]['no']
    dr.text((x0 + 3, y0 - 14), '%d–%d' % (first, last), fill=(70, 80, 96), font=F_S)

dr.text((OX, OY + D * SCALE + 10),
        '每个长条：左 20 号 + 右 20 号，中间 0.8 m 通道；紫色号段（191—240）由京东管理',
        fill=(95, 105, 122), font=F_L)
os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
img.save(OUT_PNG)
print('preview ->', OUT_PNG, img.size)
