# -*- coding: utf-8 -*-
"""给 PPT 用的宽幅架构图（2600×1080，约 2.4:1），与报告里的版本同风格。"""
import os
from PIL import Image, ImageDraw, ImageFont

FIGS = r'D:\java大作业\report\assets\figs'
MSYH = r'C:\Windows\Fonts\msyh.ttc'
MSYHBD = r'C:\Windows\Fonts\msyhbd.ttc'


def font(size, bold=False):
    return ImageFont.truetype(MSYHBD if bold else MSYH, size)


W, H = 2600, 1080
img = Image.new('RGB', (W, H), '#FFFFFF')
d = ImageDraw.Draw(img)
INK = '#1B2A24'
MUTED = '#6B7A73'
AMBER = '#D98324'
PINE = '#2F6F5E'
LINE = '#DCD6C8'
CARD = '#FFFFFF'

BANDS = [
    ('用户层', '浏览器（Chrome / Edge）· 深浅双主题 · 键盘可达 · 1440 宽优先适配', '#F6F3EA'),
    ('表现层', 'Vue 3 + TypeScript + Vite ｜ P1 运营总览 · P2 站点与服务 · P3 高峰与方案 · P4 异常协同 · P5 资料与说明\nLeaflet 双底图 ｜ ECharts 按需引入 ｜ Pinia 状态 ｜ 路由懒加载', '#FFFFFF'),
    ('接口层', 'REST /api ｜ 20 个端点 ｜ JSON ｜ 2.5 s 超时与静默降级 ｜ 失败自动回落到内置样例', '#FBF7EE'),
    ('服务层', 'Spring Boot 3.2.3 ｜ Controller — Service — Repository ｜ 逐桶递推仿真内核\n守恒校验 · 通道可通行率 · 高峰排队 ｜ JPA 持久化 ｜ H2 / MySQL 双 Profile', '#FFFFFF'),
    ('数据层', 'H2 文件库（dev，开箱即用） ｜ MySQL 8.4（prod，15 张表 / 约 2.89 万行）\n离线卫星瓦片 774 张（11.2 MB） ｜ 三场景 × 33 桶逐时段数据', '#F6F3EA'),
]

x0, x1 = 175, W - 250
top = 56
band_h = 172
gap = 26
for i, (name, desc, bgcolor) in enumerate(BANDS):
    y = top + i * (band_h + gap)
    d.rounded_rectangle([x0 - 135, y + 30, x0 - 18, y + band_h - 30], radius=12, fill=INK)
    f = font(27, True)
    tb = d.textbbox((0, 0), name, font=f)
    d.text((x0 - 76 - (tb[2] - tb[0]) / 2, y + band_h / 2 - 20), name, font=f, fill='#FFFFFF')
    d.rounded_rectangle([x0, y, x1, y + band_h], radius=14, fill=bgcolor, outline=LINE, width=2)
    d.rounded_rectangle([x0, y, x0 + 7, y + band_h], radius=3, fill=AMBER if i in (1, 2) else PINE)
    lines = desc.split('\n')
    f2 = font(24)
    ty = y + (band_h - len(lines) * 34) / 2
    for ln in lines:
        d.text((x0 + 34, ty), ln, font=f2, fill=INK)
        ty += 34
    if i < len(BANDS) - 1:
        cx = (x0 + x1) / 2
        ay = y + band_h + 4
        d.line([cx, ay, cx, ay + gap - 10], fill=MUTED, width=3)
        d.polygon([(cx - 7, ay + gap - 14), (cx + 7, ay + gap - 14), (cx, ay + gap - 3)], fill=MUTED)

rxx0, rxx1 = x1 + 35, W - 30
d.rounded_rectangle([rxx0, top, rxx1, top + 4 * (band_h + gap) + band_h], radius=14, fill='#12211B')
f3 = font(27, True)
for i, t in enumerate(['参', '数', '注', '册', '表']):
    d.text((rxx0 + 44, top + 56 + i * 40), t, font=f3, fill='#F6E7C8')
d.text((rxx0 + 26, top + 300), '31 项参数', font=font(25, True), fill='#FFFFFF')
for i, t in enumerate(['10 实测', '1 公开', '19 假设', '1 混合']):
    d.text((rxx0 + 26, top + 350 + i * 36), t, font=font(21), fill='#C9C2AE')
d.text((rxx0 + 26, top + 540), '每项都带', font=font(19), fill='#C9C2AE')
d.text((rxx0 + 26, top + 570), '区间 · 理由', font=font(19), fill='#C9C2AE')
d.text((rxx0 + 26, top + 600), '· 出处', font=font(19), fill='#C9C2AE')

out = os.path.join(FIGS, 'fig-architecture-wide.png')
img.save(out)
print('saved', out, img.size)
