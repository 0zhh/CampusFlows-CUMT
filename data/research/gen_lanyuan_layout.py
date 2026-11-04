# -*- coding: utf-8 -*-
"""兰苑无人菜鸟驿站 · 室内布局生成器 v1

依据：
  · 用户手绘草图：左上出入口 → 出库台 → 货架区；右上保留区（用途未知，留空不标注）
  · 实景照片：货架号为 505—559，5 层（照片里能看到 505-1 … 505-5），红梁双面货架，取件码 = 货架号-层号-序号
  · 用户明确：545—550 号货架离出入口最近

与桃苑的差别：兰苑是无人站，只有 55 个货架号、5 层，没有顺丰区和人工服务台。
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = r'D:\java大作业'
OUT_JSON = os.path.join(ROOT, 'data', 'geo', 'station_layouts.json')
OUT_PNG = os.path.join(ROOT, 'docs', 'screenshots', '兰苑室内布局-v1.png')

BAY_NO_FIRST, BAY_NO_LAST = 505, 559
BAYS = BAY_NO_LAST - BAY_NO_FIRST + 1          # 55
TIERS = 5                                       # 照片可见 5 层
PER_TIER = 20
AISLE = 0.8
DEPTH = 0.6
BAY_LEN = 1.0
LEFT_BAYS, RIGHT_BAYS = 5, 6
BAYS_PER_ROW = LEFT_BAYS + RIGHT_BAYS           # 11
N_ROWS = BAYS // BAYS_PER_ROW                   # 5
assert N_ROWS * BAYS_PER_ROW == BAYS

W, D = 14.0, 15.8
MARGIN_L = 1.4
TOP = 4.4
ROW_PITCH = DEPTH * 2 + AISLE                   # 2.0
RUN_LEN = BAYS_PER_ROW * BAY_LEN                # 11.0

# 编号沿"离出入口由近到远"排；到 559 后回到 505 继续
order = list(range(545, 560)) + list(range(505, 545))
assert len(order) == BAYS

rows = []
for i in range(N_ROWS):
    seq = order[i * BAYS_PER_ROW:(i + 1) * BAYS_PER_ROW]
    rows.append({
        "row_id": "R%02d" % (i + 1),
        "zone_id": "Z-RACK",
        "col": 0,
        "row_in_col": i,
        "x_m": round(MARGIN_L, 2),
        "y_m": round(TOP + i * ROW_PITCH, 2),
        "length_m": RUN_LEN,
        "depth_m": round(DEPTH * 2, 2),
        "left_bays": seq[:LEFT_BAYS],
        "right_bays": seq[LEFT_BAYS:],
        "managed_by": "SELF",
        "tiers": TIERS,
        "slots_per_tier": PER_TIER,
    })

ENTRY = {"id": "Z-ENTRY", "kind": "entrance", "label": "出入口",
         "x_m": 0.2, "y_m": 0.6, "w_m": 1.5, "h_m": 2.6}
COUNTER = {"id": "Z-COUNTER", "kind": "counter", "label": "出库台",
           "x_m": 2.2, "y_m": 0.6, "w_m": 3.6, "h_m": 2.6}
RESERVED = {"id": "Z-RESERVED", "kind": "reserved", "label": "",
            "x_m": 9.6, "y_m": 0.4, "w_m": 4.0, "h_m": 3.4}

PHYS = BAYS * TIERS * PER_TIER

station = {
    "station_id": "NH-LANYUAN",
    "name": "兰苑无人菜鸟驿站",
    "status": "designed",
    "truth_level": "observed_counts + designed_arrangement",
    "source": "用户手绘平面图 + 实景照片（2026-11-04）",
    "floor": {"width_m": W, "depth_m": D, "area_m2": round(W * D),
              "area_note": "按货架阵列与通道推算，非实测面积"},
    "params": {"bays": BAYS, "bay_first": BAY_NO_FIRST, "bay_last": BAY_NO_LAST,
               "tiers": TIERS, "slots_per_tier": PER_TIER,
               "bay_length_m": BAY_LEN, "rack_depth_m": DEPTH, "aisle_m": AISLE,
               "rows": N_ROWS, "bays_per_row": BAYS_PER_ROW,
               "left_bays": LEFT_BAYS, "right_bays": RIGHT_BAYS,
               "physical_slots": PHYS, "code_format": "货架号-层号-序号"},
    "zones": [ENTRY, COUNTER, RESERVED],
    "rows": rows,
    "notes": [
        "545—550 号货架离出入口最近（用户指定），排在最靠近出入口的第一排",
        "右上角为保留区，用途未知，图中留空不标注",
        "照片显示每架 5 层，层号写在红梁标签上（505-1 … 505-5）",
        "取件码规则：货架号-层号-包裹序号，与桃苑一致",
    ],
}

# ---------- 写回 station_layouts.json ----------
layout = json.load(open(OUT_JSON, encoding='utf-8'))
layout['stations'] = [s for s in layout['stations'] if s['station_id'] != 'NH-LANYUAN'] + [station]
layout['layout_version'] = 'v2'
layout['generated_at'] = '2026-11-04'
json.dump(layout, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('json <-', OUT_JSON, 'stations', len(layout['stations']))

# ---------- 预览图 ----------
SCALE = 40
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


F_T = font(32, True)
F_S = font(18)
F_L = font(19)
F_B = font(15, True)
F_R = font(14)

dr.text((PAD_L, 26), '兰苑无人菜鸟驿站 · 室内布局', fill=(18, 22, 30), font=F_T)
dr.text((PAD_L, 72), '%d 架 × %d 层 × %d 位 = %d 储位 · 通道 %.1f m · 占地约 %.0f m²'
        % (BAYS, TIERS, PER_TIER, PHYS, AISLE, W * D), fill=(90, 100, 118), font=F_S)
dr.text((PAD_L, 100), '依据：用户手绘平面图 + 实景照片（505—559 号货架，每架 5 层）',
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

# 出入口箭头
ex = OX + (ENTRY['x_m'] - 0.9) * SCALE
ey = OY + (ENTRY['y_m'] + ENTRY['h_m'] / 2) * SCALE
dr.line([ex, ey, ex + 30, ey], fill=(63, 169, 124), width=4)
dr.polygon([(ex + 30, ey - 8), (ex + 44, ey), (ex + 30, ey + 8)], fill=(63, 169, 124))

NEAR = set(range(545, 551))
RACK_FILL, NEAR_FILL = (58, 76, 106), (150, 62, 60)
RUN_H = DEPTH * 2                     # 双面 1.2 m 画成一整条
for r in rows:
    x0 = OX + r['x_m'] * SCALE
    y0 = OY + r['y_m'] * SCALE
    h = RUN_H * SCALE
    seq = r['left_bays'] + r['right_bays']
    for k, bay in enumerate(seq):
        bx = x0 + k * BAY_LEN * SCALE
        dr.rectangle([bx, y0, bx + BAY_LEN * SCALE, y0 + h],
                     fill=NEAR_FILL if bay in NEAR else RACK_FILL, outline=(20, 30, 44))
        dr.text((bx + BAY_LEN * SCALE / 2 - (14 if bay >= 100 else 8), y0 + h / 2 - 9),
                str(bay), fill=(238, 243, 250), font=F_R)

    dr.text((x0, y0 + h + 6), '%d—%d' % (seq[0], seq[-1]), fill=(90, 104, 126), font=F_B)

dr.text((PAD_L, OY + D * SCALE + 18),
        '深蓝＝双面货架（一条即一排，两面各 5 层）· 红棕＝545—550，离出入口最近 · 白色＝0.8 m 通道',
        fill=(95, 105, 122), font=F_S)
dr.text((PAD_L, OY + D * SCALE + 46),
        '绿色＝出入口　橙色＝出库台　浅灰＝保留区（用途未知，按要求留空、不标注）',
        fill=(95, 105, 122), font=F_S)
dr.text((PAD_L, OY + D * SCALE + 74),
        '注：货架号 505—559 连续 55 架；编号从 545 起按离门远近递增，到 559 后回到 505 继续。',
        fill=(130, 140, 156), font=F_R)

os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
img.save(OUT_PNG)
print('png ->', OUT_PNG, img.size)
print('bays', BAYS, 'slots', PHYS)
