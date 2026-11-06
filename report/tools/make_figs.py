# -*- coding: utf-8 -*-
"""生成报告/PPT 用的图：截图裁剪 + 系统架构图 + 数据可信度示意图。"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = r'D:\java大作业'
SHOTS = os.path.join(ROOT, 'report', 'assets', 'shots')
FIGS = os.path.join(ROOT, 'report', 'assets', 'figs')
os.makedirs(FIGS, exist_ok=True)

MSYH = r'C:\Windows\Fonts\msyh.ttc'
MSYHBD = r'C:\Windows\Fonts\msyhbd.ttc'


def font(size, bold=False):
    return ImageFont.truetype(MSYHBD if bold else MSYH, size)


def crop(src, box, out, quality=None):
    im = Image.open(os.path.join(SHOTS, src)).convert('RGB')
    im.crop(box).save(os.path.join(FIGS, out), quality=95)
    print('crop', out, im.crop(box).size)


# ---------- 截图裁剪 ----------
crop('P1-overview-light-full.png', (0, 0, 1440, 830), 'fig-p1-top.png')
crop('P1-overview-light-full.png', (0, 830, 1440, 1475), 'fig-p1-bottom.png')
crop('P2-sites-light-full.png', (0, 0, 1440, 900), 'fig-p2-top.png')
crop('P3-peak-light-view.png', (0, 0, 1440, 900), 'fig-p3.png')
crop('P4-incidents-light-full.png', (0, 0, 1440, 1189), 'fig-p4.png')
crop('P5-about-light-view.png', (0, 0, 1440, 900), 'fig-p5.png')

# ---------- 系统架构图 ----------
W, H = 2200, 1280
img = Image.new('RGB', (W, H), '#FBFAF6')
d = ImageDraw.Draw(img)

INK = '#1B2A24'
MUTED = '#6B7A73'
AMBER = '#D98324'
PINE = '#2F6F5E'
LINE = '#DCD6C8'
CARD = '#FFFFFF'

BANDS = [
    ('用户层', '浏览器（Chrome / Edge）· 深浅双主题 · 键盘可达 · 1440 宽优先适配', '#F3EFE4'),
    ('表现层', 'Vue 3 + TypeScript + Vite ｜ P1 运营总览 · P2 站点与服务 · P3 高峰与方案 · P4 异常协同 · P5 资料与说明\nLeaflet 双底图 ｜ ECharts 按需引入 ｜ Pinia 状态 ｜ 路由懒加载', '#FFFFFF'),
    ('接口层', 'REST /api ｜ 20 个端点 ｜ JSON ｜ 2.5 s 超时与静默降级 ｜ 失败自动回落到内置样例', '#F7F2E7'),
    ('服务层', 'Spring Boot 3.2.3 ｜ Controller — Service — Repository ｜ 逐桶递推仿真内核\n守恒校验 · 通道可通行率 · 高峰排队 ｜ JPA 持久化 ｜ H2 / MySQL 双 Profile', '#FFFFFF'),
    ('数据层', 'H2 文件库（dev，开箱即用） ｜ MySQL 8.4（prod，15 张表 / 约 2.89 万行）\n离线卫星瓦片 774 张（11.2 MB） ｜ 三场景 × 33 桶逐时段数据', '#F3EFE4'),
]

x0, x1 = 170, W - 250
top = 90
band_h = 168
gap = 34
for i, (name, desc, bg) in enumerate(BANDS):
    y = top + i * (band_h + gap)
    # 左侧标签
    d.rounded_rectangle([x0 - 130, y + 34, x0 - 18, y + band_h - 34], radius=14, fill=INK)
    f = font(30, True)
    tb = d.textbbox((0, 0), name, font=f)
    d.text((x0 - 74 - (tb[2] - tb[0]) / 2, y + band_h / 2 - 22), name, font=f, fill='#FFFFFF')
    # 主框
    d.rounded_rectangle([x0, y, x1, y + band_h], radius=16, fill=bg, outline=LINE, width=2)
    # 顶部色条
    d.rounded_rectangle([x0, y, x0 + 8, y + band_h], radius=4, fill=AMBER if i in (1, 2) else PINE)
    lines = desc.split('\n')
    f2 = font(27)
    ty = y + (band_h - len(lines) * 40) / 2
    for ln in lines:
        d.text((x0 + 40, ty), ln, font=f2, fill=INK)
        ty += 40
    # 箭头
    if i < len(BANDS) - 1:
        cx = (x0 + x1) / 2
        ay = y + band_h + 6
        d.line([cx, ay, cx, ay + gap - 12], fill=MUTED, width=3)
        d.polygon([(cx - 8, ay + gap - 16), (cx + 8, ay + gap - 16), (cx, ay + gap - 2)], fill=MUTED)

# 右侧参数竖条
rxx0, rxx1 = x1 + 40, W - 40
d.rounded_rectangle([rxx0, top, rxx1, top + 4 * (band_h + gap) + band_h - gap], radius=16, fill='#1B2A24')
f3 = font(30, True)
for i, t in enumerate(['参', '数', '注', '册', '表']):
    d.text((rxx0 + 52, top + 90 + i * 46), t, font=f3, fill='#F6E7C8')
d.text((rxx0 + 30, top + 380), '31 项参数', font=font(28, True), fill='#FFFFFF')
for i, t in enumerate(['10 实测', '1 公开', '19 假设', '1 混合']):
    d.text((rxx0 + 30, top + 440 + i * 40), t, font=font(24), fill='#C9C2AE')
d.text((rxx0 + 30, top + 640), '每项带', font=font(23), fill='#C9C2AE')
d.text((rxx0 + 30, top + 672), '区间 + 理由', font=font(23), fill='#C9C2AE')
d.text((rxx0 + 30, top + 704), '+ 出处', font=font(23), fill='#C9C2AE')

# 底部注释
d.text((x0 - 130, H - 70), '实线为调用方向；参数注册表同时约束服务层仿真与前端标签，保证“每个数字都能回答来源”。',
       font=font(24), fill=MUTED)

img.save(os.path.join(FIGS, 'fig-architecture.png'))
print('saved fig-architecture.png', img.size)

# ---------- 数据可信度三档示意 ----------
W2, H2 = 2200, 508
img2 = Image.new('RGB', (W2, H2), '#F7F4EC')
d2 = ImageDraw.Draw(img2)
cards = [
    ('实测 measured', '10 项', '实景照片读数 / 本机脚本测量', '例：货架 240 架、通道 0.8 m', '#2F6F5E', '用于：储位、货架、通道、取件码'),
    ('公开 public', '1 项', '学生手册、总务部报道、商品规格', '例：取件码规则、营业时间', '#3C6E9F', '用于：营业时间、服务分工'),
    ('假设 assumed', '19 + 1 项', '带区间与理由的运营假设', '例：日到件 ∈ [11,000, 16,000]', '#D98324', '用于：到件、到车、取件、排队'),
]
cw = 680
gap2 = 30
sx = (W2 - 3 * cw - 2 * gap2) / 2
for i, (title, cnt, l1, l2, color, l3) in enumerate(cards):
    x = sx + i * (cw + gap2)
    d2.rounded_rectangle([x, 16, x + cw, H2 - 16], radius=18, fill='#FFFFFF', outline='#E4DECF', width=2)
    d2.rounded_rectangle([x, 16, x + cw, 26], radius=6, fill=color)
    d2.text((x + 34, 52), title, font=font(30, True), fill=color)
    d2.text((x + 34, 100), cnt, font=font(52, True), fill='#1B2A24')
    d2.text((x + 34, 190), l1, font=font(22), fill='#4A5A53')
    d2.text((x + 34, 228), l2, font=font(22), fill='#4A5A53')
    d2.text((x + 34, 300), l3, font=font(20), fill='#8A9790')
img2.save(os.path.join(FIGS, 'fig-trust.png'))
print('saved fig-trust.png', img2.size)

# ---------- 8.6 用的两张高清图 ----------
crop('P1-map-expand-light-view.png', (18, 28, 1422, 872), 'fig-map-expand.png')
print('plan:', os.path.join(FIGS, 'fig-plan.png'))
