# -*- coding: utf-8 -*-
"""Chen 风格 ER 图：实体=方框，联系=菱形，属性=椭圆。

对照用户给的模板重新画：标题在左上、图例在右上（同一行）。
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = r'D:\java大作业'
OUT = os.path.join(ROOT, 'docs', 'db', 'ER-图.png')

W, H = 4800, 2800
BG = (252, 253, 255)
INK = (24, 30, 40)
LINE = (70, 82, 100)
ENT_FILL = (255, 255, 255)
ENT_LINE = (36, 48, 66)
REL_FILL = (255, 246, 224)
REL_LINE = (186, 128, 32)
ATTR_FILL = (245, 248, 253)
ATTR_LINE = (120, 134, 154)
KEY_LINE = (190, 66, 66)

img = Image.new('RGB', (W, H), BG)
dr = ImageDraw.Draw(img)


def font(sz, bold=False):
    path = r'C:\Windows\Fonts\msyhbd.ttc' if bold else r'C:\Windows\Fonts\msyh.ttc'
    try:
        return ImageFont.truetype(path, sz)
    except Exception:
        return ImageFont.load_default()


F_T = font(46, True)
F_SUB = font(20)
F_ENT = font(24, True)
F_REL = font(22)
F_ATTR = font(19)
F_CARD = font(20, True)
F_LEG = font(21)

# ---------------- 基本图元 ----------------
def entity(cx, cy, label, w=230, h=86):
    dr.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=6,
                         fill=ENT_FILL, outline=ENT_LINE, width=3)
    tw = dr.textlength(label, font=F_ENT)
    dr.text((cx - tw / 2, cy - 16), label, fill=INK, font=F_ENT)
    return (cx, cy, w, h)


def diamond(cx, cy, label, w=190, h=104):
    dr.polygon([(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)],
               fill=REL_FILL, outline=REL_LINE, width=3)
    tw = dr.textlength(label, font=F_REL)
    dr.text((cx - tw / 2, cy - 14), label, fill=(120, 78, 16), font=F_REL)


def ellipse(cx, cy, label, key=False):
    tw = dr.textlength(label, font=F_ATTR)
    w = max(150, tw + 44)
    h = 62
    dr.ellipse([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2],
               fill=ATTR_FILL, outline=KEY_LINE if key else ATTR_LINE, width=3 if key else 2)
    dr.text((cx - tw / 2, cy - 13), label, fill=(150, 40, 40) if key else (40, 50, 64), font=F_ATTR)
    if key:
        dr.line([cx - tw / 2, cy + 12, cx + tw / 2, cy + 12], fill=KEY_LINE, width=2)
    return (cx, cy, w, h)


def line(a, b, width=2, color=LINE):
    dr.line([a, b], fill=color, width=width)


def card(x, y, text):
    tw = dr.textlength(text, font=F_CARD)
    dr.rectangle([x - tw / 2 - 6, y - 14, x + tw / 2 + 6, y + 16], fill=BG)
    dr.text((x - tw / 2, y - 12), text, fill=(70, 82, 100), font=F_CARD)


def attrs_above(cx, cy, items, gap=250, dy=-230):
    """属性排成一行放在实体上方，斜线连回实体内"""
    n = len(items)
    x0 = cx - (n - 1) * gap / 2
    for i, (label, key) in enumerate(items):
        ex, ey = x0 + i * gap, cy + dy
        line((ex, ey + 26), (cx, cy - 40), width=2, color=ATTR_LINE)
        ellipse(ex, ey, label, key)


def attrs_below(cx, cy, items, gap=250, dy=230):
    n = len(items)
    x0 = cx - (n - 1) * gap / 2
    for i, (label, key) in enumerate(items):
        ex, ey = x0 + i * gap, cy + dy
        line((ex, ey - 26), (cx, cy + 40), width=2, color=ATTR_LINE)
        ellipse(ex, ey, label, key)


def rel(a, b, label, card_a='1', card_b='N', at=0.5, dxy=(0, 0)):
    ax, ay = a
    bx, by = b
    mx = ax + (bx - ax) * at + dxy[0]
    my = ay + (by - ay) * at + dxy[1]
    line((ax, ay), (mx, my))
    line((mx, my), (bx, by))
    diamond(mx, my, label)
    # 基数标注靠近两端
    card(ax + (mx - ax) * 0.28, ay + (my - ay) * 0.28, card_a)
    card(bx + (mx - bx) * 0.28, by + (my - by) * 0.28, card_b)


# ---------------- 标题 + 图例（同一行） ----------------
dr.text((70, 40), '驿链 CampusFlow · 数据库 ER 图', fill=INK, font=F_T)
dr.text((70, 104), '实体＝方框　联系＝菱形　属性＝椭圆（下划线为主键）　MySQL 8.4 · 15 个实体', fill=(110, 122, 140), font=F_SUB)

# 图例放右上
lx = W - 1180
dr.text((lx, 40), '图例', fill=INK, font=F_T)
# 实体
dr.rounded_rectangle([lx, 108, lx + 92, 152], radius=4, fill=ENT_FILL, outline=ENT_LINE, width=3)
dr.text((lx + 104, 114), '实体（方框）', fill=(60, 72, 88), font=F_LEG)
# 联系
dr.polygon([(lx + 46 - 46, 196), (lx + 46, 172), (lx + 46 + 46, 196), (lx + 46, 220)],
           fill=REL_FILL, outline=REL_LINE, width=3)
dr.text((lx + 104, 184), '联系（菱形）', fill=(60, 72, 88), font=F_LEG)
# 属性
dr.ellipse([lx, 240, lx + 110, 280], fill=ATTR_FILL, outline=ATTR_LINE, width=2)
dr.text((lx + 104 + 20, 250), '属性（椭圆）', fill=(60, 72, 88), font=F_LEG)
# 主键
dr.ellipse([lx + 250, 240, lx + 360, 280], fill=ATTR_FILL, outline=KEY_LINE, width=3)
dr.line([lx + 272, 266, lx + 338, 266], fill=KEY_LINE, width=2)
dr.text((lx + 374, 250), '主键（下划线）', fill=(60, 72, 88), font=F_LEG)
dr.text((lx, 300), '1 / N 标注在联系与实体的连线两端', fill=(120, 132, 150), font=F_SUB)

# ---------------- 左半：空间与包裹 ----------------
S1 = (420, 760)     # 承运商
S2 = (1230, 760)    # 包裹
S3 = (2040, 760)    # 取件码
S4 = (420, 1420)    # 站点
S5 = (1230, 1420)   # 货架排
S6 = (2040, 1420)   # 货架
S7 = (2040, 2050)   # 储位
S8 = (420, 2150)    # 工单
S9 = (1230, 2150)   # 工单事件

# 先画连线（在图形下面）
rel(S1, S2, '承运', '1', 'N')
rel(S2, S3, '标识', '1', '1')
rel(S4, S5, '拥有', '1', 'N')
rel(S5, S6, '组成', '1', 'N')
rel(S6, S7, '包含', '1', 'N')
rel(S7, S2, '存放', '0..1', '1', at=0.55, dxy=(60, -80))
rel(S4, S8, '报障', '1', 'N')
rel(S8, S9, '流转', '1', 'N')

for pt, label in ((S1, '承运商'), (S2, '包裹'), (S3, '取件码'), (S4, '站点'),
                  (S5, '货架排'), (S6, '货架'), (S7, '储位'), (S8, '工单'), (S9, '工单事件')):
    entity(pt[0], pt[1], label)

attrs_above(S1[0], S1[1], [('承运商编码', True), ('名称', False)], gap=230, dy=-250)
attrs_above(S2[0], S2[1], [('包裹号', True), ('站点号', False), ('批次', False)], gap=250, dy=-250)
attrs_above(S3[0], S3[1], [('取件码', True), ('站点号', False), ('包裹号', False)], gap=250, dy=-250)
attrs_above(S4[0], S4[1], [('站点号', True), ('名称', False), ('物理储位', False)], gap=250, dy=-250)
attrs_above(S5[0], S5[1], [('排号', True), ('货架区', False)], gap=230, dy=-250)
attrs_above(S6[0], S6[1], [('货架号', True), ('层数', False)], gap=230, dy=-250)
attrs_below(S7[0], S7[1], [('储位号', True), ('层/位', False)], gap=250, dy=200)
attrs_below(S8[0], S8[1], [('工单号', True), ('状态', False)], gap=250, dy=200)
attrs_below(S9[0], S9[1], [('事件号', True), ('动作', False)], gap=250, dy=200)

# ---------------- 右半：场景与仿真 ----------------
R1 = (2760, 760)    # 参数版本
R2 = (2760, 1420)   # 场景
R3 = (3600, 1420)   # 场景站点参数
R4 = (3600, 2050)   # 逐桶需求
R5 = (2760, 2050)   # 仿真运行
R6 = (3600, 2620)   # 逐桶结果  (下移，避免挤)

rel(R2, R3, '配置', '1', 'N')
rel(R2, R5, '运行', '1', 'N')
rel(R5, R6, '明细', '1', 'N')
rel(R3, R4, '给出', '1', 'N')
rel(R1, R5, '引用', '1', 'N', at=0.5, dxy=(-320, 60))

for pt, label in ((R1, '参数版本'), (R2, '场景'), (R3, '场景站点参数'), (R4, '逐桶需求'),
                  (R5, '仿真运行'), (R6, '逐桶结果')):
    entity(pt[0], pt[1], label, w=250)

attrs_above(R1[0], R1[1], [('版本号', True), ('三档计数', False)], gap=250, dy=-250)
attrs_above(R2[0], R2[1], [('场景号', True), ('第几天', False)], gap=230, dy=-250)
attrs_above(R3[0], R3[1], [('场景号', True), ('站点号', False), ('处理能力', False)], gap=250, dy=-250)
attrs_below(R4[0], R4[1], [('时段', True), ('到件量', False)], gap=250, dy=200)
attrs_below(R5[0], R5[1], [('运行号', True), ('种子', False)], gap=230, dy=200)
attrs_above(R6[0], R6[1], [('Q / I', False), ('风险', False)], gap=230, dy=-210)

# 分区说明
dr.text((300, 430), '空间与包裹', fill=(120, 132, 150), font=font(26, True))
dr.text((2660, 430), '场景与仿真', fill=(120, 132, 150), font=font(26, True))
dr.line([(2380, 400), (2380, 2600)], fill=(214, 220, 230), width=3)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT)
print('saved', OUT, img.size)
