# -*- coding: utf-8 -*-
"""兰苑无人菜鸟驿站 · 室内布局 v2（纵向列）

用户 2026-11-04 更正：
  · 真实货架是"一列一列竖着"排的（列沿进深方向，通道左右分隔），不是横排
  · 每个货架只有一个号，不能重复

依据实景照片：货架号 505—559 共 55 个，每架 5 层，取件码 = 货架号-层号-序号。
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = r'D:\java大作业'
OUT_JSON = os.path.join(ROOT, 'data', 'geo', 'station_layouts.json')
OUT_PNG = os.path.join(ROOT, 'docs', 'screenshots', '兰苑室内布局-v2-纵列.png')

BAY_FIRST, BAY_LAST = 505, 559
BAYS = BAY_LAST - BAY_FIRST + 1          # 55
TIERS = 5
PER_TIER = 20
AISLE = 0.8
DEPTH = 0.6                              # 单面进深；一列＝双面 1.2 m
RUN_W = DEPTH * 2                        # 列的宽度（横向）
COL_GAP = AISLE                          # 列间通道
BAY_LEN = 1.0                            # 每个货架沿进深方向占 1.0 m
COLS = 5
PER_COL = BAYS // COLS                   # 11
assert PER_COL * COLS == BAYS

# 编号：从门口第一列开始，自上而下递增；559 之后回到 505 继续
order = list(range(545, 560)) + list(range(505, 545))

W, D = 11.6, 17.0
LEFT = 1.5
TOP = 5.0
COL_PITCH = RUN_W + COL_GAP

cols = []
for c in range(COLS):
    seq = order[c * PER_COL:(c + 1) * PER_COL]
    cols.append({
        "row_id": "C%02d" % (c + 1),
        "zone_id": "Z-RACK",
        "orientation": "vertical",
        "col": c,
        "row_in_col": c,
        "x_m": round(LEFT + c * COL_PITCH, 2),
        "y_m": round(TOP, 2),
        "w_m": round(RUN_W, 2),
        "length_m": round(PER_COL * BAY_LEN, 2),
        "depth_m": round(RUN_W, 2),
        "bay_len_m": BAY_LEN,
        "bays": seq,
        "managed_by": "SELF",
        "tiers": TIERS,
        "slots_per_tier": PER_TIER,
    })

ENTRY = {"id": "Z-ENTRY", "kind": "entrance", "label": "出入口",
         "x_m": 0.2, "y_m": 1.0, "w_m": 1.5, "h_m": 2.6}
COUNTER = {"id": "Z-COUNTER", "kind": "counter", "label": "出库台",
           "x_m": 2.2, "y_m": 1.0, "w_m": 3.4, "h_m": 2.6}
RESERVED = {"id": "Z-RESERVED", "kind": "reserved", "label": "",
            "x_m": 7.4, "y_m": 0.6, "w_m": 3.8, "h_m": 3.6}

PHYS = BAYS * TIERS * PER_TIER

station = {
    "station_id": "NH-LANYUAN",
    "name": "兰苑无人菜鸟驿站",
    "status": "designed",
    "layout_version": "v2",
    "truth_level": "observed_counts + designed_arrangement",
    "source": "用户手绘平面图 + 实景照片（2026-11-04）",
    "floor": {"width_m": W, "depth_m": D, "area_m2": round(W * D),
              "area_note": "按货架阵列与通道推算，非实测面积"},
    "params": {"bays": BAYS, "bay_first": BAY_FIRST, "bay_last": BAY_LAST,
               "tiers": TIERS, "slots_per_tier": PER_TIER,
               "bay_length_m": BAY_LEN, "rack_depth_m": DEPTH, "aisle_m": AISLE,
               "cols": COLS, "per_col": PER_COL, "col_width_m": RUN_W,
               "physical_slots": PHYS, "code_format": "货架号-层号-序号"},
    "zones": [ENTRY, COUNTER, RESERVED],
    "rows": cols,
    "notes": [
        "货架按列排布：每列 11 个货架，沿进深方向自上而下编号，列间 0.8 m 通道",
        "545—550 位于最靠近出入口的第一列上端（用户指定）",
        "右上角为保留区，用途未知，图中留空不标注",
        "每个货架只有一个货架号，55 个货架对应 505—559 共 55 个号",
        "照片显示每架 5 层，层号写在红梁标签上（505-1 … 505-5）",
    ],
}

layout = json.load(open(OUT_JSON, encoding='utf-8'))
layout['stations'] = [s for s in layout['stations'] if s['station_id'] != 'NH-LANYUAN'] + [station]
layout['layout_version'] = 'v3'
layout['generated_at'] = '2026-11-04'
json.dump(layout, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

allb = [b for c in cols for b in c['bays']]
print('json <-', OUT_JSON)
print('bays', len(allb), 'unique', len(set(allb)), 'min', min(allb), 'max', max(allb))

# ---------------- 预览图 ----------------
SCALE = 44
PAD_L, PAD_T = 70, 150
IMG_W = 1060
IMG_H = int(D * SCALE) + PAD_T + 140
img = Image.new('RGB', (IMG_W, IMG_H), (250, 250, 252))
dr = ImageDraw.Draw(img)


def font(sz, bold=False):
    for path in ((r'C:\Windows\Fonts\msyhbd.ttc' if bold else r'C:\Windows\Fonts\msyh.ttc'),
                 r'C:\Windows\Fonts\simhei.ttf'):
        try:
            return ImageFont.truetype(path, sz)
        except Exception:
            continue
    return ImageFont.load_default()


F_T = font(32, True); F_S = font(18); F_L = font(19); F_B = font(15, True)
F_R = font(14, True); F_SM = font(13)

dr.text((PAD_L, 24), '兰苑无人菜鸟驿站 · 室内布局', fill=(18, 22, 30), font=F_T)
dr.text((PAD_L, 68), '%d 架 × %d 层 × %d 位 = %d 储位 · %d 列 × 每列 %d 架 · 通道 %.1f m · 占地约 %.0f m²'
        % (BAYS, TIERS, PER_TIER, PHYS, COLS, PER_COL, AISLE, W * D), fill=(90, 100, 118), font=F_S)
dr.text((PAD_L, 94), '货架按列纵向排布（用户 2026-11-04 更正）；依据实景照片 505—559 号货架、每架 5 层',
        fill=(90, 100, 118), font=F_S)

OX = (IMG_W - W * SCALE) // 2
OY = PAD_T
dr.rectangle([OX, OY, OX + W * SCALE, OY + D * SCALE], fill=(241, 244, 249), outline=(150, 160, 178), width=3)

ZC = {"entrance": (63, 169, 124), "counter": (232, 163, 61), "reserved": (214, 218, 226)}
for z in station['zones']:
    x0, y0 = OX + z['x_m'] * SCALE, OY + z['y_m'] * SCALE
    x1, y1 = x0 + z['w_m'] * SCALE, y0 + z['h_m'] * SCALE
    dr.rectangle([x0, y0, x1, y1], fill=ZC[z['kind']], outline=(120, 128, 142))
    if z['label']:
        dr.text((x0 + 10, y0 + 10), z['label'], fill=(255, 255, 255), font=F_L)

ex, ey = OX + ENTRY['x_m'] * SCALE, OY + (ENTRY['y_m'] + ENTRY['h_m'] / 2) * SCALE
dr.line([ex - 34, ey, ex, ey], fill=(63, 169, 124), width=4)
dr.polygon([(ex - 10, ey - 8), (ex, ey), (ex - 10, ey + 8)], fill=(63, 169, 124))

NEAR = set(range(545, 551))
RACK_FILL, NEAR_FILL = (58, 76, 106), (150, 62, 60)
for c in cols:
    x0 = OX + c['x_m'] * SCALE
    y0 = OY + c['y_m'] * SCALE
    w = c['w_m'] * SCALE
    cell = BAY_LEN * SCALE
    for k, bay in enumerate(c['bays']):
        y = y0 + k * cell
        dr.rectangle([x0, y, x0 + w, y + cell],
                     fill=NEAR_FILL if bay in NEAR else RACK_FILL, outline=(20, 30, 44))
        dr.text((x0 + w / 2 - 13, y + cell / 2 - 8), str(bay), fill=(240, 245, 252), font=F_R)
    # 列号写在列的顶部
    dr.text((x0 + w / 2 - 16, y0 - 22), 'C%d' % (c['col'] + 1), fill=(90, 104, 126), font=F_SM)

dr.text((PAD_L, OY + D * SCALE + 18),
        '深蓝＝货架（每架 5 层，双面）· 红棕＝545—550，离出入口最近 · 白色＝0.8 m 通道',
        fill=(95, 105, 122), font=F_S)
dr.text((PAD_L, OY + D * SCALE + 46),
        '绿色＝出入口　橙色＝出库台　浅灰＝保留区（用途未知，按要求留空、不标注）',
        fill=(95, 105, 122), font=F_S)
dr.text((PAD_L, OY + D * SCALE + 74),
        '注：55 个货架对应 505—559 共 55 个号，一号一架不重复；编号自门口第一列起自上而下，到 559 后回到 505。',
        fill=(130, 140, 156), font=F_SM)

os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
img.save(OUT_PNG)
print('png ->', OUT_PNG, img.size)
