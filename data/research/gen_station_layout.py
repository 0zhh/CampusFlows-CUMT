# -*- coding: utf-8 -*-
"""桃苑主站室内布局生成器 v6

六列从左到右均等排布（用户 2026-11-03 最终口径）：
  · 6 列，每列 8 排，每排 5 个货架号（一侧 2 个、一侧 3 个，取较长侧算列宽）
  · 列宽 4.5 m（3 开间 × 1.5 m），列间 1.2 m 横向通道；排间距 2.0 m（双面货架 1.2 + 通道 0.8）
  · 240 个货架号：每列 40 个（1-40、41-80 … 201-240）
  · 191-240 恰好在排边界上（191 = 5×38+1），所以京东管理区正好 10 排 50 个货架号，不跨半排
"""
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = r'D:\java大作业'
PARAMS = os.path.join(ROOT, 'data', 'params', 'param_registry.json')
OUT_JSON = os.path.join(ROOT, 'data', 'geo', 'station_layouts.json')
OUT_PNG = os.path.join(ROOT, 'docs', 'screenshots', '桃苑室内布局-v8-五层.png')

reg = json.load(open(PARAMS, encoding='utf-8'))
P = {p['id']: p for p in reg['params']}

BAYS = P['P-RACK-COUNT']['value']          # 240
TIERS = P['P-TIERS']['value']              # 4
PER_TIER = P['P-SLOTS-PER-TIER']['value']  # 20
AISLE = P['P-AISLE-WIDTH']['value']        # 0.8
DEPTH = P['P-SHELF-OBSERVED']['value']['depth_mm'] / 1000.0  # 0.6

BAY_LEN = 1.0                              # 3 开间 = 3.0 m 一排；收窄是为了整体宽度压缩 1/4
LEFT_BAYS = 2
RIGHT_BAYS = 3
BAYS_PER_ROW = LEFT_BAYS + RIGHT_BAYS      # 5
COLS = 6
N_ROWS = BAYS // BAYS_PER_ROW              # 48
ROWS_PER_COL = N_ROWS // COLS              # 8
assert ROWS_PER_COL * COLS * BAYS_PER_ROW == BAYS

RUN_LEN = RIGHT_BAYS * BAY_LEN             # 4.5
ROW_PITCH = DEPTH * 2 + AISLE              # 2.0
COL_GAP = 1.2

MARGIN = 2.0
SF_H = 2.4
SCAN_H = 3.0
BOTTOM = 4.6

SF_Y = MARGIN + 0.4
SCAN_Y = SF_Y + SF_H + 0.5
GRID_Y = SCAN_Y + SCAN_H + 0.9
W = MARGIN * 2 + COLS * RUN_LEN + (COLS - 1) * COL_GAP
D = GRID_Y + ROWS_PER_COL * ROW_PITCH + BOTTOM + MARGIN

rows = []
for c in range(COLS):
    for i in range(ROWS_PER_COL):
        n = c * ROWS_PER_COL * BAYS_PER_ROW + i * BAYS_PER_ROW + 1
        left = list(range(n, n + LEFT_BAYS))
        right = list(range(n + LEFT_BAYS, n + BAYS_PER_ROW))
        rows.append({
            "row_id": "R%02d" % (len(rows) + 1),
            "zone_id": "Z-C%d" % (c + 1),
            "col": c,
            "row_in_col": i,
            "x_m": round(MARGIN + c * (RUN_LEN + COL_GAP), 2),
            "y_m": round(GRID_Y + i * ROW_PITCH, 2),
            "length_m": RUN_LEN,
            "depth_m": round(DEPTH * 2, 2),
            "left_bays": left,
            "right_bays": right,
            "managed_by": "JD" if left[0] >= 191 else "SELF",
            "tiers": TIERS,
            "slots_per_tier": PER_TIER,
        })

zones = [
    {"id": "Z-SF", "kind": "brand_sf", "label": "顺丰独立收发区",
     "x_m": round(MARGIN, 2), "y_m": round(SF_Y, 2), "w_m": round(W - MARGIN * 2, 2), "h_m": SF_H},
    {"id": "Z-ENTRY", "kind": "entrance", "label": "出入口",
     "x_m": 0.2, "y_m": round(SCAN_Y, 2), "w_m": 1.6, "h_m": SCAN_H},
    {"id": "Z-SCAN", "kind": "counter", "label": "扫码出库台",
     "x_m": 2.2, "y_m": round(SCAN_Y, 2), "w_m": round(W - 4.2, 2), "h_m": SCAN_H},
    {"id": "Z-MANUAL", "kind": "manual", "label": "人工服务台",
     "x_m": round(MARGIN + 3 * (RUN_LEN + COL_GAP) + 0.6, 2), "y_m": round(D - BOTTOM + 0.8, 2),
     "w_m": 5.0, "h_m": 3.0},
]

layout = {
    "schema_version": "1.1",
    "generated_at": "2026-11-03",
    "layout_version": "v6",
    "note": "货架数/层数/每层位数/通道宽来自参数表（实测档）；"
            "六个货架区从左到右均等排布，每区 8 排、每排 5 个货架号，属设计示意，非实测平面图。",
    "stations": [
        {
            "station_id": "NH-TAOYUAN",
            "name": "桃苑物流服务中心",
            "truth_level": "public_structure + observed_counts + designed_arrangement",
            "floor": {"width_m": round(W, 1), "depth_m": round(D, 1),
                      "area_m2": round(W * D), "area_note": "按阵列与通道推算，非实测面积"},
            "params": {"bays": BAYS, "tiers": TIERS, "slots_per_tier": PER_TIER,
                       "bay_length_m": BAY_LEN, "rack_depth_m": DEPTH, "aisle_m": AISLE,
                       "cols": COLS, "rows_per_col": ROWS_PER_COL, "rows": N_ROWS,
                       "bays_per_row": BAYS_PER_ROW, "left_bays": LEFT_BAYS, "right_bays": RIGHT_BAYS,
                       "physical_slots": BAYS * TIERS * PER_TIER,
                       "code_format": "货架号-层号-序号"},
            "zones": zones,
            "rows": rows,
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
print('floor %.1f x %.1f = %.0f m2 ; cols %d ; rows %d ; bays %d ; slots %d'
      % (W, D, W * D, COLS, N_ROWS, BAYS, BAYS * TIERS * PER_TIER))

# ---------------- 预览图 ----------------
SCALE = 21
IMG_W, IMG_H = int(W * SCALE) + 80, int(D * SCALE) + 150
img = Image.new('RGB', (IMG_W, IMG_H), (250, 250, 252))
dr = ImageDraw.Draw(img)


def font(sz):
    for path in (r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf'):
        try:
            return ImageFont.truetype(path, sz)
        except Exception:
            continue
    return ImageFont.load_default()


F_T, F_L, F_S = font(25), font(14), font(10)
OX, OY = 40, 104
dr.text((OX, 20), '桃苑主站室内布局 v7 · %d 架 × %d 层 × %d 位 = %d 储位'
        % (BAYS, TIERS, PER_TIER, BAYS * TIERS * PER_TIER), fill=(18, 22, 30), font=F_T)
dr.text((OX, 54), '六个货架区自左向右均等排布（每区 %d 排 × 每排 %d 号）· 通道 %.1f m · 占地约 %.0f m² · v6'
        % (ROWS_PER_COL, BAYS_PER_ROW, AISLE, W * D), fill=(90, 100, 118), font=F_L)
dr.text((OX, 74), '顶部：顺丰独立收发区 → 扫码出库台（出入口在出库台左侧）· 底部：人工服务台（已左移加宽）· v7',
        fill=(90, 100, 118), font=F_S)

dr.rectangle([OX, OY, OX + W * SCALE, OY + D * SCALE], fill=(240, 243, 248), outline=(160, 170, 186))

ZC = {"brand_sf": (150, 92, 128), "entrance": (63, 169, 124),
      "counter": (232, 163, 61), "manual": (91, 155, 213)}
for z in zones:
    x0, y0 = OX + z['x_m'] * SCALE, OY + z['y_m'] * SCALE
    x1, y1 = x0 + z['w_m'] * SCALE, y0 + z['h_m'] * SCALE
    dr.rectangle([x0, y0, x1, y1], fill=ZC[z['kind']], outline=(55, 65, 80))
    dr.text((x0 + 5, y0 + 5), z['label'], fill=(255, 255, 255), font=F_L)

# 六个列区外框
for c in range(COLS):
    x0 = OX + (MARGIN + c * (RUN_LEN + COL_GAP) - 0.25) * SCALE
    y0 = OY + (GRID_Y - 0.35) * SCALE
    x1 = x0 + (RUN_LEN + 0.5) * SCALE
    y1 = y0 + (ROWS_PER_COL * ROW_PITCH - AISLE + 0.7) * SCALE
    dr.rectangle([x0, y0, x1, y1], outline=(120, 132, 150), width=2)
    dr.text((x0 + 3, y0 + 2), "Z-C%d" % (c + 1), fill=(120, 132, 150), font=F_S)

for row in rows:
    x0 = OX + row['x_m'] * SCALE
    y0 = OY + row['y_m'] * SCALE
    jd = row.get('managed_by') == 'JD'
    up = (120, 78, 160) if jd else (60, 80, 112)
    dn = (142, 96, 182) if jd else (74, 96, 130)
    dr.rectangle([x0, y0, x0 + row['length_m'] * SCALE, y0 + DEPTH * SCALE], fill=up, outline=(28, 38, 52))
    dr.rectangle([x0, y0 + (DEPTH + AISLE) * SCALE, x0 + row['length_m'] * SCALE,
                  y0 + (DEPTH * 2 + AISLE) * SCALE], fill=dn, outline=(28, 38, 52))
    if row['row_in_col'] % 2 == 0:
        dr.text((x0, y0 - 11), '%d-%d' % (row['left_bays'][0], row['right_bays'][-1]),
                fill=(120, 132, 150), font=F_S)

jd_rows = [r for r in rows if r.get('managed_by') == 'JD']
if jd_rows:
    dr.text((OX + jd_rows[0]['x_m'] * SCALE - 40, OY + (jd_rows[0]['y_m'] - 1.4) * SCALE),
            '京东管理区 191—240', fill=(120, 78, 160), font=F_L)

dr.text((OX, OY + D * SCALE + 10),
        '深蓝＝自营货架，紫色＝京东管理 191—240；白色为 0.8 m 通道；六个灰框是六个货架区',
        fill=(95, 105, 122), font=F_L)
os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
img.save(OUT_PNG)
print('preview ->', OUT_PNG, img.size)
