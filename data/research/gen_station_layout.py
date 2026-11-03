# -*- coding: utf-8 -*-
"""生成桃苑主站室内布局数据 + 预览图。

排布按照片里的真实形态：一条通道两侧各一排货架（双面货架），
每侧 5 个货架号，所以一排 = 10 个货架号、通道净宽 1.3 m。
220 个货架号 → 22 排，分两个区，中间留横向主通道。
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
BAYS_PER_ROW = BAYS_PER_SIDE * 2                  # 一排 10 个货架号
N_ROWS = math.ceil(BAYS / BAYS_PER_ROW)           # 22 排
BAY_LEN = 1.5                                     # 单开间长（12 件/层 × 约 12 cm）
RUN_LEN = BAYS_PER_SIDE * BAY_LEN                 # 7.5 m
ROW_PITCH = DEPTH * 2 + AISLE                     # 1.2 + 1.3 = 2.5 m
CROSS_AISLE = 2.4
MARGIN = 2.0
HEAD = 6.0                                        # 入口与服务台区

# 用户要求：三列等长，最右列不缩水。列数固定 3，排数向上取整后补齐
N_BLOCK = 3
BLOCK_ROWS = math.ceil(N_ROWS / N_BLOCK)
W = MARGIN * 2 + N_BLOCK * RUN_LEN + (N_BLOCK - 1) * CROSS_AISLE
JD_STRIP = 4.5                                     # 底部给京东服务区留一条
D = MARGIN * 2 + HEAD + BLOCK_ROWS * ROW_PITCH + JD_STRIP

rows = []
bay_no = 0
PADDED_NOTE = '末列与其余两列等长，多出的排位留空（现场就是齐的，不是缺口）'
for r in range(BLOCK_ROWS * N_BLOCK):
    block = r // BLOCK_ROWS
    row_in_block = r % BLOCK_ROWS
    x = MARGIN + block * (RUN_LEN + CROSS_AISLE)
    y = MARGIN + HEAD + row_in_block * ROW_PITCH
    left, right = [], []
    for _ in range(BAYS_PER_SIDE):
        bay_no += 1
        if bay_no <= BAYS:
            left.append(bay_no)
    for _ in range(BAYS_PER_SIDE):
        bay_no += 1
        if bay_no <= BAYS:
            right.append(bay_no)
    if not left and not right:
        continue
    rows.append({
        "row_id": "R%02d" % (r + 1),
        "block": block,
        "x_m": round(x, 2),
        "y_m": round(y, 2),
        "length_m": RUN_LEN,
        "depth_m": round(DEPTH * 2, 2),
        "left_bays": left,
        "right_bays": right,
        "managed_by": "JD" if (left and left[0] >= 191) else "SELF",
        "tiers": TIERS,
        "slots_per_tier": PER_TIER,
        "aisle_y_m": round(y + DEPTH, 2)
    })

# 顶部：出入口在左、扫码出库台在右（两者同一横带，门在出库台的左边）
# 底部：人工服务台（原来放京东的位置）
# 京东不单独占区域——第三列 191—240 号货架就是京东管理的货架，用颜色区分
ZONE_Y = 2.6
ZONE_H = 3.2
zones = [
    {"id": "Z-ENTRY", "kind": "entrance", "label": "出入口", "x_m": 0.2, "y_m": ZONE_Y,
     "w_m": 1.6, "h_m": ZONE_H},
    {"id": "Z-SCAN", "kind": "counter", "label": "扫码出库台",
     "x_m": 2.2, "y_m": ZONE_Y, "w_m": round(W - 4.2, 2), "h_m": ZONE_H},
    {"id": "Z-MANUAL", "kind": "brand", "label": "人工服务台",
     "x_m": round(MARGIN + 2 * (RUN_LEN + CROSS_AISLE), 2), "y_m": round(D - JD_STRIP + 0.7, 2),
     "w_m": round(RUN_LEN, 2), "h_m": 3.0},
]

layout = {
    "schema_version": "1.0",
    "generated_at": "2026-11-03",
    "note": "货架数/层数/每层位数/通道宽来自参数表（桃苑为照片+用户口述实测档）；"
            "行列排布按“三列等长、每排两侧各 5 个货架号、通道 0.8 m”生成，是设计示意，不是实测平面图。",
    "stations": [
        {
            "station_id": "NH-TAOYUAN",
            "name": "桃苑物流服务中心",
            "truth_level": "public_structure + observed_counts + designed_arrangement",
            "floor": {"width_m": round(W, 1), "depth_m": round(D, 1),
                      "area_m2": round(W * D), "area_note": "按阵列与通道推算，非实测面积"},
            "params": {"bays": BAYS, "tiers": TIERS, "slots_per_tier": PER_TIER,
                       "bay_length_m": BAY_LEN, "rack_depth_m": DEPTH, "aisle_m": AISLE,
                       "rows": N_ROWS, "bays_per_row": BAYS_PER_ROW,
                       "physical_slots": BAYS * TIERS * PER_TIER,
                       "code_format": "货架号-层号-序号"},
            "zones": zones,
            "rows": rows,
        },
        {
            "station_id": "NH-LANYUAN",
            "name": "兰苑无人菜鸟驿站",
            "status": "pending_photos",
            "note": "用户 2026-11-04 提供实景照片后生成；在此之前不画示意布局。"
        }
    ]
}

os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
json.dump(layout, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('json ->', OUT_JSON)
print('floor %.1f x %.1f m = %.0f m2 ; rows %d ; bays %d ; slots %d'
      % (W, D, W * D, N_ROWS, BAYS, BAYS * TIERS * PER_TIER))

# ---------------- 预览图 ----------------
SCALE = 22
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


F_T, F_L, F_S = font(26), font(15), font(11)
OX, OY = 40, 108
dr.text((OX, 22), '桃苑主站室内布局 v4 · %d 架 × %d 层 × %d 位 = %d 储位'
        % (BAYS, TIERS, PER_TIER, BAYS * TIERS * PER_TIER), fill=(18, 22, 30), font=F_T)
dr.text((OX, 56), '三列等长（1-80 / 81-160 / 161-240）· 通道 %.1f m · %d 排 · 占地约 %.0f m² · v4 2026-11-03'
        % (AISLE, N_ROWS, W * D), fill=(90, 100, 118), font=F_L)

dr.rectangle([OX, OY, OX + W * SCALE, OY + D * SCALE], fill=(240, 243, 248), outline=(160, 170, 186))

for z in zones:
    x0, y0 = OX + z['x_m'] * SCALE, OY + z['y_m'] * SCALE
    x1, y1 = x0 + z['w_m'] * SCALE, y0 + z['h_m'] * SCALE
    c = {"entrance": (63, 169, 124), "counter": (232, 163, 61), "brand": (91, 155, 213)}[z['kind']]
    dr.rectangle([x0, y0, x1, y1], fill=c, outline=(55, 65, 80))
    dr.text((x0 + 5, y0 + 4), z['label'], fill=(255, 255, 255), font=F_S)

for row in rows:
    x0 = OX + row['x_m'] * SCALE
    y0 = OY + row['y_m'] * SCALE
    # 通道
    dr.rectangle([x0, y0 + DEPTH * SCALE, x0 + row['length_m'] * SCALE, y0 + (DEPTH + AISLE) * SCALE],
                 fill=(255, 255, 255))
    jd = row.get('managed_by') == 'JD'
    up = (120, 78, 160) if jd else (60, 80, 112)
    dn = (142, 96, 182) if jd else (74, 96, 130)
    # 上侧货架
    dr.rectangle([x0, y0, x0 + row['length_m'] * SCALE, y0 + DEPTH * SCALE], fill=up, outline=(28, 38, 52))
    # 下侧货架
    dr.rectangle([x0, y0 + (DEPTH + AISLE) * SCALE, x0 + row['length_m'] * SCALE,
                  y0 + (DEPTH * 2 + AISLE) * SCALE], fill=dn, outline=(28, 38, 52))
    for side_x in (x0, x0 + row['length_m'] * SCALE):
        pass
    lab = '%d-%d / %d-%d' % (row['left_bays'][0], row['left_bays'][-1],
                             row['right_bays'][0], row['right_bays'][-1]) if row['left_bays'] and row['right_bays'] else ''
    dr.text((x0 + 4, y0 + DEPTH * SCALE + 1), lab, fill=(120, 132, 150), font=F_S)

# 京东管理区标注：放在该列第一排京东货架的上方
jd_rows = [r for r in rows if r.get('managed_by') == 'JD']
if jd_rows:
    x_jd = OX + jd_rows[0]['x_m'] * SCALE
    y_jd = OY + (jd_rows[0]['y_m'] - 1.1) * SCALE
    dr.text((x_jd, y_jd), '京东管理区 191—240（紫色货架）', fill=(120, 78, 160), font=F_L)
dr.text((OX, OY + D * SCALE + 12),
        '深蓝＝自营货架，紫色＝京东管理货架；白色为 0.8 m 通道；左上角为出入口，门在扫码出库台左侧',
        fill=(95, 105, 122), font=F_L)
os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
img.save(OUT_PNG)
print('preview ->', OUT_PNG, img.size)
