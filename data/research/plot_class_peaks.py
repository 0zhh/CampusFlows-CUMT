# -*- coding: utf-8 -*-
"""画出"课表版"取件曲线：上课时段是低谷，课间是高峰。"""
import csv
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = r'D:\java大作业'
D = os.path.join(ROOT, 'data', 'demo')
OUT = os.path.join(ROOT, 'docs', 'db', '出库曲线-课表版.png')

SITES = [('桃苑', 2), ('松苑', 3), ('梅苑', 4), ('兰苑', 5)]
COLORS = {'桃苑': (58, 96, 168), '松苑': (196, 132, 48), '梅苑': (60, 150, 120), '兰苑': (150, 90, 160)}

rows = list(csv.DictReader(open(os.path.join(D, 'nov_outbound_wide.csv'), encoding='utf-8-sig')))
day = [r for r in rows if r['日期'] == '2026-11-11']
series = {name: [0] * 144 for name, _ in SITES}
total = [0] * 144
for r in day:
    i = int(r['时间'][:2]) * 6 + int(r['时间'][3:]) // 10
    s = 0
    for name, _ in SITES:
        v = int(r[name])
        series[name][i] = v
        s += v
    total[i] = s

W, H = 1900, 900
img = Image.new('RGB', (W, H), (252, 253, 255))
dr = ImageDraw.Draw(img)


def font(sz, bold=False):
    p = r'C:\Windows\Fonts\msyhbd.ttc' if bold else r'C:\Windows\Fonts\msyh.ttc'
    try:
        return ImageFont.truetype(p, sz)
    except Exception:
        return ImageFont.load_default()


F_T = font(36, True); F = font(18); F_S = font(15); F_B = font(17, True); F_XS = font(13)
dr.text((70, 30), '取件（出库）日内曲线 · 按课程表设计', fill=(24, 30, 40), font=F_T)
dr.text((70, 80), '上课时段（8:00-12:00 / 14:00-18:00 / 19:00-20:45）是低谷，课间是高峰 · 数据为 2026-11-11 模拟值',
        fill=(110, 122, 140), font=F)

X0, Y0, WD, HT = 100, 190, 1700, 470
mx = max(total) * 1.12


def px(i): return X0 + i / 143 * WD
def py(v): return Y0 + HT - v / mx * HT


# 上课时段底纹
for (a, b) in [(8, 12), (14, 18), (19, 20.75)]:
    x1, x2 = px(int(a * 6)), px(int(b * 6))
    dr.rectangle([x1, Y0, x2, Y0 + HT], fill=(232, 234, 240))
    dr.text(((x1 + x2) / 2 - 26, Y0 + HT - 26), '上课', fill=(120, 126, 140), font=F_S)
# 高峰时段底纹
for (a, b, lab) in [(7, 8, '早课前'), (12, 14, '午休'), (18, 19, '晚饭'), (20.75, 23, '晚课后')]:
    x1, x2 = px(int(a * 6)), px(int(b * 6))
    dr.rectangle([x1, Y0, x2, Y0 + HT], fill=(255, 245, 228))
    dr.text(((x1 + x2) / 2 - len(lab) * 8, Y0 + 10), lab, fill=(180, 120, 30), font=F_S)

# 轴
dr.line([X0, Y0 + HT, X0 + WD, Y0 + HT], fill=(200, 206, 216), width=2)
for i in range(0, 144, 6):
    dr.text((px(i) - 14, Y0 + HT + 10), '%02d:00' % (i // 6), fill=(120, 130, 146), font=F_XS)

# 各站曲线
for name, _ in SITES:
    pts = [(px(i), py(v)) for i, v in enumerate(series[name])]
    dr.line(pts, fill=COLORS[name], width=3, joint='curve')
# 合计曲线（粗）
pts = [(px(i), py(v)) for i, v in enumerate(total)]
dr.line(pts, fill=(90, 96, 110), width=5, joint='curve')

# 峰值标注
peak_i = max(range(144), key=lambda i: total[i])
dr.text((px(peak_i) - 40, py(total[peak_i]) - 34), '峰值 %d 件/10 分钟' % total[peak_i],
        fill=(40, 48, 62), font=F_B)

# 图例
lx, ly = 110, 700
dr.text((lx, ly), '图例', fill=(40, 50, 64), font=F_B)
dr.line([lx, ly + 34, lx + 34, ly + 34], fill=(90, 96, 110), width=5)
dr.text((lx + 42, ly + 24), '四站合计', fill=(70, 82, 100), font=F_S)
for k, (name, _) in enumerate(SITES):
    x = lx + 190 + k * 150
    dr.line([x, ly + 34, x + 34, ly + 34], fill=COLORS[name], width=3)
    dr.text((x + 42, ly + 24), name, fill=(70, 82, 100), font=F_S)

# 说明
dr.text((110, 780), '为什么这样设计：学生在上课时间不能离开教室，取件只能发生在四个窗口 —— ',
        fill=(80, 92, 108), font=F_S)
dr.text((110, 812), '早课前的 7:00-8:00、午休 12:00-14:00、晚饭 18:00-19:00、晚课后的 20:45-23:00。',
        fill=(80, 92, 108), font=F_S)
dr.text((110, 844), '桃苑 18:30 关门，接不到晚课后那一波；这三小时基本全压在三个无人站身上。',
        fill=(170, 90, 40), font=F_S)

img.save(OUT)
print('saved', OUT, img.size)
