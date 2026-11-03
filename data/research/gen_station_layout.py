# -*- coding: utf-8 -*-
"""桃苑主站室内布局生成器 v5

几何口径（用户 2026-11-03 明确）：
  · 六个长方形货架区：3 列 × 2 带，每区 4 排，每排两侧各 5 个货架号
  · 通道 0.8 m，货架深 0.6 m（双面 = 1.2 m），单开间 1.5 m
  · 顶部自外向内：顺丰独立收发区 → 扫码出库台；出入口在出库台左侧
  · 底部：人工服务台（原京东柜台位置）；191—240 号货架为京东管理区（紫色）
"""
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = r'D:\java大作业'
PARAMS = os.path.join(ROOT, 'data', 'params', 'param_registry.json')
OUT_JSON = os.path.join(ROOT, 'data', 'geo', 'station_layouts.json')
OUT_PNG = os.path.join(ROOT, '.probe', 'layout_taoyuan.png')

reg = json.load(open(PARAMS, encoding='utf-8'))
P = {p['id']: p for p in reg['params']}

BAYS = P['P-RACK-COUNT']['value']
TIERS = P['P-TIERS']['value']
PER_TIER = P['P-SLOTS-PER-TIER']['value']
AISLE = P['P-AISLE-WIDTH']['value']
DEPTH = P['P-SHELF-OBSERVED']['value']['depth_mm'] / 1000.0

BAYS_PER_SIDE = 5
BAYS_PER_ROW = BAYS_PER_SIDE * 2      # 10
BAY_LEN = 1.5
RUN_LEN = BAYS_PER_SIDE * BAY_LEN     # 7.5
ROW_PITCH = DEPTH * 2 + AISLE         # 2.0

COLS = 3
BANDS = 2
ROWS_PER_BAND = 4
ROWS_PER_COL = BANDS * ROWS_PER_BAND  # 8
N_ROWS = COLS * ROWS_PER_COL          # 24
assert N_ROWS * BAYS_PER_ROW == BAYS, (N_ROWS, BAYS)

MARGIN = 2.0
SF_H = 2.4
SF_GAP = 0.4
SCAN_H = 3.2
TOP_GAP = 0.8
BAND_AISLE = 2.4
BOTTOM = 4.6

SF_Y = MARGIN + 0.4
SCAN_Y = SF_Y + SF_H + SF_GAP
GRID_Y = SCAN_Y + SCAN_H + TOP_GAP
D = GRID_Y + BANDS * ROWS_PER_BAND * ROW_PITCH + BAND_AISLE + BOTTOM + MARGIN
W = MARGIN * 2 + COLS * RUN_LEN + (COLS - 1) * 2.2

rows = []
for c in range(COLS):
    col_base = c * ROWS_PER_COL * BAYS_PER_ROW
    for b in range(BANDS):
        for i in range(ROWS_PER_BAND):
            n = col_base + (b * ROWS_PER_BAND + i) * BAYS_PER_ROW + 1
            left = list(range(n, n + BAYS_PER_SIDE))
            right = list(range(n + BAYS_PER_SIDE, n + BAYS_PER_ROW))
            rows.append({
                "row_id": "R%02d" % (len(rows) + 1),
                "zone_id": "Z-%s%d" % ("AB"[b], c + 1),
                "col": c, "band": b, "row_in_band": i,
                "x_m": round(MARGIN + c * (RUN_LEN + 2.2), 2),
                "y_m": round(GRID_Y + b * (ROWS_PER_BAND * ROW_PITCH + BAND_AISLE) + i * ROW_PITCH, 2),
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
     "x_m": round(MARGIN + 2 * (RUN_LEN + 2.2), 2), "y_m": round(D - BOTTOM + 0.7, 2),
     "w_m": RUN_LEN, "h_m": 3.0},
]

layout = {
    "schema_version": "1.1",
    "generated_at": "2026-11-03",
    "layout_version": "v5",
    "note": "货架数/层数/每层位数/通道宽来自参数表（实测档）；"
            "六个货架区的排布按“3 列 × 2 带、每区 4 排、每排两侧各 5 号”生成，是设计示意，非实测平面图。",
    "stations": [
        {
            "station_id": "NH-TAOYUAN",
            "name": "桃苑物流服务中心",
            "truth_level": "public_structure + observed_counts + designed_arrangement",
            "floor": {"width_m": round(W, 1), "depth_m": round(D, 1),
                      "area_m2": round(W * D), "area_note": "按阵列与通道推算，非实测面积"},
            "params": {"bays": BAYS, "tiers": TIERS, "slots_per_tier": PER_TIER,
                       "bay_length_m": BAY_LEN, "rack_depth_m": DEPTH, "aisle_m": AISLE,
                       "rows": N_ROWS, "rows_per_band": ROWS_PER_BAND, "cols": COLS, "bands": BANDS,
                       "bays_per_row": BAYS_PER_ROW,
                       "physical_slots": BAYS * TIERS * PER_TIER,
                       "code_format": "货架号-层号-序号"},
            "zones": zones,
            "rows": rows,
        },
        {
            "station_id": "NH-LANYUAN",
            "name": "兰苑无人菜鸟驿站",
            "status": "pending_photos",
            "note": "等用户提供实景照片后生成；在此之前不画示意布局。"
        }
    ]
}
os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
json.dump(layout, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('floor %.1f x %.1f = %.0f m2 ; rows %d ; bays %d ; slots %d'
      % (W, D, W * D, N_ROWS, BAYS, BAYS * TIERS * PER_TIER))

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


F_T, F_L, F_S = font(25), font(14), font(11)
OX, OY = 40, 104
dr.text((OX, 20), '桃苑主站室内布局 v5 · %d 架 × %d 层 × %d 位 = %d 储位'
        % (BAYS, TIERS, PER_TIER, BAYS * TIERS * PER_TIER), fill=(18, 22, 30), font=F_T)
dr.text((OX, 54), '六个货架区（3 列 × 2 带，每区 4 排）· 通道 %.1f m · 占地约 %.0f m² · v5 2026-11-03'
        % (AISLE, W * D), fill=(90, 100, 118), font=F_L)
dr.text((OX, 74), '顶部：顺丰独立收发区 → 扫码出库台（出入口在出库台左侧）· 底部：人工服务台',
        fill=(90, 100, 118), font=F_S)

dr.rectangle([OX, OY, OX + W * SCALE, OY + D * SCALE], fill=(240, 243, 248), outline=(160, 170, 186))

ZC = {"brand_sf": (150, 92, 128), "entrance": (63, 169, 124),
      "counter": (232, 163, 61), "manual": (91, 155, 213)}
for z in zones:
    x0, y0 = OX + z['x_m'] * SCALE, OY + z['y_m'] * SCALE
    x1, y1 = x0 + z['w_m'] * SCALE, y0 + z['h_m'] * SCALE
    dr.rectangle([x0, y0, x1, y1], fill=ZC[z['kind']], outline=(55, 65, 80))
    dr.text((x0 + 5, y0 + 5), z['label'], fill=(255, 255, 255), font=F_L)

# 每个货架区画一个外框（让"六个长方形"看得清）
for c in range(COLS):
    for b in range(BANDS):
        x0 = OX + (MARGIN + c * (RUN_LEN + 2.2) - 0.35) * SCALE
        y0 = OY + (GRID_Y + b * (ROWS_PER_BAND * ROW_PITCH + BAND_AISLE) - 0.35) * SCALE
        x1 = x0 + (RUN_LEN + 0.7) * SCALE
        y1 = y0 + (ROWS_PER_BAND * ROW_PITCH - AISLE + 0.7) * SCALE
        dr.rectangle([x0, y0, x1, y1], outline=(120, 132, 150), width=2)
        dr.text((x0 + 4, y0 + 2), "Z-%s%d" % ("AB"[b], c + 1), fill=(120, 132, 150), font=F_S)

for row in rows:
    x0 = OX + row['x_m'] * SCALE
    y0 = OY + row['y_m'] * SCALE
    jd = row.get('managed_by') == 'JD'
    up = (120, 78, 160) if jd else (60, 80, 112)
    dn = (142, 96, 182) if jd else (74, 96, 130)
    dr.rectangle([x0, y0, x0 + row['length_m'] * SCALE, y0 + DEPTH * SCALE], fill=up, outline=(28, 38, 52))
    dr.rectangle([x0, y0 + (DEPTH + AISLE) * SCALE, x0 + row['length_m'] * SCALE,
                  y0 + (DEPTH * 2 + AISLE) * SCALE], fill=dn, outline=(28, 38, 52))
    lab = '%d-%d' % (row['left_bays'][0], row['right_bays'][-1])
    dr.text((x0 + 3, y0 + DEPTH * SCALE + 1), lab, fill=(120, 132, 150), font=F_S)

jd_rows = [r for r in rows if r.get('managed_by') == 'JD']
if jd_rows:
    dr.text((OX + jd_rows[0]['x_m'] * SCALE, OY + (jd_rows[0]['y_m'] - 1.0) * SCALE),
            '京东管理区 191—240', fill=(120, 78, 160), font=F_L)

dr.text((OX, OY + D * SCALE + 10),
        '深蓝＝自营货架，紫色＝京东管理 191—240；白色为 0.8 m 通道；六个灰框是六个货架区',
        fill=(95, 105, 122), font=F_L)
os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
img.save(OUT_PNG)
print('preview ->', OUT_PNG, img.size)
