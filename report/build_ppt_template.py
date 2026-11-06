# -*- coding: utf-8 -*-
"""按学校课件模板（智慧能源概论_教师课件模板与框架素材库.pptx）重做答辩 PPT。

保留模板的版式语言：深蓝标题栏 002049、校徽、蓝色二级标题栏 006FB9、底部深蓝条、黑体加粗、红色 D90000 强调。
内容沿用上一版 13 页 + 目录页。
"""
import os
import copy

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = r'D:\java大作业'
FIGS = os.path.join(ROOT, 'report', 'assets', 'figs')
TPL = r'D:\能源概论ppt\output\智慧能源概论_教师课件模板与框架素材库.pptx'
ASSETS = os.path.join(ROOT, 'report', 'assets', 'tpl')
OUT = os.path.join(ROOT, 'report', '驿链CampusFlow_答辩PPT_5min.pptx')

# 模板取色
NAVY = RGBColor(0x00, 0x20, 0x49)
BLUE = RGBColor(0x00, 0x6F, 0xB9)
RED = RGBColor(0xD9, 0x00, 0x00)
INK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY = RGBColor(0x59, 0x59, 0x59)
LIGHT = RGBColor(0xEA, 0xF2, 0xFA)
BORDER = RGBColor(0xBF, 0xBF, 0xBF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = 'SimHei'

prs = Presentation(TPL)
SW, SH = prs.slide_width / 914400, prs.slide_height / 914400  # 13.333 x 7.5
BLANK = prs.slide_layouts[5]


# ---------------- 基础工具 ----------------
def _font(run, size, bold=True, color=INK, font=FONT, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font
    run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for tag in ('a:ea', 'a:cs'):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set('typeface', font)


def txt(slide, x, y, w, h, lines, size=16, bold=False, color=INK, align=PP_ALIGN.LEFT,
        anchor=MSO_ANCHOR.TOP, spacing=1.2, space_after=2, font=FONT):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    if isinstance(lines, str):
        lines = [lines]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(space_after)
        text, opt = (ln if isinstance(ln, tuple) else (ln, {}))
        r = p.add_run()
        r.text = text
        _font(r, opt.get('size', size), opt.get('bold', bold), opt.get('color', color), font)
    return box


def rect(slide, x, y, w, h, fill=None, line=None, lw=0.9, shape=None, radius=None):
    sp = slide.shapes.add_shape(shape or MSO_SHAPE.RECTANGLE,
                                Inches(x), Inches(y), Inches(w), Inches(h))
    if radius is not None:
        try:
            sp.adjustments[0] = radius
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
        sp.line.width = Pt(lw)
    sp.shadow.inherit = False
    tf = sp.text_frame
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    return sp


def pic(slide, path, x, y, w, h, contain=True, border=BORDER):
    iw, ih = Image.open(path).size
    if contain:
        s = min(w / iw, h / ih)
        pw, ph = iw * s, ih * s
        px, py = x + (w - pw) / 2, y + (h - ph) / 2
        p = slide.shapes.add_picture(path, Inches(px), Inches(py), Inches(pw), Inches(ph))
    else:
        p = slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
    if border is not None:
        p.line.color.rgb = border
        p.line.width = Pt(1)
    return p


def chrome(slide, title, subtitle):
    """深蓝一级标题栏 + 蓝色二级标题栏 + 校徽 + 底部条，完全复刻模板的几何。"""
    rect(slide, 0, 0, 13.333, 0.91, fill=NAVY)
    size = 30 if len(title) <= 18 else 26
    txt(slide, 0.56, 0.1, 10.4, 0.7, [(title, {'size': size})], bold=True, color=WHITE,
        anchor=MSO_ANCHOR.MIDDLE)
    slide.shapes.add_picture(os.path.join(ASSETS, 'logo.png'), Inches(11.17), Inches(0.09),
                             Inches(2.08), Inches(0.7))
    rect(slide, 0, 1.01, 11.98, 0.65, fill=BLUE)
    slide.shapes.add_picture(os.path.join(ASSETS, 'grad.png'), Inches(11.98), Inches(1.01),
                             Inches(1.35), Inches(0.65))
    txt(slide, 0.6, 1.06, 11.2, 0.55, [(subtitle, {'size': 22})], bold=True, color=WHITE,
        anchor=MSO_ANCHOR.MIDDLE)
    rect(slide, 0, 7.25, 13.333, 0.25, fill=NAVY)


def label(slide, text, y=1.82, x=0.55):
    rect(slide, x, y + 0.07, 0.2, 0.2, fill=RED)
    txt(slide, x + 0.34, y, 11.0, 0.42, [(text, {'size': 20})], bold=True, color=NAVY)


def new_slide(title, subtitle):
    s = prs.slides.add_slide(BLANK)
    chrome(s, title, subtitle)
    return s


def note(slide, text):
    slide.notes_slide.notes_text_frame.text = text


# ---------------- 1 封面：改模板封面 ----------------
cover = prs.slides[0]
# 删掉模板的标题字画（“智慧能源概论”那张图）与两行占位文字
for idx in sorted([0, 3, 4], reverse=True):
    sh = cover.shapes[idx]
    sh._element.getparent().remove(sh._element)
# 保留：细横线（原 shape 1）、底部校徽条（原 shape 2）

txt(cover, 0.9, 0.72, 11.6, 1.0, [('驿链 CampusFlow', {'size': 54})], bold=True,
    color=NAVY, align=PP_ALIGN.CENTER)
txt(cover, 0.9, 1.68, 11.6, 0.32,
    [('C A M P U S F L O W   ·   C A M P U S   L O G I S T I C S', {'size': 11})],
    bold=True, color=BLUE, align=PP_ALIGN.CENTER)

txt(cover, 0.8, 2.45, 11.8, 0.6,
    [('中国矿业大学南湖校区校园物流管理系统的设计与实现', {'size': 28})],
    bold=True, color=INK, align=PP_ALIGN.CENTER)
txt(cover, 0.8, 3.32, 11.8, 0.4,
    [('Java 语言及网络编程 · 课程结题报告', {'size': 18})],
    bold=False, color=GRAY, align=PP_ALIGN.CENTER)
txt(cover, 0.8, 4.18, 11.8, 0.4,
    [('答辩人：____________     学号：____________     指导教师：____________', {'size': 14})],
    bold=False, color=GRAY, align=PP_ALIGN.CENTER)
txt(cover, 0.8, 4.68, 11.8, 0.4, [('2026 年 11 月', {'size': 14})],
    bold=False, color=GRAY, align=PP_ALIGN.CENTER)
note(cover, '开场 10 秒：各位老师好，我是___，我做的是南湖校区的校园物流管理系统“驿链 CampusFlow”。'
            '今天用五分钟讲三件事：为什么做、怎么做、做成了什么。')

# ---------------- 2 目录：改模板目录 ----------------
toc = prs.slides[2]
items = [
    '第一部分      问题与数据约束',
    '第二部分      系统设计与实现',
    '第三部分      系统运行展示',
    '第四部分      测试验证与总结',
]
for i, shape_idx in enumerate((5, 6, 7, 8)):
    sh = toc.shapes[shape_idx]
    tf = sh.text_frame
    p = tf.paragraphs[0]
    runs = p.runs
    if runs:
        runs[0].text = items[i]
        for r in runs[1:]:
            r._r.getparent().remove(r._r)
note(toc, '5 秒过渡：我分四部分讲，重点是第二部分的“可信”和第三部分的“能用”。')

# 说明：模板里其余页在最后统一删除（先新增再删，避免 partname 冲突）

# ---------------- 3 问题 ----------------
s = new_slide('一、问题', '一个“数据拿不到”的系统')
label(s, '南湖校区：“一主三辅”的四站格局')
txt(s, 0.9, 2.28, 11.8, 1.0,
    [('桃苑物流服务中心是主站，松苑、梅苑、兰苑是三座无人快递超市，竹苑另设收发室。',
      {'size': 16}),
     ('决定体验的量——每天到多少件、几点到车、货架还剩多少、取件排多久——都在运营方手里。',
      {'size': 16})], bold=False, color=INK, spacing=1.35)

cards = [
    ('数据约束', '运营数据一条也拿不到', '既不能编，也不能装作有'),
    ('时间约束', '只有一个课程周期', '必须先做完，再做深'),
    ('解释约束', '评委不是运营专家', '每个数字都要能回答来源'),
]
for i, (t, l1, l2) in enumerate(cards):
    x = 0.55 + i * 4.15
    rect(s, x, 3.45, 3.9, 1.95, fill=LIGHT, line=BLUE, lw=0.75)
    rect(s, x, 3.45, 3.9, 0.07, fill=NAVY)
    txt(s, x + 0.28, 3.66, 3.3, 0.36, [(t, {'size': 19})], bold=True, color=NAVY)
    txt(s, x + 0.28, 4.1, 3.3, 0.4, [(l1, {'size': 13.5})], bold=False, color=INK)
    txt(s, x + 0.28, 4.52, 3.3, 0.4, [(l2, {'size': 13.5})], bold=False, color=GRAY)

txt(s, 0.55, 5.78, 12.2, 0.9,
    [('问题因此被重新定义：不是做一个好看的看板，', {'size': 19, 'color': NAVY}),
     ('而是做一个每个数字都能回答来源的系统。', {'size': 19, 'color': RED})],
    bold=True, spacing=1.3)
note(s, '25 秒：这个项目最大的难点不是写代码，是数据。校园快递的真实运营数据学生拿不到。'
        '所以我没有编数据，而是把“数据不可得”当成设计前提。')

# ---------------- 4 方法 ----------------
s = new_slide('二、方法', '把“不可知”变成“可替换”')
label(s, '31 项参数，每一项都带 source / range / rationale / swap_hint')
cols = [
    ('10', '项', '实测 measured', '实景照片读数、本机脚本测量', '例：货架 240 架、通道 0.8 m'),
    ('1', '项', '公开 public', '学生手册、总务部报道、商品规格', '例：取件码规则、营业时间'),
    ('20', '项', '假设 assumed', '带区间与理由的运营假设', '例：日到件 ∈ [11,000, 16,000]'),
]
for i, (num, unit, name, d1, d2) in enumerate(cols):
    x = 0.55 + i * 4.15
    rect(s, x, 2.35, 3.9, 2.15, fill=None, line=BORDER, lw=0.75)
    txt(s, x + 0.25, 2.45, 3.4, 0.8, [(f'{num} 项', {'size': 36})], bold=True,
        color=(NAVY if i < 2 else RED))
    txt(s, x + 0.25, 3.22, 3.4, 0.3, [(name, {'size': 15})], bold=True,
        color=(NAVY if i < 2 else RED))
    txt(s, x + 0.25, 3.55, 3.45, 0.75, [(d1, {'size': 11.5}), (d2, {'size': 11.5})],
        bold=False, color=GRAY, spacing=1.2)

rules = [
    ('01', '数值可溯源', '实测 / 公开 / 假设，三档标签页面可查'),
    ('02', '假设有区间', '每项假设给上下界与理由，脚本自动校验'),
    ('03', '结论用相对量', '“占用 92.9%”而不是“剩 3080 件”，参数扰动下结论不反转'),
]
for i, (n, t, d) in enumerate(rules):
    y = 4.85 + i * 0.62
    txt(s, 0.55, y, 0.5, 0.3, [(n, {'size': 15})], bold=True, color=RED)
    txt(s, 1.15, y, 1.9, 0.3, [(t, {'size': 15})], bold=True, color=NAVY)
    txt(s, 3.05, y + 0.02, 9.6, 0.3, [(d, {'size': 13})], bold=False, color=INK)
note(s, '30 秒：方法是三档可信度。10 项实测、1 项公开、20 项带区间的假设。'
        '页面每个数字都带标签，结论一律用相对量，参数怎么变，结论方向都不变。')

# ---------------- 5 架构 ----------------
s = new_slide('三、系统设计', '五层结构，一条参数主线')
label(s, '总体架构')
pic(s, os.path.join(FIGS, 'fig-architecture-wide.png'), 0.55, 2.3, 12.2, 4.78)
note(s, '25 秒：技术上是标准的前后端分离，Vue 3 加 Spring Boot。我特意保留双数据库：'
        'H2 让老师克隆下来就能跑，MySQL 形态才开五个增强接口。')

# ---------------- 6 功能地图 ----------------
s = new_slide('四、功能', '五页一图：从“看到”到“处置”')
label(s, '五个页面，五类任务：巡检、查档、预案、处置、溯源')
items = [
    ('P1', '运营总览', '六项 KPI、四站状态、取件码查询、流量曲线、本周推演'),
    ('P2', '站点与服务', '站点档案、30 分钟运行表、室内平面图逐排逐格'),
    ('P3', '高峰与方案', '双库存堆叠、需求与能力、方案对比、风险时段清单'),
    ('P4', '异常协同', '自动建单、状态写回数据库、事件时间线'),
    ('P5', '资料与说明', '三档标签、公开来源清单、模型假设、不做清单'),
]
routes = ['/overview', '/sites', '/peak', '/incidents', '/about']
for i, (code, name, desc) in enumerate(items):
    x = 0.55 + (i % 3) * 4.15
    y = 2.42 + (i // 3) * 1.95
    rect(s, x, y, 3.9, 1.72, fill=None, line=BORDER, lw=0.75)
    txt(s, x + 0.22, y + 0.14, 0.9, 0.4, [(code, {'size': 22})], bold=True, color=BLUE)
    txt(s, x + 1.05, y + 0.18, 2.6, 0.35, [(name, {'size': 16})], bold=True, color=NAVY)
    txt(s, x + 0.22, y + 0.68, 3.5, 0.75, [(desc, {'size': 11.5})], bold=False, color=GRAY,
        spacing=1.3)
    txt(s, x + 0.22, y + 1.43, 3.4, 0.22, [(routes[i], {'size': 9})], bold=False, color=BORDER)

rect(s, 8.85, 2.42 + 1.95, 3.9, 1.75, fill=LIGHT, line=BLUE, lw=0.75)
txt(s, 9.07, 4.5, 3.5, 0.4, [('地图是第六个“页面”', {'size': 16})], bold=True, color=RED)
txt(s, 9.07, 4.95, 3.5, 0.9,
    [('双底图、四站四入口、在途车辆与批次、人工校准，都收在一次“放大”里。', {'size': 11.5})],
    bold=False, color=INK, spacing=1.3)
txt(s, 0.55, 6.5, 12.2, 0.35,
    [('一套数据、五个视角：任何一页都能回答“这个数哪来的”。', {'size': 13})],
    bold=False, color=GRAY)
note(s, '20 秒：五个页面不是功能堆叠，而是五类任务。第六个“页面”是地图的放大态。')

# ---------------- 7 地图 ----------------
s = new_slide('五、空间', '地图不是背景，是工作台')
label(s, '双底图 · 四站四入口 · 在途车辆')
pic(s, os.path.join(FIGS, 'fig-map-expand.png'), 0.5, 2.3, 7.95, 4.75)
txt(s, 8.72, 2.35, 4.1, 0.3, [('三件事在地图上发生', {'size': 14})], bold=True, color=RED)
txt(s, 8.72, 2.72, 4.05, 1.5,
    [('· 四站与四个入口的相对位置', {'size': 11.5}),
     ('· 配送路径与在途车辆（13:10，本批 244 件、4 车）', {'size': 11.5}),
     ('· 手工校准：拖图 → 反算经纬度 → 持久化', {'size': 11.5})],
    bold=False, color=INK, spacing=1.45)
txt(s, 8.72, 4.35, 4.1, 0.3, [('诚实边界', {'size': 14})], bold=True, color=RED)
txt(s, 8.72, 4.72, 4.05, 1.2,
    [('坐标是相对方位推定，不是测绘成果；车辆位置是线性插值，不是真实 GPS。页面上都标了。',
      {'size': 11.5})], bold=False, color=INK, spacing=1.35)
txt(s, 8.72, 6.15, 4.05, 0.9,
    [('774 张瓦片离线缓存，断网也能演示。', {'size': 11.5})], bold=True, color=NAVY)
note(s, '25 秒：地图不是画点，是把配送路径、在途车辆、批次时间都放进来了。'
        '自动配准试了四种都不收敛，最后做人工校准工具——这个失败也写进报告了。')

# ---------------- 8 P1 ----------------
s = new_slide('六、运行 · P1', '运营总览：一屏看清四个站')
label(s, '六项 KPI + 地图 + 取件码查询 + 流量曲线')
pic(s, os.path.join(FIGS, 'fig-p1-top.png'), 0.5, 2.3, 8.35, 4.75)
stats = [
    ('17,050', '件', '当日到件', NAVY),
    ('92.9', '%', '最高占用率（松苑）', RED),
    ('166.7', '分钟', '最长高峰排队', RED),
    ('0', '件', '未满足取件', NAVY),
]
for i, (v, u, lab, c) in enumerate(stats):
    y = 2.35 + i * 1.16
    txt(s, 9.1, y, 3.4, 0.55, [(v, {'size': 30})], bold=True, color=c)
    txt(s, 9.1, y + 0.52, 3.4, 0.3, [(u + '   ' + lab, {'size': 11.5})], bold=False, color=GRAY)
    if i < 3:
        rect(s, 9.1, y + 0.95, 3.55, 0.01, fill=BORDER)
note(s, '25 秒：总览一屏六个数。除了到件、取件，我加了两个自定义指标：通道可通行率、高峰排队。'
        '运营的人不关心库存多少件，他关心通道还走不走得动、队排多长。')

# ---------------- 9 P2 ----------------
s = new_slide('七、运行 · P2', '站点与服务：从站点到储位')
label(s, '站点档案 · 30 分钟运行表 · 室内平面图')
pic(s, os.path.join(FIGS, 'fig-p2-top.png'), 0.5, 2.3, 7.15, 4.47)
pic(s, os.path.join(FIGS, 'fig-plan.png'), 7.9, 2.28, 2.85, 3.0)
txt(s, 10.95, 2.32, 1.9, 1.9,
    [('240 架', {'size': 17, 'color': NAVY}),
     ('× 5 层', {'size': 17, 'color': NAVY}),
     ('× 20 位', {'size': 17, 'color': NAVY}),
     ('= 24,000 储位', {'size': 11, 'color': RED})], bold=True, spacing=1.45)
txt(s, 7.9, 5.42, 4.85, 0.9,
    [('平面按实景照片参数生成；点“排”展开储位，点格子看取件码与承运商。', {'size': 11.5})],
    bold=False, color=INK, spacing=1.3)
txt(s, 0.5, 6.85, 7.0, 0.28, [('越限行整行标红。', {'size': 10})], bold=False, color=GRAY)
note(s, '25 秒：站点页两个层次：档案和现场。运行表精确到 30 分钟，越限整行标红；'
        '室内平面图能钻到储位，24,000 个储位和宏观模型的待取上限是同一套数。')

# ---------------- 10 P3 ----------------
s = new_slide('八、运行 · P3', '高峰与方案：双 11 第 7 天会怎样')
label(s, 'S1 常态 → S2 双 11 第 7 天 → S3 分流增能')
pic(s, os.path.join(FIGS, 'fig-p3.png'), 0.5, 2.3, 7.8, 4.87)
stats = [
    ('83.4%', '桃苑占用 · 预警', RED),
    ('52', '四站风险时段', RED),
    ('88.2', '桃苑高峰排队（分钟）', NAVY),
    ('38.8', '分流增能后（分钟）', BLUE),
]
for i, (v, lab, c) in enumerate(stats):
    x = 8.55 + (i % 2) * 2.15
    y = 2.3 + (i // 2) * 1.55
    rect(s, x, y, 2.0, 1.35, fill=None, line=BORDER, lw=0.75)
    txt(s, x + 0.16, y + 0.12, 1.7, 0.5, [(v, {'size': 24})], bold=True, color=c)
    txt(s, x + 0.16, y + 0.72, 1.75, 0.55, [(lab, {'size': 10.5})], bold=False, color=GRAY,
        spacing=1.15)
txt(s, 8.55, 5.45, 4.25, 1.5,
    [('S3 排队 88.2 → 38.8 分钟（−56%），无人站占用只降 0.7 个百分点。', {'size': 12}),
     ('瓶颈在取件侧，不在到件侧。', {'size': 12, 'color': RED})],
    bold=True, color=INK, spacing=1.35)
note(s, '30 秒：这是全系统的核心结论。双 11 第 7 天桃苑 83.4% 预警，三个无人站 89–93% 限流。'
        '分流增能后排队从 88 压到 39 分钟，但无人站占用几乎没降——瓶颈在取件侧。')

# ---------------- 11 P4 ----------------
s = new_slide('九、运行 · P4', '异常协同：工单不是写死的')
label(s, '自动建单 · 状态写回 MySQL · 事件时间线')
pic(s, os.path.join(FIGS, 'fig-p4-ppt.png'), 0.5, 2.3, 8.0, 4.55)
txt(s, 8.75, 2.35, 4.05, 0.3, [('工单从哪来', {'size': 14})], bold=True, color=RED)
txt(s, 8.75, 2.72, 4.0, 1.35,
    [('按仿真结果生成：连续越限合并成“越限工单”；未越限但到 70% 的站补“预警工单”；'
      '全场无压力才出“演练工单”。', {'size': 11.5})], bold=False, color=INK, spacing=1.35)
txt(s, 8.75, 4.1, 4.05, 0.3, [('状态是真写库的', {'size': 14})], bold=True, color=RED)
txt(s, 8.75, 4.47, 4.0, 1.35,
    [('点“处理中 / 已闭环”→ PATCH /api/workorders/{id} → 更新工单、追加事件。'
      '刷新记录还在，这是“真写库”和“假状态”的区别。', {'size': 11.5})],
    bold=False, color=INK, spacing=1.35)
note(s, '25 秒：异常页是唯一写数据库的页面。工单按规则生成，状态流转真的写回 MySQL 并追加事件。')

# ---------------- 12 模型 ----------------
s = new_slide('十、模型', '宏观递推 + 实体级仿真，用四条断言绑定')
label(s, '两层模型')
rect(s, 0.55, 2.3, 7.3, 2.0, fill=LIGHT, line=BLUE, lw=0.75)
txt(s, 0.8, 2.42, 6.8, 0.3, [('宏观层：30 分钟一桶，逐桶递推', {'size': 13})], bold=True, color=NAVY)
txt(s, 0.8, 2.82, 6.9, 1.7,
    [('S_t = min(Q_t + A_t, C_t)', {'size': 12}),
     ('Q_t+1 = Q_t + A_t − S_t', {'size': 12}),
     ('P_t = min(D_t, I_t + S_t)', {'size': 12}),
     ('I_t+1 = I_t + S_t − P_t', {'size': 12}),
     ('守恒：Q_t+1 + I_t+1 = Q_t + I_t + A_t − P_t', {'size': 11, 'color': GRAY})],
    bold=False, color=NAVY, spacing=1.12, font='Consolas')

rect(s, 8.15, 2.3, 4.65, 2.0, fill=None, line=BORDER, lw=0.75)
txt(s, 8.4, 2.42, 4.2, 0.3, [('实体层：1 分钟粒度', {'size': 13})], bold=True, color=NAVY)
txt(s, 8.4, 2.82, 4.2, 1.6,
    [('到车批次 → 卸货分拣 → 储位分配 → 取件码生成 → 取件排队 → 容量分级',
      {'size': 11.5}),
     ('随机数用 mulberry32，同一种子必得同一结果。', {'size': 10.5, 'color': GRAY})],
    bold=False, color=INK, spacing=1.4)

txt(s, 0.55, 4.55, 3.0, 0.3, [('四条一致性断言', {'size': 14})], bold=True, color=RED)
tags = ['件数守恒', '峰值对齐 ±5%', '无负库存', '无超卖']
for i, t in enumerate(tags):
    x = 0.55 + i * 2.95
    rect(s, x, 4.92, 2.65, 0.5, fill=NAVY)
    txt(s, x, 5.0, 2.65, 0.35, [(t, {'size': 13})], bold=True, color=WHITE,
        align=PP_ALIGN.CENTER)
txt(s, 0.55, 5.65, 12.2, 0.8,
    [('标定原则：C、κ_q、κ_i 只在设计峰值场景标定一次，三个场景共用；场景要改，必须用显式倍率——',
      {'size': 12}),
     ('否则高峰场景会自动扩容，“高峰撑爆”的结论就不成立了。', {'size': 12, 'color': RED})],
    bold=True, color=INK, spacing=1.35)
note(s, '30 秒：宏观层 30 分钟递推，微观层下沉到车、货架、储位，四条断言绑定。'
        '这里踩过坑：处理能力按各场景倒推会自己扩容，所以常量只标定一次。')

# ---------------- 13 工程质量 ----------------
s = new_slide('十一、质量', '把一个课程作业当工程项目做')
label(s, '可执行的验收标准，而不是形容词')
stats = [
    ('20', '个 REST 接口', '读多写一，错误码语义化'),
    ('15', '张表 · 2.89 万行', 'H2 与 MySQL 双形态'),
    ('60', '条前端断言', '交互 31 / 键盘 9 / 校准 20'),
    ('29', '条契约断言', '状态码、字段、类型、降级'),
    ('3', '个后端单测', '手算 / 50 组随机守恒 / 单调性'),
    ('0', '布局缺陷', '三档屏宽 · 深浅双主题'),
]
for i, (v, t, d) in enumerate(stats):
    x = 0.55 + (i % 3) * 4.15
    y = 2.35 + (i // 3) * 1.95
    rect(s, x, y, 3.9, 1.72, fill=None, line=BORDER, lw=0.75)
    rect(s, x, y, 0.07, 1.72, fill=(RED if v in ('0', '3') else NAVY))
    txt(s, x + 0.25, y + 0.14, 1.3, 0.6, [(v, {'size': 34})], bold=True, color=NAVY)
    txt(s, x + 1.3, y + 0.3, 2.4, 0.35, [(t, {'size': 13})], bold=True, color=INK)
    txt(s, x + 0.25, y + 1.05, 3.4, 0.5, [(d, {'size': 10.5})], bold=False, color=GRAY)
txt(s, 0.55, 6.35, 12.2, 0.5,
    [('“页面不能错位”被翻译成三条可执行断言：横向溢出 0、裁剪 0、重叠 0——红绿灯代替人眼。',
      {'size': 12.5})], bold=False, color=GRAY)
note(s, '20 秒：工程质量就一组数：20 个接口、15 张表、60 条前端断言、29 条契约断言、3 个后端单测，'
        '三档屏宽零布局缺陷。')

# ---------------- 14 收尾 ----------------
s = new_slide('十二、收尾', '做完了什么，还差什么')
txt(s, 0.55, 2.3, 5.9, 0.35, [('已经做完', {'size': 16})], bold=True, color=NAVY)
txt(s, 0.55, 2.75, 5.9, 1.9,
    [('· 五页 + 地图 + 室内布局', {'size': 13}),
     ('· 双库形态的后端与 20 个接口', {'size': 13}),
     ('· 60 + 29 + 3 条可跑断言', {'size': 13})], bold=False, color=INK, spacing=1.7)
txt(s, 6.85, 2.3, 5.9, 0.35, [('还没做（如实列出）', {'size': 16})], bold=True, color=RED)
txt(s, 6.85, 2.75, 5.9, 1.9,
    [('· 登录与权限（刻意收缩）', {'size': 13}),
     ('· 真实 GPS 轨迹（现为插值）', {'size': 13}),
     ('· 两层仿真的严格对齐', {'size': 13})], bold=False, color=INK, spacing=1.7)
rect(s, 0.55, 4.85, 12.2, 0.02, fill=BORDER)
txt(s, 0.55, 5.05, 12.2, 0.85,
    [('在拿不到真实数据的条件下，仍然做出了一个', {'size': 18, 'color': NAVY}),
     ('每个数字都能回答来源的系统。', {'size': 18, 'color': RED})],
    bold=True, spacing=1.35)
txt(s, 0.55, 6.2, 6.0, 0.4, [('谢谢老师，请提问。', {'size': 15})], bold=True, color=NAVY)
txt(s, 6.85, 6.2, 5.9, 0.4, [('现场演示：http://127.0.0.1:5173', {'size': 11})],
    bold=False, color=GRAY, align=PP_ALIGN.RIGHT)
note(s, '20 秒：做完的、没做的都如实列了。一句话总结，谢谢老师。')

# ---------------- 最后：删掉模板里没用到的页 ----------------
sldIdLst = prs.slides._sldIdLst
ids = list(sldIdLst)
new_count = 12                     # 3—14 页是新建的
keep_front = 2                     # 封面 + 目录
for i in range(len(ids) - 1, -1, -1):
    if i >= len(ids) - new_count:      # 新建的 12 页保留
        continue
    if i in (0, 2):                    # 封面 + 目录保留
        continue
    prs.part.drop_rel(ids[i].rId)
    sldIdLst.remove(ids[i])

prs.save(OUT)
print('saved:', OUT, 'slides:', len(prs.slides))
