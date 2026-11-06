# -*- coding: utf-8 -*-
"""生成《驿链 CampusFlow》5 分钟答辩 PPT（16:9，含演讲备注）。"""
import os

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = r'D:\java大作业'
FIGS = os.path.join(ROOT, 'report', 'assets', 'figs')
OUT = os.path.join(ROOT, 'report', '驿链CampusFlow_答辩PPT_5min.pptx')

# ---------- 设计系统 ----------
INK = RGBColor(0x14, 0x21, 0x1C)
INK2 = RGBColor(0x3A, 0x4A, 0x43)
MUTED = RGBColor(0x6B, 0x7A, 0x73)
PAPER = RGBColor(0xF7, 0xF4, 0xEC)
CARD = RGBColor(0xFF, 0xFF, 0xFF)
AMBER = RGBColor(0xD9, 0x83, 0x24)
PINE = RGBColor(0x2F, 0x6F, 0x5E)
LINE = RGBColor(0xDC, 0xD6, 0xC8)
CREAM = RGBColor(0xF1, 0xEA, 0xD9)
FONT = '微软雅黑'

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

W = 13.333
H = 7.5
ML = 0.72


def _set_font(run, size, bold=False, color=INK, font=FONT, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font
    run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', font)


def text(slide, x, y, w, h, lines, size=16, bold=False, color=INK, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, line_spacing=1.25, space_after=4, font=FONT):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    if isinstance(lines, str):
        lines = [lines]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)
        if isinstance(ln, tuple):
            txt, opt = ln
        else:
            txt, opt = ln, {}
        r = p.add_run()
        r.text = txt
        _set_font(r, opt.get('size', size), opt.get('bold', bold),
                  opt.get('color', color), font)
    return box


def rect(slide, x, y, w, h, fill=None, line=None, line_w=0.75, radius=False, shape=None):
    st = shape or (MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE)
    sp = slide.shapes.add_shape(st, Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        try:
            sp.adjustments[0] = 0.04
        except Exception:
            pass
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(line_w)
    sp.shadow.inherit = False
    tf = sp.text_frame
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    return sp


def pic_fill(slide, path, x, y, w, h, border=True):
    """按目标框裁切图片（cover 方式），保持比例。"""
    iw, ih = Image.open(path).size
    target = w / h
    src = iw / ih
    pic = slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
    if src > target:  # 源更宽，裁左右
        frac = (1 - target / src) / 2
        pic.crop_left = frac
        pic.crop_right = frac
    elif src < target:  # 源更高，裁上下
        frac = (1 - src / target) / 2
        pic.crop_top = frac
        pic.crop_bottom = frac
    if border:
        pic.line.color.rgb = LINE
        pic.line.width = Pt(0.75)
    return pic


def pic_contain(slide, path, x, y, w, h, border=True):
    """等比缩放到框内（不裁切），在框中居中。"""
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    px, py = x + (w - pw) / 2, y + (h - ph) / 2
    pic = slide.shapes.add_picture(path, Inches(px), Inches(py), Inches(pw), Inches(ph))
    if border:
        pic.line.color.rgb = LINE
        pic.line.width = Pt(0.75)
    return pic


def bg(slide, color=PAPER):
    b = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    b.fill.solid()
    b.fill.fore_color.rgb = color
    b.line.fill.background()
    b.shadow.inherit = False
    # 置于底层
    sp = b._element
    sp.getparent().remove(sp)
    slide.shapes._spTree.insert(2, sp)
    return b


def head(slide, num, kicker, title, sub=None, dark=False):
    c1 = AMBER
    c2 = RGBColor(0xFF, 0xFF, 0xFF) if dark else INK
    c3 = RGBColor(0xC9, 0xC2, 0xAE) if dark else MUTED
    text(slide, ML, 0.42, 6.0, 0.3, [(f'{num}  {kicker}', {'size': 10.5, 'bold': True, 'color': c1})])
    text(slide, ML, 0.72, 11.9, 0.7, [(title, {'size': 30, 'bold': True, 'color': c2})])
    if sub:
        text(slide, ML, 1.32, 11.4, 0.4, [(sub, {'size': 12.5, 'color': c3})])
    ln = rect(slide, ML, 1.72, 11.9, 0.012, fill=(RGBColor(0x3A, 0x4A, 0x43) if dark else LINE))


def footer(slide, idx, dark=False):
    c = RGBColor(0x8C, 0x9A, 0x93) if dark else MUTED
    text(slide, ML, 6.98, 6.0, 0.25, [('驿链 CampusFlow · 中国矿业大学南湖校区', {'size': 9, 'color': c})])
    text(slide, W - 1.3, 6.98, 0.6, 0.25, [(f'{idx:02d}', {'size': 9, 'color': c})], align=PP_ALIGN.RIGHT)


def note(slide, s):
    slide.notes_slide.notes_text_frame.text = s


def stat(slide, x, y, w, value, unit, label, color=INK):
    rect(slide, x, y, w, 1.42, fill=CARD, line=LINE, radius=True)
    text(slide, x + 0.26, y + 0.2, w - 0.4, 0.6, [(value, {'size': 30, 'bold': True, 'color': color})])
    if unit:
        text(slide, x + 0.26, y + 0.82, w - 0.4, 0.3, [(unit, {'size': 11, 'color': MUTED})])
    text(slide, x + 0.26, y + 1.08, w - 0.4, 0.28, [(label, {'size': 10.5, 'color': INK2})])


# ======================================================================
# 1 封面
# ======================================================================
s = prs.slides.add_slide(BLANK)
bg(s, INK)
rect(s, 0, 0, 0.22, H, fill=AMBER)
text(s, 1.0, 0.9, 8.0, 0.3, [('中国矿业大学 · Java 语言及网络编程 · 课程结课作业', {'size': 11.5, 'color': AMBER, 'bold': True})])
text(s, 1.0, 1.55, 11.0, 1.4, [('驿链 CampusFlow', {'size': 60, 'bold': True, 'color': RGBColor(0xFF, 0xFF, 0xFF)})])
text(s, 1.0, 3.02, 11.0, 0.6, [('中国矿业大学南湖校区校园物流管理系统的设计与实现', {'size': 22, 'color': CREAM})])
rect(s, 1.0, 3.92, 1.5, 0.03, fill=AMBER)
text(s, 1.0, 4.15, 10.6, 0.9,
     [('规格驱动开发（SDD）  ×  宏观—微观双层仿真  ×  Vue 3 + Spring Boot 前后端分离',
       {'size': 13, 'color': RGBColor(0xC9, 0xC2, 0xAE)})])
text(s, 1.0, 6.25, 11.0, 0.5,
     [('答辩人：____________    学号：____________    指导教师：____________    2026 年 11 月',
       {'size': 11.5, 'color': RGBColor(0x9F, 0x94, 0x7E)})])
note(s, '开场 10 秒：各位老师好，我是___，我做的是南湖校区的校园物流管理系统“驿链 CampusFlow”。'
        '今天用五分钟讲三件事：为什么做、怎么做、做成了什么。')

# ======================================================================
# 2 问题
# ======================================================================
s = prs.slides.add_slide(BLANK)
bg(s)
head(s, '01', '问题', '一个“数据拿不到”的系统')
text(s, ML, 1.98, 11.6, 0.9,
     [('南湖校区是“一主三辅”的四站格局：桃苑主站 + 松苑、梅苑、兰苑三座无人快递超市，竹苑另设收发室。',
       {'size': 15, 'color': INK2}),
      ('决定体验的量——每天到多少件、几点到车、货架还剩多少、取件排多久——都在运营方手里。',
       {'size': 15, 'color': INK2})])

cards = [
    ('数据约束', '运营数据一条也拿不到\n既不能编，也不能装作有', AMBER),
    ('时间约束', '一个课程周期\n必须先做完，再做深', PINE),
    ('解释约束', '面对的评委不是运营专家\n每个数字都要能回答来源', RGBColor(0x3C, 0x6E, 0x9F)),
]
for i, (t, d, c) in enumerate(cards):
    x = ML + i * 4.02
    rect(s, x, 3.5, 3.72, 1.9, fill=CARD, line=LINE, radius=True)
    rect(s, x, 3.5, 0.06, 1.9, fill=c)
    text(s, x + 0.28, 3.72, 3.2, 0.35, [(t, {'size': 14, 'bold': True, 'color': c})])
    text(s, x + 0.28, 4.14, 3.2, 1.0, [(ln, {'size': 11.5, 'color': INK2}) for ln in d.split('\n')])

text(s, ML, 5.75, 11.8, 0.8,
     [('于是问题被重新定义：不是“做一个好看的看板”，而是“做一个每个数字都能回答来源的系统”。',
       {'size': 16, 'bold': True, 'color': INK})])
footer(s, 2)
note(s, '25 秒：这个项目最大的难点不是写代码，是数据。校园快递的真实运营数据学生拿不到。'
        '所以我没有编数据，而是把“数据不可得”当成设计前提，这就引出了下一页的方法。')

# ======================================================================
# 3 方法
# ======================================================================
s = prs.slides.add_slide(BLANK)
bg(s)
head(s, '02', '方法论', '把“不可知”变成“可替换”')
text(s, ML, 1.95, 11.8, 0.4,
     [('31 项参数，每一项都带 source（来源档位）、range（区间）、rationale（理由）与 swap_hint（怎么换）。',
       {'size': 13, 'color': INK2})])
pic_fill(s, os.path.join(FIGS, 'fig-trust.png'), ML, 2.42, 11.9, 2.75)

rules = [
    ('数值可溯源', '实测 / 公开 / 假设，三档标签页面可查'),
    ('假设有区间', '每项假设给上下界与理由，脚本自动校验'),
    ('结论用相对量', '“占用 92.9%”而不是“剩 3080 件”，参数扰动下结论不反转'),
]
for i, (t, d) in enumerate(rules):
    x = ML + i * 4.02
    text(s, x, 5.55, 3.7, 0.3, [(f'0{i + 1}', {'size': 10, 'bold': True, 'color': AMBER})])
    text(s, x, 5.82, 3.7, 0.32, [(t, {'size': 13.5, 'bold': True, 'color': INK})])
    text(s, x, 6.16, 3.55, 0.6, [(d, {'size': 10.5, 'color': INK2})])
footer(s, 3)
note(s, '30 秒：方法是三档可信度。10 项来自实景照片实测，1 项来自公开规格，20 项是带区间的假设。'
        '页面上的每个数字都带标签，结论一律用相对量，这样参数在区间内怎么变，结论方向都不变。'
        '这也是我觉得这个项目最像“工程”而不是“作业”的地方。')

# ======================================================================
# 4 架构
# ======================================================================
s = prs.slides.add_slide(BLANK)
bg(s)
head(s, '03', '架构', '五层结构，一条参数主线')
pic_contain(s, os.path.join(FIGS, 'fig-architecture.png'), ML, 1.9, 7.85, 4.6)
text(s, 8.9, 1.95, 3.8, 0.3, [('为什么长这样', {'size': 12, 'bold': True, 'color': AMBER})])
text(s, 8.9, 2.3, 3.75, 2.6,
     [('· 前后端分离：前端可离线演示，后端可独立部署', {'size': 10.5, 'color': INK2}),
      ('· 双数据库：H2 克隆即跑，MySQL 才是完整形态', {'size': 10.5, 'color': INK2}),
      ('· 参数注册表：同时约束服务端计算与前端标签', {'size': 10.5, 'color': INK2}),
      ('· 降级路径：接口不通就回落样例，演示不白屏', {'size': 10.5, 'color': INK2})], line_spacing=1.5)
text(s, 8.9, 5.35, 3.8, 1.0,
     [('一句话：架构里每一层都知道“数据可能不可靠”。', {'size': 10.5, 'color': MUTED})])
text(s, ML, 6.62, 7.8, 0.3,
     [('前端 5 页 · 后端 20 个 REST 接口 · 15 表 · 774 张离线瓦片', {'size': 10, 'color': MUTED})])
footer(s, 4)
note(s, '25 秒：技术上是标准的前后端分离，Vue 3 加 Spring Boot。我特意保留了双数据库形态：'
        'H2 让老师克隆下来就能跑，MySQL 形态才开五个增强接口。右边这条参数注册表贯穿前后端，'
        '所以“数据可信”是架构属性，不是文档口号。')

# ======================================================================
# 5 功能地图
# ======================================================================
s = prs.slides.add_slide(BLANK)
bg(s)
head(s, '04', '功能', '五页一图：从“看到”到“处置”')
items = [
    ('P1', '运营总览', '六项 KPI、四站状态、取件码查询、流量曲线、本周推演', AMBER),
    ('P2', '站点与服务', '站点档案、30 分钟运行表、室内平面图逐排逐格', PINE),
    ('P3', '高峰与方案', '双库存堆叠、需求与能力、方案对比、风险时段清单', RGBColor(0x3C, 0x6E, 0x9F)),
    ('P4', '异常协同', '自动建单、状态写回数据库、事件时间线', RGBColor(0xA8, 0x4E, 0x6B)),
    ('P5', '资料与说明', '三档标签、公开来源清单、模型假设、不做清单', RGBColor(0x6B, 0x6B, 0x5E)),
]
for i, (code, name, desc, c) in enumerate(items):
    x = ML + (i % 3) * 4.02
    y = 2.0 + (i // 3) * 2.05
    rect(s, x, y, 3.72, 1.8, fill=CARD, line=LINE, radius=True)
    text(s, x + 0.26, y + 0.2, 1.0, 0.35, [(code, {'size': 20, 'bold': True, 'color': c})])
    text(s, x + 1.0, y + 0.26, 2.5, 0.3, [(name, {'size': 13.5, 'bold': True, 'color': INK})])
    text(s, x + 0.26, y + 0.78, 3.2, 0.85, [(desc, {'size': 10.5, 'color': INK2})])
text(s, ML + 8.04, 4.05, 3.7, 1.75,
     [('地图是第六个“页面”', {'size': 13.5, 'bold': True, 'color': AMBER}),
      ('双底图、四站四入口、在途车辆与批次、人工校准，都收在一次“放大”里。', {'size': 10.5, 'color': INK2})])
text(s, ML, 6.35, 11.8, 0.3,
     [('一套数据、五个视角：任何一页都能回答“这个数哪来的”。', {'size': 11.5, 'color': MUTED})])
footer(s, 5)
note(s, '20 秒：五个页面不是五个功能堆叠，而是五类任务：巡检、查档、预案、处置、溯源。'
        '第六个“页面”是地图的放大态，下一页单独说。')

# ======================================================================
# 6 地图
# ======================================================================
s = prs.slides.add_slide(BLANK)
bg(s)
head(s, '05', '空间', '地图不是背景，是工作台')
pic_fill(s, os.path.join(FIGS, 'fig-map-expand.png'), 5.05, 1.95, 7.6, 4.55)
text(s, ML, 2.0, 4.0, 0.3, [('双底图', {'size': 12, 'bold': True, 'color': AMBER})])
text(s, ML, 2.3, 4.05, 0.6,
     [('实景影像（774 张瓦片离线缓存）与手册原图可切换，红点与站点图标重合。', {'size': 10.5, 'color': INK2})])
text(s, ML, 3.15, 4.0, 0.3, [('三件事在地图上发生', {'size': 12, 'bold': True, 'color': AMBER})])
text(s, ML, 3.45, 4.05, 1.5,
     [('· 四站与四个入口的相对位置', {'size': 10.5, 'color': INK2}),
      ('· 配送路径与在途车辆（13:10，本批 244 件、4 车）', {'size': 10.5, 'color': INK2}),
      ('· 手工校准：拖图 → 反算经纬度 → 持久化', {'size': 10.5, 'color': INK2})])
text(s, ML, 5.15, 4.0, 0.3, [('诚实边界', {'size': 12, 'bold': True, 'color': AMBER})])
text(s, ML, 5.45, 4.05, 0.9,
     [('坐标是相对方位推定，不是测绘成果；车辆位置是线性插值，不是真实 GPS。页面上都标了。',
       {'size': 10.5, 'color': INK2})])
footer(s, 6)
note(s, '25 秒：地图是我个人最满意的一页。它不只是画点，而是把配送路径、在途车辆、批次时间都放进来了。'
        '自动配准试了四种都不收敛，最后做了人工校准工具——这个失败也写进了报告。')

# ======================================================================
# 7 P1
# ======================================================================
s = prs.slides.add_slide(BLANK)
bg(s)
head(s, '06', '界面 · P1', '运营总览：一屏看清四个站')
pic_fill(s, os.path.join(FIGS, 'fig-p1-top.png'), ML, 1.95, 7.55, 4.35)
xs = 8.55
stat(s, xs, 1.95, 1.95, '17,050', '件 · 四站合计', '当日到件', AMBER)
stat(s, xs + 2.05, 1.95, 1.95, '92.9', '% · 松苑', '最高占用率', RGBColor(0xC0, 0x39, 0x2B))
stat(s, xs, 3.55, 1.95, '166.7', '分钟 · 高峰', '最长排队', RGBColor(0xC0, 0x39, 0x2B))
stat(s, xs + 2.05, 3.55, 1.95, '0', '件', '未满足取件', PINE)
text(s, xs, 5.2, 4.0, 1.1,
     [('两项自定义指标：', {'size': 10.5, 'bold': True, 'color': INK}),
      ('“通道可通行率”把货堆进通道折算成百分比；“高峰排队”把排队折算成分钟。',
       {'size': 10, 'color': INK2})])
footer(s, 7)
note(s, '25 秒：总览一屏六个数。除了常规的到件、取件，我加了两个自己定义的指标：通道可通行率、高峰排队。'
        '因为运营的人不关心“库存多少件”，他关心“通道还走得动吗、队排多长”。')

# ======================================================================
# 8 P2
# ======================================================================
s = prs.slides.add_slide(BLANK)
bg(s)
head(s, '07', '界面 · P2', '站点与服务：从站点到储位')
pic_fill(s, os.path.join(FIGS, 'fig-p2-top.png'), ML, 1.95, 6.95, 4.34)
pic_contain(s, os.path.join(FIGS, 'fig-plan.png'), 7.9, 1.9, 2.95, 3.1)
text(s, 11.0, 1.98, 2.2, 2.4,
     [('240 架', {'size': 17, 'bold': True, 'color': AMBER}),
      ('× 5 层', {'size': 17, 'bold': True, 'color': AMBER}),
      ('× 20 位', {'size': 17, 'bold': True, 'color': AMBER}),
      ('= 24,000 个储位', {'size': 11, 'color': INK2})], line_spacing=1.45)
text(s, 7.9, 5.22, 4.85, 1.1,
     [('室内平面按实景照片的参数生成', {'size': 11, 'bold': True, 'color': INK}),
      ('点“排”展开储位矩阵，点格子显示取件码与承运商；0.8 m 的通道是现场量的。',
       {'size': 10, 'color': INK2})])
text(s, ML, 6.45, 6.9, 0.3,
     [('30 分钟一行的运行表，越限整行标红。', {'size': 10.5, 'color': MUTED})])
footer(s, 8)
note(s, '25 秒：站点页有两个层次：站点档案和现场。运行表精细到 30 分钟，越限整行标红；'
        '室内平面图能从“排”钻到“储位”，点格子直接看到取件码。储位总数 24000，和宏观模型的待取上限是同一套数。')

# ======================================================================
# 9 P3
# ======================================================================
s = prs.slides.add_slide(BLANK)
bg(s)
head(s, '08', '界面 · P3', '高峰与方案：双 11 第 7 天会怎样')
pic_fill(s, os.path.join(FIGS, 'fig-p3.png'), ML, 1.95, 7.05, 4.41)
xs = 8.9
stat(s, xs, 1.95, 1.85, '83.4', '% · 桃苑', 'S2 占用率 · 预警', AMBER)
stat(s, xs + 1.95, 1.95, 1.85, '52', '个 · 四站', '风险时段', RGBColor(0xC0, 0x39, 0x2B))
stat(s, xs, 3.55, 1.85, '88.2', '分钟', '桃苑高峰排队', RGBColor(0xC0, 0x39, 0x2B))
stat(s, xs + 1.95, 3.55, 1.85, '38.8', '分钟', '分流增能后', PINE)
text(s, xs, 5.2, 3.85, 1.2,
     [('三个场景：S1 常态 → S2 双 11 第 7 天 → S3 分流增能。',
       {'size': 10, 'color': INK2}),
      ('S3 把排队压掉了 56%，但无人站占用只降 0.7 个百分点——瓶颈在取件侧，不在到件侧。',
       {'size': 10, 'color': INK2})])
footer(s, 9)
note(s, '30 秒：这是全系统的核心结论。双 11 第 7 天，桃苑 83.4% 预警，三个无人站 89% 到 93% 限流。'
        '做了分流增能之后，排队从 88 分钟压到 39 分钟，但无人站占用几乎没降——说明瓶颈在取件侧。'
        '这条结论比任何一张图都有价值。')

# ======================================================================
# 10 P4
# ======================================================================
s = prs.slides.add_slide(BLANK)
bg(s)
head(s, '09', '界面 · P4', '异常协同：工单不是写死的')
pic_contain(s, os.path.join(FIGS, 'fig-p4-ppt.png'), ML, 1.95, 7.05, 4.4)
text(s, 8.05, 1.98, 4.6, 0.3, [('工单从哪来', {'size': 12, 'bold': True, 'color': AMBER})])
text(s, 8.05, 2.28, 4.6, 1.15,
     [('不是手写假数据，而是按仿真结果生成：连续越限时段合并成一张“越限工单”；'
       '未越限但到 70% 的站补一张“预警工单”；全场无压力时才出“演练工单”。',
       {'size': 10, 'color': INK2})])
text(s, 8.05, 3.55, 4.6, 0.3, [('状态是真写库的', {'size': 12, 'bold': True, 'color': AMBER})])
text(s, 8.05, 3.85, 4.6, 1.25,
     [('点“处理中 / 已闭环”→ PATCH /api/workorders/{id} → 更新 work_order、追加 workorder_event。'
       '刷新页面记录还在，这是“真写库”和“假状态”的区别。', {'size': 10, 'color': INK2})])
text(s, 8.05, 5.4, 4.6, 0.9,
     [('页面右上角写着当前是“接口数据”还是“演示数据”，不藏。', {'size': 10, 'color': MUTED})])
footer(s, 10)
note(s, '25 秒：异常页是唯一会写数据库的页面。工单是按规则从仿真结果生成的，不是写死的；'
        '状态流转会真的写回 MySQL 并追加一条事件，刷新还在。')

# ======================================================================
# 11 模型
# ======================================================================
s = prs.slides.add_slide(BLANK)
bg(s)
head(s, '10', '模型', '宏观递推 + 实体级仿真，用四条断言绑定')
rect(s, ML, 1.95, 6.55, 2.45, fill=CARD, line=LINE, radius=True)
text(s, ML + 0.28, 2.1, 6.0, 0.3, [('宏观层：30 分钟一桶，逐桶递推', {'size': 12, 'bold': True, 'color': INK})])
text(s, ML + 0.28, 2.48, 6.0, 1.8,
     [('S_t = min(Q_t + A_t, C_t)', {'size': 11, 'color': PINE}),
      ('Q_(t+1) = Q_t + A_t - S_t', {'size': 11, 'color': PINE}),
      ('P_t = min(D_t, I_t + S_t)', {'size': 11, 'color': PINE}),
      ('I_(t+1) = I_t + S_t - P_t', {'size': 11, 'color': PINE}),
      ('守恒：Q_(t+1) + I_(t+1) = Q_t + I_t + A_t - P_t', {'size': 10.5, 'color': MUTED})], line_spacing=1.05)

rect(s, 7.55, 1.95, 5.05, 2.45, fill=CARD, line=LINE, radius=True)
text(s, 7.83, 2.1, 4.5, 0.3, [('实体层：1 分钟粒度', {'size': 12, 'bold': True, 'color': INK})])
text(s, 7.83, 2.48, 4.55, 1.85,
     [('到车批次 → 卸货分拣 → 储位分配 → 取件码生成 → 取件排队 → 容量分级',
       {'size': 10.5, 'color': INK2}),
      ('随机数用 mulberry32，同一种子必得同一结果。', {'size': 10, 'color': MUTED})])

text(s, ML, 4.65, 5.0, 0.3, [('四条一致性断言', {'size': 12, 'bold': True, 'color': AMBER})])
tags = ['件数守恒', '峰值对齐 ±5%', '无负库存', '无超卖']
for i, t in enumerate(tags):
    x = ML + i * 1.62
    sp = rect(s, x, 5.0, 1.5, 0.42, fill=CREAM, line=None, radius=True)
    tf = sp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = t
    _set_font(r, 10, True, INK2)

text(s, ML, 5.75, 11.9, 0.9,
     [('标定原则：C、κ_q、κ_i 只在设计峰值场景标定一次，三个场景共用；场景要改，必须用显式倍率——',
       {'size': 11.5, 'color': INK2}),
      ('否则高峰场景会自动扩容，“高峰撑爆”的结论就不成立了。', {'size': 11.5, 'bold': True, 'color': INK})])
footer(s, 11)
note(s, '30 秒：模型有两层。宏观层是 30 分钟的库存递推，四个公式；微观层下沉到车、货架、储位。'
        '两层用四条断言绑住。这里有个坑我踩过：处理能力如果按每个场景自己的到件量倒推，高峰场景会自己扩容，'
        '风险就消失了。所以常量只在设计峰值标定一次。')

# ======================================================================
# 12 工程质量
# ======================================================================
s = prs.slides.add_slide(BLANK)
bg(s)
head(s, '11', '质量', '把一个课程作业当工程项目做')
stats = [
    ('20', 'REST 接口', '读多写一，错误码语义化', AMBER),
    ('15', '张表 · 2.89 万行', 'H2 与 MySQL 双形态', PINE),
    ('60', '条前端断言', '交互 31 / 键盘 9 / 校准 20', RGBColor(0x3C, 0x6E, 0x9F)),
    ('29', '条契约断言', '状态码、字段、类型、降级', RGBColor(0xA8, 0x4E, 0x6B)),
    ('3', '个后端单测', '手算 / 50 组随机守恒 / 单调性', RGBColor(0x6B, 0x6B, 0x5E)),
    ('0', '布局缺陷', '1280/1440/1920 三档 · 深浅双主题', PINE),
]
for i, (v, t, d, c) in enumerate(stats):
    x = ML + (i % 3) * 4.02
    y = 2.0 + (i // 3) * 1.95
    rect(s, x, y, 3.72, 1.68, fill=CARD, line=LINE, radius=True)
    text(s, x + 0.26, y + 0.14, 1.4, 0.66, [(v, {'size': 32, 'bold': True, 'color': c})])
    text(s, x + 1.35, y + 0.34, 2.2, 0.32, [(t, {'size': 12, 'bold': True, 'color': INK})])
    text(s, x + 0.26, y + 1.02, 3.2, 0.5, [(d, {'size': 9.5, 'color': INK2})])
text(s, ML, 6.0, 11.8, 0.55,
     [('“页面不能错位”被翻译成三条可执行断言：横向溢出 0、元素裁剪 0、元素重叠 0——红绿灯代替人眼。',
       {'size': 11.5, 'color': MUTED})])
footer(s, 12)
note(s, '20 秒：工程质量这块我不多说，就一组数：20 个接口、15 张表、60 条前端断言、29 条契约断言、3 个后端单测，'
        '三档屏宽零布局缺陷。验收标准是能跑的，不是形容词。')

# ======================================================================
# 13 收尾
# ======================================================================
s = prs.slides.add_slide(BLANK)
bg(s, INK)
rect(s, 0, 0, 0.22, H, fill=AMBER)
text(s, 1.0, 0.95, 8.0, 0.3, [('12  收尾', {'size': 10.5, 'bold': True, 'color': AMBER})])
text(s, 1.0, 1.35, 10.5, 0.8, [('做完了什么，还差什么', {'size': 34, 'bold': True, 'color': RGBColor(0xFF, 0xFF, 0xFF)})])

left = [
    ('已经做完', ['五页 + 地图 + 室内布局', '双库形态的后端与 20 个接口', '60 + 29 + 3 条可跑断言']),
    ('还没做', ['登录与权限（刻意收缩）', '真实 GPS 轨迹（现为插值）', '两层仿真的严格对齐']),
]
for i, (t, items) in enumerate(left):
    x = 1.0 + i * 5.0
    text(s, x, 2.55, 4.4, 0.3, [(t, {'size': 11, 'bold': True, 'color': AMBER})])
    text(s, x, 2.95, 4.4, 1.6, [('· ' + it, {'size': 13, 'color': RGBColor(0xE6, 0xE0, 0xD0)}) for it in items],
         line_spacing=1.5)

rect(s, 1.0, 4.95, 11.3, 0.012, fill=RGBColor(0x3A, 0x4A, 0x43))
text(s, 1.0, 5.15, 11.3, 0.5,
     [('一句话总结：在拿不到真实数据的条件下，仍然做出了一个每个数字都能回答来源的系统。',
       {'size': 15, 'bold': True, 'color': RGBColor(0xFF, 0xFF, 0xFF)})])
text(s, 1.0, 6.35, 6.0, 0.4, [('谢谢老师，请提问。', {'size': 13, 'color': CREAM})])
text(s, 7.0, 6.35, 5.3, 0.4, [('现场演示：http://localhost:5173', {'size': 11, 'color': RGBColor(0x9F, 0x94, 0x7E)})],
     align=PP_ALIGN.RIGHT)
note(s, '20 秒：最后一句总结。已经做完的、还没做的我都如实列了。'
        '如果老师允许，我可以现场打开系统走一遍。谢谢。')

prs.save(OUT)
print('saved:', OUT)
print('slides:', len(prs.slides.__iter__.__self__._sldIdLst))
