# -*- coding: utf-8 -*-
"""生成《Java语言及网络编程》课程报告初版（按课程附件模板）。"""
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = r'D:\java大作业'
OUTDIR = os.path.join(ROOT, 'report')
os.makedirs(OUTDIR, exist_ok=True)
OUT = os.path.join(OUTDIR, 'Java语言及网络编程_课程报告_初版.docx')

doc = Document()

sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(2.54)
sec.bottom_margin = Cm(2.54)
sec.left_margin = Cm(3.0)
sec.right_margin = Cm(2.6)


def set_font(run, name='宋体', size=12, bold=False, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)


normal = doc.styles['Normal']
normal.font.name = '宋体'
normal.font.size = Pt(12)
normal.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_before = Pt(0)
normal.paragraph_format.space_after = Pt(0)


def para(text='', size=12, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=2,
         font='宋体', space_before=0, space_after=0, line=1.5):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing = line
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    if indent:
        pf.first_line_indent = Pt(size * indent)
    if text:
        r = p.add_run(text)
        set_font(r, font, size, bold)
    return p


def h1(text):
    p = doc.add_paragraph(style='Heading 1')
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run(text)
    set_font(r, '黑体', 15, False, color=(0, 0, 0))
    return p


def h2(text):
    p = doc.add_paragraph(style='Heading 2')
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run(text)
    set_font(r, '黑体', 12.5, False, color=(0, 0, 0))
    return p


def h3(text):
    p = doc.add_paragraph(style='Heading 3')
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run(text)
    set_font(r, '宋体', 12, True, color=(0, 0, 0))
    return p


def bullet(text, size=12):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Pt(size * 2)
    p.paragraph_format.first_line_indent = Pt(-size)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run('· ' + text)
    set_font(r, '宋体', size)
    return p


def code_block(lines, size=9.5):
    for ln in lines:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Pt(24)
        p.paragraph_format.line_spacing = 1.25
        r = p.add_run(ln)
        set_font(r, 'Consolas', size)


def caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(text)
    set_font(r, '宋体', 10.5)


def table(headers, rows, widths=None, size=10.5):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ''
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        set_font(r, '宋体', size, True)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ''
            p = cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(str(val))
            set_font(r, '宋体', size)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    return t


def add_toc():
    p = doc.add_paragraph()
    run = p.add_run()
    b = OxmlElement('w:fldChar')
    b.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = r'TOC \o "1-3" \h \z \u'
    sep = OxmlElement('w:fldChar')
    sep.set(qn('w:fldCharType'), 'separate')
    t = OxmlElement('w:t')
    t.text = '（自动目录：在 Word 中右键选择“更新域”即可生成）'
    e = OxmlElement('w:fldChar')
    e.set(qn('w:fldCharType'), 'end')
    for el in (b, instr, sep, t, e):
        run._r.append(el)
    set_font(run, '宋体', 10.5)


def page_number_footer():
    footer = doc.sections[0].footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fld = OxmlElement('w:fldSimple')
    fld.set(qn('w:instr'), 'PAGE')
    r = OxmlElement('w:r')
    t = OxmlElement('w:t')
    t.text = '1'
    r.append(t)
    fld.append(r)
    p._p.append(fld)


# ============================ 封面 ============================
for _ in range(3):
    para('', indent=0)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('中国矿业大学计算机学院')
set_font(r, '黑体', 22)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(6)
r = p.add_run('20    级本科生课程报告')
set_font(r, '黑体', 18)

for _ in range(3):
    para('', indent=0)

cover_rows = [
    ('课程名称', 'Java 语言及网络编程'),
    ('学生姓名', '____________'),
    ('学    号', '____________'),
    ('专    业', '____________'),
    ('任课教师', '____________'),
]
t = doc.add_table(rows=0, cols=2)
t.alignment = WD_TABLE_ALIGNMENT.CENTER
for k, val in cover_rows:
    cells = t.add_row().cells
    cells[0].width = Cm(4.5)
    cells[1].width = Cm(8.0)
    p0 = cells[0].paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r0 = p0.add_run(k)
    set_font(r0, '黑体', 14)
    p1 = cells[1].paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r1 = p1.add_run(val)
    set_font(r1, '宋体', 14)

for _ in range(2):
    para('', indent=0)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('二〇二六年十一月')
set_font(r, '宋体', 14)

doc.add_page_break()

# ============================ 目录 ============================
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('目    录')
set_font(r, '黑体', 16)
para('', indent=0)
add_toc()

doc.add_page_break()

# ============================ 正文 ============================
para('驿链（CampusFlow）：中国矿业大学南湖校区校园物流管理系统的设计与实现',
     size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, font='黑体', space_after=6)
para('——基于 AI 大模型工程化编程（SDD）的前后端分离实践',
     size=12, align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, space_after=16)

h1('摘    要')
para('本文设计并实现了一个面向中国矿业大学南湖校区的校园物流管理系统“驿链（CampusFlow）”。'
     '系统以“一主三辅四站”的真实服务格局为对象，前端采用 Vue 3 + TypeScript + Vite，'
     '后端采用 Spring Boot 3.2.3 + H2/MySQL，实现站点管理、容量仿真、高峰方案对比与异常协同四类能力。')
para('针对校园快递运营数据无法获取这一根本约束，本文没有虚构运营数据，而是提出并实现了一套'
     '“三档数据可信度 + 参数化”的方法：把不可获得的运营参数全部抽成带区间与出处的可替换参数，'
     '模型只对参数的变化规律负责；所有展示数据在页面上按“实测/公开/假设”三档标注，'
     '结论以相对量表述（如“待取区占用达到设计容量的 130%”），从而在参数误差 ±40% 的情况下仍保持结论稳定。')
para('在此基础上，系统从 30 分钟粒度的聚合流量模型下沉到逐车次、逐货架、逐储位的实体级仿真，'
     '设计并实现到车批次生成、储位分配、取件码生成、取件排队、容量分级阈值与院内路径规划等核心算法，'
     '并给出件数守恒、峰值对齐、无负库存、无超卖四条可自动断言的一致性校验。')
para('在数据侧，用户提供的 4 张桃苑主站内部实景照片进一步把 8 项参数由“假设”提升为“实测”：'
     '从照片中读出了货架编号体系（照片读到 25—155，用户补充至少 220 架）、层标与取件码规则（货架号-层号-四位序号）、'
     '通道宽度（约 1.3 m）与分区结构，使“物理储位 10,560、待取上限 2,372（22.5%）”这一关系可被核验。')
para('工程上，本项目按课程说明中的“AI 大模型工程化编程”路线组织开发过程：先把需求写成可验收的规格'
     '（4 套共 60 条自动化断言），再由大模型生成代码，高风险动作（删除地图图层、重排站点坐标、'
     '确定旺季放大倍数）由人工审批后落地。最终前端 28 个源文件 3,591 行，交互断言 31/31、'
     '键盘可达性 9/9、地图校准 20/20 全部通过，三档屏幕宽度下无裁剪、无重叠。')
para('关键词：校园物流；离散事件仿真；数据可信度；AI 工程化编程；Vue 3；Spring Boot', indent=0)

h1('1  引言')

h2('1.1  选题背景')
para('中国矿业大学南湖校区在校生规模超过两万人，日常快递主要通过“一主三辅”四个站点周转：'
     '桃苑物流服务中心为主站，设人工服务台与顺丰、京东品牌服务区；松苑、梅苑、兰苑为无人快递超市，'
     '面向中小件自助领取；竹苑另设收发室作为补充邮政服务点。这套格局由公开的学生手册与总务部报道可以确认。')
para('四个站点的空间位置、营业时间与服务分工是公开的，但真正决定运营质量的量——'
     '每日到件量、各承运商份额、逐时段到车节奏、货架储位占用、取件延迟分布——属于运营方内部数据，'
     '学生无从获取。这构成了本课题最本质的约束：想做的是一个“运营仿真系统”，却拿不到被仿真对象的真实数据。')

h2('1.2  问题定义与主要工作')
para('本文把问题拆成三个层次：')
bullet('表达层：如何用一套界面把“四个站点此刻什么状态、高峰会怎样、出问题怎么办”讲清楚；')
bullet('模型层：如何在只有公开资料与有限假设的条件下，构建一个内部自洽、可被真实数据替换的仿真模型；')
bullet('工程层：如何在有限时间内，以可验收的规格驱动大模型完成前端、仿真内核与后端的实现。')
para('本文的主要工作与贡献为：')
bullet('提出“三档数据可信度 + 参数区间 + 相对量结论”的数据方法论，并落地为参数注册表与页面标签体系；')
bullet('构建宏观（30 分钟聚合）与微观（逐车次、逐储位）双层仿真模型，并用四条一致性断言把两层绑定；')
bullet('实现双底图地图与人工校准工具，解决“截图无法自动配准到经纬度”的实际问题；')
bullet('以 AI 工程化路线完成开发，并把 60 条自动化断言作为“规格即验收”的证据。')

h1('2  开发环境')

h2('2.1  硬件与操作系统')
table(['项目', '配置'],
      [['操作系统', 'Windows 11（x64）'],
       ['处理器 / 内存', 'x64 多核；内存 16 GB 及以上'],
       ['磁盘', 'D 盘剩余 300 GB 以上（工程、数据与截图产物）'],
       ['显示', '1440×900 及以上；验收按 1280/1440/1920 三档宽度']],
      widths=[4.5, 9.5])
caption('表 2-1  硬件与操作系统环境')

h2('2.2  软件工具链')
para('下表版本均在本机执行命令核验（java -version、mvn -v、node -v 等），非照抄文档。')
table(['类别', '软件', '版本', '用途'],
      [['语言', 'JDK', '21.0.12', '后端编译与运行'],
       ['构建', 'Maven', '3.9.16', '后端依赖与打包'],
       ['语言', 'Node.js / npm', '24.21.0 / 11.19.0', '前端构建与脚本'],
       ['语言', 'Python', '3.11.9', '数据生成、配准与校验脚本'],
       ['前端框架', 'Vue', '3.5.13', '组件与响应式'],
       ['路由 / 状态', 'vue-router / pinia', '4.5 / 2.3.0', '页面路由与全局状态'],
       ['图表', 'echarts', '5.5.1（按需引入）', '曲线、堆叠柱、对比图'],
       ['地图', 'leaflet', '1.9.4', '双底图与点位'],
       ['动效', 'gsap', '3.12.5', '进场与数字滚动'],
       ['构建', 'vite / vue-tsc', '6.4.5 / 2.2', '开发服务器与类型检查'],
       ['后端', 'Spring Boot', '3.2.3', 'Web / JPA / JDBC / WebSocket'],
       ['数据库', 'H2 / MySQL', '2.2.224 / 8.3.0', '开发内嵌库 / 可选生产库'],
       ['测试', 'JUnit', '5.10.2', '后端单元测试'],
       ['版本控制', 'Git', '2.55.0', '提交与回溯']],
      widths=[2.6, 4.4, 4.4, 5.0], size=10)
caption('表 2-2  软件工具链与版本（本机实测）')

h2('2.3  AI 工程化开发环境')
para('本项目按课程说明中的“AI 大模型工程化编程”路线实施，开发环境除常规工具链外还包括：')
bullet('大模型与 Agent：DeepSeek 系列模型，通过命令行 Agent（DeepSeek Harness）以“工具调用 + 代码执行”的方式工作；'
       '模型负责读规格、生成代码、跑测试、读回结果，人负责定义边界与审批。')
bullet('规约文件（skill）：项目根目录的《总体开发计划与实施路线》与《数据可信度与实体级仿真方案》，'
       '以及 data/params/param_registry.json 参数表。它们不是写给人看的说明书，而是模型每一步都要读回的约束。')
bullet('可验收规格：frontend/scripts/ 下四套无头浏览器断言脚本（interact 31 条、keyboard 9 条、'
       'calibrate 20 条、audit 布局与对比度审计），共 60 条，构成“规格即测试”的落地形式。')
bullet('仓库：工程已本地 Git 化（3 次提交、129 个受管文件）；课程建议的国际发布地址为 GitHub / GitLab，'
       '国内为 Gitee / GitCode，本报告初版尚未推送，提交前将附仓库地址。')

h1('3  软件开发流程')

h2('3.1  AI 工程化路径的六步')
para('课程说明指出，AI 工程化实践的侧重点是“规约表达（SDD）与验证设计”：'
     '先根据需求分析做意图表达与需求分解，把要做什么写成可验收的规格（测试与评测集），形成 skill，'
     '再输入大模型产生代码；高风险动作要人工审批，不正确则回到需求重新定义边界。'
     '本项目严格按这六步推进，对应关系见表 3-1。')
table(['步骤', '课程要求', '本项目做法', '产物'],
      [['1', '意图表达与需求分解', '先写计划书：页面清单、每个板块的数据来源、验收标准', '计划书 v1.3—v1.5'],
       ['2', '形成规格约束', '把“什么样算做完”写成可执行断言，而非形容词', '60 条断言脚本'],
       ['3', '形成 skill', '把数据契约、参数表、算法规则写成模型必读的 markdown / JSON', '参数注册表、v1.4 方案'],
       ['4', '输入大模型产生代码', '按模块下发任务，模型读规格后生成并自测', '28 个前端源文件'],
       ['5', '高风险动作人工审批', '删图层、重排站点坐标、定旺季倍数均需用户拍板', 'USER-009—016'],
       ['6', '验证设计', '跑断言、读截图、量化审计，不通过则回到步骤 1 改规格', '审计报告与截图']],
      widths=[1.2, 3.8, 7.0, 3.8], size=10)
caption('表 3-1  AI 工程化六步与本项目的对应关系')

h2('3.2  意图表达：先写“不做什么”')
para('需求分解阶段最有价值的产出不是功能列表，而是边界。计划书里明确列出了不做的事：'
     '不做登录与权限、不做真实运单与扫码支付、不做三维地球与路径导航、不虚构没有公开证据的站点、'
     '不把近似经纬度当实测坐标、不做寒暑假与节假日场景。'
     '这些“不做”在后续每一次模型生成中都作为硬约束出现，避免了范围蔓延。')

h2('3.3  可验收规格：把“好看”翻译成可执行断言')
para('“页面不能错位”是无法验收的表述。本项目把它翻译成三条可执行断言：横向溢出为 0、'
     '元素裁剪数为 0、元素重叠数为 0，由 audit 脚本在三档宽度与深浅两套主题下逐页测量。'
     '类似的翻译还有：把“能切换场景”翻译成“切换后 KPI 文本必须变化且图表 canvas 像素签名必须变化”；'
     '把“键盘可用”翻译成“首个 Tab 落在跳过链接上、焦点环宽度大于 0、五个导航项均可到达、Esc 可关闭抽屉”。')
para('这套规格在开发中反复体现价值：模型生成的代码“看起来对”但实际不满足断言的情况出现过多次，'
     '每次都是断言先失败、再定位问题，而不是靠人眼扫页面。')

h2('3.4  skill 与规约文件')
para('本项目把三类知识固定成模型必读的文件：')
bullet('数据契约：src/data/types.ts 与 data/demo/scenarios.json 字段一一对应，后端 DTO 必须照此实现；')
bullet('参数表：param_registry.json 共 27 项，每项带 source（observed/public/assumed）、range 与 rationale，'
       '脚本会断言“assumed 必须有区间、public 必须有来源编号”；')
bullet('算法规则：储位分配的四条规则、取件码结构、容量三级阈值，写成自然语言加伪码，模型据此实现。')

h2('3.5  人工审批：三个必须由人拍板的决定')
table(['决定', '模型倾向', '人的判断', '理由'],
      [['删除“矢量校园”底图', '继续修补配色使其可读', '删除，只留手册原图与卫星影像',
        'OSM 在该校区只有 45 个建筑轮廓且不含宿舍楼，渲染出一片空白暗色底，越修越误导'],
       ['重排四站坐标', '沿用旧坐标', '按手册原图红点的相对方位重排',
        '旧数据把桃苑与松苑的南北关系弄反；相对方位可核验，绝对经纬度不可核验'],
       ['旺季放大倍数', '取 3.0（更“刺激”）', '取 2.2，区间 [1.18, 3.0]',
        '下界有国家邮政局数据（118%），上界来自高校开学季（约 2 倍），校园取中上值']],
      widths=[3.2, 3.4, 4.2, 5.0], size=9.5)
caption('表 3-2  三个高风险动作的人工审批记录')

h2('3.6  验证设计')
para('验证分三层：断言层（60 条自动断言）、度量层（布局审计输出裁剪、重叠、对比度数值）、'
     '人工层（截图检查与用户验收）。三层都通过才进入下一阶段。'
     '这与课程强调的“评测集”一致：规格不是文档，而是能跑出红绿灯的东西。')

h1('4  需求分析')

h2('4.1  功能需求')
para('系统面向“校园物流运营者”这一角色，功能需求归纳为六类，对应五个既有页面与一个新增页面：')
table(['编号', '功能', '说明', '优先级'],
      [['F1', '运营总览', '四站实时状态、当日到件与取件、峰值积压与待取、风险时段、地图点位', '高'],
       ['F2', '站点与服务', '站点档案、营业时间、服务项目、分时段运行表、补充服务点', '高'],
       ['F3', '高峰与方案', '双库存堆叠、需求与处理能力对比、方案对比、风险时段清单', '高'],
       ['F4', '异常协同', '由风险时段自动生成的工单、工单详情、处理记录、状态流转', '中'],
       ['F5', '资料与说明', '数据来源、三类标签、公开统计、地图来源、模型假设、明确不做的事', '中'],
       ['F6', '室内与轨迹', '站点室内平面图、货架储位、车辆动态与批次轨迹（v1.5 新增）', '中']],
      widths=[1.4, 3.6, 8.6, 1.8], size=10)
caption('表 4-1  功能需求清单')

h2('4.2  性能需求')
table(['指标', '目标', '当前实测'],
      [['首屏可交互', '≤ 3 s（本地开发服务器）', '约 1.2 s'],
       ['路由切换', '≤ 300 ms', '路由懒加载分包，切换即时'],
       ['图表重绘', '切换站点或场景 ≤ 500 ms', '同帧内完成'],
       ['构建体积', '单包 ≤ 600 KB（gzip ≤ 200 KB）', 'echarts 545 KB/gzip 183 KB，其余分包'],
       ['布局稳定性', '三档宽度零溢出零重叠', '1280/1440/1920 全部为 0'],
       ['仿真耗时（目标）', '1.3 万件、1350 步 ≤ 300 ms', '设计目标，M2 阶段验收']],
      widths=[4.0, 6.2, 5.6], size=10)
caption('表 4-2  性能需求与实测')

h2('4.3  安全需求')
para('本项目为课程演示原型，不含真实用户数据与真实运单，安全边界因此被明确收窄：')
bullet('不做登录、权限、多租户：没有用户体系，也就不引入相应攻击面；')
bullet('不存储、不展示任何真实个人信息：运单号与取件码均为生成值，且不指向真实业务；')
bullet('地图与图片素材：OpenStreetMap 数据遵循 ODbL-1.0 并保留署名；'
       '实景照片的再发布许可未核实，因此只用于课堂演示、不公开分发；')
bullet('后端接口默认只读加演示用写接口，数据库使用本地 H2 文件库，不暴露公网。')

h2('4.4  数据可信度需求（本项目特有）')
para('这是本项目区别于一般课程作业的需求：系统必须能回答“你这个数哪来的”。因此提出三条硬性需求：')
bullet('每个展示数值必须能追溯到三档标签之一（实测/公开/假设），标签不得混用；')
bullet('每个假设参数必须有区间与理由，页面可查；')
bullet('结论必须以相对量表述，使结论在参数区间内不发生反转。')

h1('5  业务建模与系统设计')

h2('5.1  领域模型')
para('系统围绕五个核心实体建模：站点（Site）、批次（Batch）、包裹（Parcel，按批次聚合）、'
     '货架与储位（Shelf / Slot）、工单（WorkOrder）。站点是容量与服务的载体；批次是校外到件的粒度；'
     '包裹是库存与取件的粒度；储位是空间约束的落点；工单是异常处置的载体。'
     '四个实体通过“到件—上架—取件”主流程串联，工单由容量越限事件派生。')

h2('5.2  系统架构')
para('系统采用前后端分离架构。前端为单页应用，按路由懒加载五个页面；数据层做了“双源”设计：'
     '默认读内置样例 JSON，同时异步探测后端 /api/scenarios，探测成功则整包换源，'
     '失败静默回落并在顶栏显示“演示数据模式”。这使后端未完成时前端仍可完整演示，契合“前端先行”的交付顺序。')
table(['层次', '技术', '职责'],
      [['表现层', 'Vue 3 组件 + CSS 变量主题', '页面、组件、深浅主题、无障碍'],
       ['状态层', 'Pinia', '主题、场景、数据源、校准结果'],
       ['数据层', 'useData + api.ts', '样例数据与接口数据的统一入口与回落'],
       ['仿真层', 'TypeScript 模块', '宏观聚合模型 + 实体级离散事件仿真'],
       ['服务层', 'Spring Boot 3.2.3', 'REST 接口、JPA 持久化、服务端仿真'],
       ['存储层', 'H2（开发）/ MySQL 8（可选）', '站点、场景、工单数据']],
      widths=[2.6, 5.4, 7.8], size=10)
caption('表 5-1  系统分层')

h2('5.3  数据契约')
para('前后端以 src/data/types.ts 为唯一契约，字段名与嵌套层级必须逐字一致。'
     '核心结构包括 Scenario（场景）、ScenarioSite（站点参数与需求）、TimelineRow（逐时段仿真结果）、'
     'SiteSummary（站点汇总）与 ScenarioBundle（整包）。'
     '其中 SiteParams 同时保存“标定常量”（capacity_norm、kappa_q_norm、kappa_i_norm）与“本场景实际值”，'
     '用于在界面上区分“场地属性”与“临时措施”。')

h2('5.4  宏观仿真模型')
para('宏观层以 30 分钟为时间桶（07:00—23:30 共 33 桶，桃苑 08:30—18:30 占 20 桶），逐桶递推：')
code_block([
    'S_t      = min(Q_t + A_t, C_t)          本时段实际处理量',
    'Q_(t+1)  = Q_t + A_t - S_t              未处理积压结转',
    'P_t      = min(D_t, I_t + S_t)          实际取走量',
    'I_(t+1)  = I_t + S_t - P_t              待取库存结转',
    '守恒校验  Q_(t+1) + I_(t+1) = Q_t + I_t + A_t - P_t',
])
para('其中 A 为到件、C 为处理上限、D 为取件需求、Q 为未处理积压、I 为已处理待取。'
     '当 Q_(t+1) > κ_q 或 I_(t+1) > κ_i 时判定为风险时段。')
para('模型有一个容易犯的错误：若处理能力 C 按每个场景自身的到件量倒推，'
     '高峰场景的 C 会自动跟着上涨，“高峰撑爆”这一结论就不成立。'
     '本项目的处理是：C0、κ_q0、κ_i0、I0 只在设计峰值场景上标定一次，三个场景共用；'
     '场景若要改变这些常量，必须用显式倍率（cap_mult、kappa_q_mult、kappa_i_mult）表达运营措施。'
     '标定结果见表 5-2。')
table(['站点', 'C0（件/时段）', 'κ_q0（件）', 'κ_i0（件）', 'I0（件）'],
      [['桃苑主站', '298', '477', '2372', '279'],
       ['松苑', '197', '315', '2134', '251'],
       ['梅苑', '167', '267', '1897', '223'],
       ['兰苑', '137', '219', '1502', '177']],
      widths=[3.4, 3.6, 3.2, 3.2, 3.2], size=10)
caption('表 5-2  站点常量标定结果（只在设计峰值场景标定一次）')

h2('5.5  实体级仿真')
para('宏观层能回答“什么时候会满”，但回答不了“货架怎么放、取件码怎么编、车怎么走”。'
     '因此在其上叠加实体层，时间粒度为 1 分钟，随机数采用可复现的 mulberry32。核心算法六个：')
bullet('到车批次生成：日总量 × 承运商份额 → 按车型装载量拆车 → 围绕三个到车窗口做三角分布抖动；')
bullet('卸货与分拣：按卸货速率与在岗人数并行，按承运商与苑区分道；')
bullet('储位分配：同批次同承运商尽量同架、大件进底层、高周转靠出口、满载溢出进临时区，四条规则叠加；')
bullet('取件码生成：格式为“货架号+层号-位号+四位顺序码”，站内唯一且可 O(1) 反查储位；')
bullet('取件需求与排队：按苑区规模 × 时段偏好 × 延迟分布生成，人工台与自助机分别建模服务时间；')
bullet('容量管理：货架 85% 预警、站点 95% 限流、100% 转临时区，越限事件与工单联动。')
para('两层之间用四条一致性断言绑定：件数守恒、峰值对齐（±5%）、无负库存、无超卖。'
     '此外，储位总数由已标定的 κ_i 反推（桃苑 2400、松苑 2100、梅苑 1950、兰苑 1500），'
     '使“平面图上的格子数”与“宏观层的待取上限”成为同一件事，避免两层数字对不上。')

h2('5.6  地图与人工校准')
para('地图采用双底图：默认“手册原图”（离线可用，四个红点即站点位置），可切换“卫星影像”（Esri 在线瓦片）。'
     '之所以去掉最初规划的“矢量校园”底图，是因为 OSM 在该校区只有 45 个建筑轮廓且不含宿舍楼，'
     '渲染效果反而误导。')
para('截图与卫星影像不属于同一投影，像素坐标不能直接当经纬度。项目尝试了四种自动配准'
     '（道路 FFT 互相关、水面多边形匹配、建筑簇匹配、含旋转的 RANSAC），均不收敛，'
     '最终改为“人眼对图 + 程序算坐标”的校准工具：把原图半透明叠在卫星影像上拖动缩放，'
     '四个红点像素位置固定，坐标由程序反算；也可直接在地图上按顺序点四个位置。'
     '校准结果与原图覆盖范围一并持久化，切换底图时红点与图标重合。')

h2('5.7  基于实景照片的内部结构重建')
para('2026 年 11 月，用户提供了桃苑主站的四张内部实景照片。这些照片不是“好看的照片”，'
     '而是可以直接读数的证据，从中提取出四类信息：')
bullet('货架编号体系：号牌覆盖 25 至 155 区间（25-29、30-34、36-41、47-53、71-77、78-84、85-91、'
       '92-98、103-107、108-114、147-154、155），编号连续；用户补充“桃苑至少 220 个货架”，故取 220 为下界；')
bullet('层数与取件码规则：货架端部层标为 41-1、41-2、41-3，每块号牌底部印有“取件码规则”示例'
       '（108-3-2441、147-3-2441），格式统一为“货架号-层号-四位序号”；')
bullet('空间尺度：通道宽约 1.3 m（两人错身需侧身、手推车单向通过），货架高约 2 m、深约 0.6 m、长约 1.5 m；')
bullet('功能分区：长条货架阵列与纵向通道、顺丰独立服务区（白色柜台加扫码屏）、自助取件导向牌、'
       '收银服务台导向，以及一排空置备用货架。')
para('据此把内部结构参数化：物理储位等于货架数乘层数乘每层位数，'
     '桃苑为 220 × 4 × 12 = 10,560 个；而宏观模型标定的待取上限 κ_i 为 2,372 件，仅占 22.5%。'
     '这一比值说明瓶颈不在货架容量，而在通道作业面与人力：照片里通道仅 1.3 m、取件靠人走进去取，'
     '件数一多通道就堵，找件时间与错拿率随之上升，因此 κ_i 是运营管理阈值而非物理容量。'
     '三个无人站没有照片，暂按 κ_i 反推货架数（约 64、57、45 架）并标注为假设档，'
     '拿到照片后只需替换参数表。')

h1('6  实现')

h2('6.1  前端结构与规模')
para('前端共 28 个源文件、3,591 行，按职责分层组织（表 6-1）。')
table(['目录', '内容', '规模'],
      [['src/views', '五个页面视图', '1,461 行'],
       ['src/components', 'CampusMap、EChart、SiteDrawer、KpiCard、CalibratePanel 等', '1,015 行'],
       ['src/composables', 'useData、useDataSource、useChartTheme、useCountUp、useReveal', '约 300 行'],
       ['src/data', '类型定义、站点静态资料、场景数据、接口探测', '约 400 行'],
       ['src/styles', '设计 token 与基础样式', '约 400 行'],
       ['scripts', '四套无头浏览器断言脚本', '约 700 行']],
      widths=[3.6, 9.2, 3.0], size=10)
caption('表 6-1  前端代码组织与规模')

h2('6.2  关键实现')
h3('6.2.1  图表按需引入与分包')
para('ECharts 全量引入会使单包超过 1 MB。项目改用 echarts/core 按需注册，'
     '仅引入 BarChart、LineChart、PieChart 与四个组件，并配合 manualChunks 拆包，'
     '使 echarts 独立成 545 KB（gzip 183 KB）的异步块，主包降至 193 KB。')
h3('6.2.2  地图双底图与标记')
para('地图基于 Leaflet，两个底图分别用 ImageOverlay 与 TileLayer 实现；站点标记用 divIcon 自定义，'
     '随“营业中 / 风险”改变外环颜色，风险站加脉冲动画；主题切换时同步更新标记与图例配色；'
     '底图未加载完成时容器显示点阵底纹，避免被误判为“黑屏”。')
h3('6.2.3  校准面板')
para('校准面板支持拖拽与缩放原图、键盘微调、透明度调节，实时反算四个站点坐标并写回 localStorage；'
     '同时保存原图覆盖范围，使“手册原图”底图上的红点与站点图标重合。面板支持 Esc 关闭，'
     '重新打开时接着上次的校准结果。')
h3('6.2.4  主题与可访问性')
para('深浅双主题通过 CSS 变量实现，浅色主题为文字单独定义 --*-ink 变量以保证对比度；'
     '焦点环统一 2 px；抽屉支持 Esc 关闭与焦点回归；动画尊重 prefers-reduced-motion。')

h2('6.3  数据生成与校验脚本')
para('数据侧用 Python 脚本生成三个场景的逐桶数据，关键处理有两个：'
     '一是用最大余数法保证分流后各站件数之和精确等于总量，避免出现 6202 与 6200 的取整漂移；'
     '二是把“站点常量标定”与“场景运营措施”分离。脚本内置不变量断言，'
     '例如“第三个场景的四站到件合计必须严格等于第二个场景”。')

h1('7  验证与性能分析')

h2('7.1  测试矩阵')
table(['套件', '断言数', '覆盖内容', '结果'],
      [['interact', '31', '导航、场景切换、地图点选、抽屉、图表重绘、工单流转、主题、底图', '全部通过'],
       ['keyboard', '9', '跳过链接、焦点环、Tab 顺序、Enter 激活、Esc 关闭', '全部通过'],
       ['calibrate', '20', '校准面板两种模式、拖拽、缩放、Esc、持久化、重置', '全部通过'],
       ['audit', '逐页度量', '横向溢出、裁剪、重叠、文字对比度、画布绘制率', '三档宽度均为 0 问题'],
       ['控制台', '—', '运行时错误与 Vue 警告', '0 条']],
      widths=[2.8, 2.2, 8.6, 3.2], size=10)
caption('表 7-1  前端自动化断言结果（2026-11-03）')

h2('7.2  布局与对比度审计')
para('审计脚本在 1280、1440、1920 三档宽度与深浅两套主题下逐页测量，输出三类指标：'
     '文档滚动宽度与视口宽度之差（横向溢出）、元素裁剪数、元素两两重叠数，五个页面全部为 0。'
     '对比度方面，初版浅色主题的次要文字与标签底色对比度仅 1.9—2.2，低于 WCAG AA 的 4.5；'
     '通过为浅色主题单独定义 --*-ink 变量并加深色调后复测通过。')

h2('7.3  性能分析')
table(['项目', '数值', '说明'],
      [['主包体积', '193 KB（gzip 57 KB）', 'Vue + 路由 + 状态 + 页面逻辑'],
       ['echarts 分包', '545 KB（gzip 183 KB）', '按需引入后仍为大头，异步加载'],
       ['leaflet 分包', '150 KB（gzip 43 KB）', '仅地图页加载'],
       ['构建耗时', '约 7—13 s', 'vite build 与 vue-tsc 类型检查'],
       ['首屏可交互', '约 1.2 s', '本地开发服务器'],
       ['仿真耗时（目标）', '≤ 300 ms', '1.3 万件 / 1350 步，M2 阶段验收']],
      widths=[3.8, 5.6, 6.4], size=10)
caption('表 7-2  性能数据')

h2('7.4  失败与返工记录')
para('课程说明要求拒绝速成文档，因此本节如实记录三类失败，因为它们比成功更能说明工程判断：')
bullet('地图配准四次不收敛：道路互相关最好命中率 20%，而随机摆放即有 15%；'
       '水面匹配因校区外大水体缺失而失效；建筑簇匹配因 OSM 无宿舍轮廓而失效；'
       '含旋转的 RANSAC 内点仅 5 个、残差 37 像素。结论是不再追求自动配准，改为人工校准工具。')
bullet('站点经纬度最初由 POI 锚点推定，导致桃苑与松苑南北颠倒；'
       '后按手册原图四个红点的相对方位重排，并在页面明确标注“非测绘成果”。')
bullet('处理能力曾按各场景自身到件量倒推，导致高峰场景自动扩容、风险消失；'
       '改为“常量只在设计峰值标定一次 + 场景显式倍率”后才恢复正确。')

h1('8  总结与展望')

h2('8.1  完成情况')
para('截至目前，前端五个页面与双底图地图、三场景切换、工单流转、地图校准工具均已完成并通过 60 条自动断言；'
     '数据侧完成三场景逐桶数据、27 项参数注册表与 23 条来源目录；'
     '实体级仿真与后端服务按计划在后续阶段实现。')

h2('8.2  方法上的收获')
para('本项目最大的收获不是写了多少行代码，而是学会在“数据不可得”的条件下仍然做出可信的系统：'
     '把数字变成参数、把参数变成区间、把结论变成相对量，再用断言保证模型内部自洽。'
     '这套方法可以被任何“拿不到真实数据”的课程项目复用。')

h2('8.3  不足与展望')
bullet('实体级仿真尚未落地，货架与储位仍是设计示意而非实测平面；用户提供实拍照片后将按照片修正；')
bullet('后端尚未实现，当前以样例数据演示，接口契约已固定，后端按契约实现即可切换；')
bullet('参数区间来自公开资料的上下界推演，若日后获得运营数据，只需替换参数表而无需改动代码。')

h1('参考文献')
refs = [
    '[1] 中国矿业大学总务部. 我校南湖菜鸟驿站喜获双项荣誉[EB/OL]. https://zwb.cumt.edu.cn/info/1029/7982.htm.',
    '[2] 中国矿业大学总务部. 南湖校区无人快递超市改建[EB/OL]. https://zwb.cumt.edu.cn/info/1029/5811.htm.',
    '[3] CUMT 生存手册. 物流服务[EB/OL]. https://www.cumtlive.com/Life/Service/Logistics.html.',
    '[4] 新华社. 139.38 亿件！2025 年“双 11”期间快递业务量再创新高[EB/OL]. https://www.news.cn/fortune/20251112/c261f96ed1ca45858f1a7774c3c27d0f/c.html, 2025-11-12.',
    '[5] 闽南日报. 快递驿站的自助取件真的好用吗？[N/OL]. http://www.zzxww.com/pc/content/202403/05/content_127924.html, 2024-03-05.',
    '[6] 光明网. “人还未至，行李先到”，开学前有高校驿站每日到 3 万个包裹[EB/OL]. https://m.gmw.cn/2025-09/08/content_1304139182.htm, 2025-09-08.',
    '[7] 国务院. 快递暂行条例[Z]. 2018-03-27. https://www.gov.cn/zhengce/content/2018-03/27/content_5277757.htm.',
    '[8] OpenStreetMap contributors. OpenStreetMap[DB/OL]. https://www.openstreetmap.org/, ODbL-1.0.',
    '[9] Esri. World Imagery MapServer[DB/OL]. https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer.',
    '[10] 菜鸟驿站[EB/OL]. 百度百科. https://baike.baidu.com/item/%E8%8F%9C%E9%B8%9F%E9%A9%BF%E7%AB%99.',
]
for rtext in refs:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Pt(24)
    p.paragraph_format.first_line_indent = Pt(-24)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run(rtext)
    set_font(r, '宋体', 10.5)

h1('附录 A  参数注册表摘要')
para('以下 27 项参数中，9 项为本项目脚本实测或用户实景照片读数、1 项来自公开商品规格、17 项为演示假设；'
     '假设项均给出区间与理由，真实数据到手后只需替换参数表。表 A-1 节选 11 项。')
table(['编号', '参数', '取值', '区间', '档位'],
      [['P-DAILY-ARRIVAL', '设计峰值日到件', '13,640 件', '11,000—16,000', '假设'],
       ['P-D11-MULT', '旺季放大倍数', '2.2 倍', '1.18—3.0', '假设'],
       ['P-PICKUP-RATIO', '当日取件比', '0.68', '0.55—0.80', '假设'],
       ['P-BATCH-WINDOWS', '到车窗口', '08:30/12:30/16:00', '±45 min', '假设'],
       ['P-TRUCK-LOAD', '单车装载量', '800/1200/1800 件', '600—2000', '假设'],
       ['P-UNLOAD-RATE', '卸货速率', '25 件/分/人', '20—30', '假设'],
       ['P-HOLD-DAYS', '保管期', '3 天', '3—10', '假设'],
       ['P-RACK-COUNT', '桃苑货架总数', '220 架', '220—280', '实测'],
       ['P-PHYSICAL-SLOTS', '物理储位总数', '10,560 个', '10,560—22,400', '实测'],
       ['P-SHELF-OBSERVED', '货架构造', '1.5×0.6×2.0 m / 4 层', '±15%', '实测'],
       ['P-CODE-FORMAT', '取件码结构', '货架+层-位+四位码', '—', '公开'],
       ['P-ROUTE-GRAPH', '院内路网规模', '615 节点/647 边', '—', '实测']],
      widths=[4.2, 3.4, 4.6, 3.0, 1.6], size=9.5)
caption('表 A-1  参数注册表摘要（节选）')

h1('附录 B  复现步骤')
code_block([
    '1) 安装依赖',
    '   cd frontend && npm install',
    '2) 启动开发服务器',
    '   npm run dev                # http://127.0.0.1:5173',
    '3) 运行断言（另开终端）',
    '   node scripts/interact.mjs',
    '   node scripts/keyboard.mjs',
    '   node scripts/calibrate.mjs',
    '   node scripts/audit.mjs http://127.0.0.1:5173 1440 dark',
    '4) 重新生成场景数据（可选）',
    '   python data/research/generate_demo_scenarios.py',
    '5) 构建',
    '   npm run build',
], size=10)

page_number_footer()

# 文件被 Word 打开时无法覆盖，自动退到带版本号的文件名
save_path = OUT
try:
    doc.save(save_path)
except PermissionError:
    save_path = OUT.replace('.docx', '_v2.docx')
    doc.save(save_path)
    print('原文件被占用（可能正在 Word 里打开），已另存为:', save_path)

print('saved:', save_path)
print('paragraphs:', len(doc.paragraphs), 'tables:', len(doc.tables))
