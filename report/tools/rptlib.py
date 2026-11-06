# -*- coding: utf-8 -*-
"""课程报告的排版工具：字体、标题、表格、插图、目录、页眉页脚。"""
import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BODY_FONT = '宋体'
HEAD_FONT = '黑体'
CODE_FONT = 'Consolas'
INK = (0, 0, 0)
TEXT_W = 15.4  # cm，正文可用宽度


class Report:
    def __init__(self, title='', header=''):
        self.doc = Document()
        self.title = title
        self._seq = {'fig': {}, 'tab': {}}
        self._break = False
        self._setup()
        if header:
            self._header(header)

    # ---------------- 基础 ----------------
    def _setup(self):
        sec = self.doc.sections[0]
        sec.page_width = Cm(21.0)
        sec.page_height = Cm(29.7)
        sec.top_margin = Cm(2.4)
        sec.bottom_margin = Cm(2.4)
        sec.left_margin = Cm(3.0)
        sec.right_margin = Cm(2.6)
        sec.header_distance = Cm(1.4)
        sec.footer_distance = Cm(1.4)

        normal = self.doc.styles['Normal']
        normal.font.name = BODY_FONT
        normal.font.size = Pt(12)
        normal.element.rPr.rFonts.set(qn('w:eastAsia'), BODY_FONT)
        pf = normal.paragraph_format
        pf.line_spacing = 1.5
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)

        # 打开文档时提示更新域（目录）
        settings = self.doc.settings.element
        upd = OxmlElement('w:updateFields')
        upd.set(qn('w:val'), 'true')
        settings.append(upd)

    @staticmethod
    def set_font(run, name=BODY_FONT, size=12, bold=False, color=None, italic=False):
        run.font.name = name
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        if color:
            run.font.color.rgb = RGBColor(*color)
        rpr = run._element.get_or_add_rPr()
        rf = rpr.find(qn('w:rFonts'))
        if rf is None:
            rf = OxmlElement('w:rFonts')
            rpr.append(rf)
        rf.set(qn('w:eastAsia'), name)

    def _header(self, text):
        hdr = self.doc.sections[0].header
        p = hdr.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = p.add_run(text)
        self.set_font(r, BODY_FONT, 9, color=(0x59, 0x59, 0x59))
        # 页眉下划线
        pPr = p._p.get_or_add_pPr()
        bdr = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '4')
        bottom.set(qn('w:space'), '1')
        bottom.set(qn('w:color'), 'BFBFBF')
        bdr.append(bottom)
        pPr.append(bdr)

    def footer_page_number(self, prefix='', suffix=''):
        footer = self.doc.sections[0].footer
        p = footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if prefix:
            r = p.add_run(prefix)
            self.set_font(r, BODY_FONT, 9, color=(0x59, 0x59, 0x59))
        # 完整的 PAGE 域：begin → instrText → separate → 占位 → end
        run = p.add_run()
        begin = OxmlElement('w:fldChar')
        begin.set(qn('w:fldCharType'), 'begin')
        instr = OxmlElement('w:instrText')
        instr.set(qn('xml:space'), 'preserve')
        instr.text = ' PAGE '
        sep = OxmlElement('w:fldChar')
        sep.set(qn('w:fldCharType'), 'separate')
        txt = OxmlElement('w:t')
        txt.text = '1'
        end = OxmlElement('w:fldChar')
        end.set(qn('w:fldCharType'), 'end')
        for el in (begin, instr, sep, txt, end):
            run._r.append(el)
        self.set_font(run, BODY_FONT, 9)
        if suffix:
            r2 = p.add_run(suffix)
            self.set_font(r2, BODY_FONT, 9, color=(0x59, 0x59, 0x59))

    def _apply_break(self, par):
        """把“分页”变成下一段的 page_break_before，避免空段落单独占一页。"""
        if self._break:
            par.paragraph_format.page_break_before = True
            self._break = False
    # ---------------- 文本 ----------------
    def p(self, text='', size=12, bold=False, align='justify', indent=2, font=BODY_FONT,
          before=0, after=0, line=1.5, color=None):
        amap = {'justify': WD_ALIGN_PARAGRAPH.JUSTIFY, 'center': WD_ALIGN_PARAGRAPH.CENTER,
                'left': WD_ALIGN_PARAGRAPH.LEFT, 'right': WD_ALIGN_PARAGRAPH.RIGHT}
        par = self.doc.add_paragraph()
        self._apply_break(par)
        par.alignment = amap[align]
        pf = par.paragraph_format
        pf.line_spacing = line
        pf.space_before = Pt(before)
        pf.space_after = Pt(after)
        if indent:
            pf.first_line_indent = Pt(size * indent)
        if text:
            r = par.add_run(text)
            self.set_font(r, font, size, bold, color)
        return par

    def rich(self, parts, size=12, align='justify', indent=2, line=1.5):
        """parts: [(text, bold, color_or_None), ...]"""
        amap = {'justify': WD_ALIGN_PARAGRAPH.JUSTIFY, 'center': WD_ALIGN_PARAGRAPH.CENTER,
                'left': WD_ALIGN_PARAGRAPH.LEFT}
        par = self.doc.add_paragraph()
        self._apply_break(par)
        par.alignment = amap[align]
        par.paragraph_format.line_spacing = line
        if indent:
            par.paragraph_format.first_line_indent = Pt(size * indent)
        for text, bold, color in parts:
            r = par.add_run(text)
            self.set_font(r, BODY_FONT, size, bold, color)
        return par

    def bullet(self, text, size=12, level=0):
        par = self.doc.add_paragraph()
        pf = par.paragraph_format
        pf.left_indent = Pt(size * (2 + 2 * level))
        pf.first_line_indent = Pt(-size)
        pf.line_spacing = 1.5
        r = par.add_run(('· ' if level == 0 else '– ') + text)
        self.set_font(r, BODY_FONT, size)
        return par

    def h1(self, text, num=None):
        par = self.doc.add_paragraph(style='Heading 1')
        self._apply_break(par)
        pf = par.paragraph_format
        pf.space_before = Pt(16)
        pf.space_after = Pt(8)
        pf.line_spacing = 1.5
        pf.keep_with_next = True
        r = par.add_run((f'{num}  ' if num else '') + text)
        self.set_font(r, HEAD_FONT, 15, False, INK)
        return par

    def h2(self, text, num=None):
        par = self.doc.add_paragraph(style='Heading 2')
        self._apply_break(par)
        pf = par.paragraph_format
        pf.space_before = Pt(10)
        pf.space_after = Pt(4)
        pf.line_spacing = 1.5
        pf.keep_with_next = True
        r = par.add_run((f'{num}  ' if num else '') + text)
        self.set_font(r, HEAD_FONT, 13, False, INK)
        return par

    def h3(self, text, num=None):
        par = self.doc.add_paragraph(style='Heading 3')
        self._apply_break(par)
        pf = par.paragraph_format
        pf.space_before = Pt(6)
        pf.space_after = Pt(2)
        pf.line_spacing = 1.5
        pf.keep_with_next = True
        r = par.add_run((f'{num}  ' if num else '') + text)
        self.set_font(r, BODY_FONT, 12, True, INK)
        return par

    def code(self, lines, size=9.5):
        for ln in lines:
            par = self.doc.add_paragraph()
            pf = par.paragraph_format
            pf.left_indent = Pt(18)
            pf.line_spacing = 1.15
            pf.space_before = Pt(0)
            pf.space_after = Pt(0)
            r = par.add_run(ln if ln else ' ')
            self.set_font(r, CODE_FONT, size)

    # ---------------- 图表 ----------------
    def fig(self, path, caption, width=TEXT_W, after=10):
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.space_before = Pt(6)
        par.paragraph_format.space_after = Pt(2)
        par.paragraph_format.keep_with_next = True
        run = par.add_run()
        run.add_picture(path, width=Cm(width))
        cap = self.doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_before = Pt(0)
        cap.paragraph_format.space_after = Pt(after)
        r = cap.add_run(caption)
        self.set_font(r, BODY_FONT, 10, color=(0x40, 0x40, 0x40))

    def table(self, caption, headers, rows, widths=None, size=10, align_first_left=True,
              after=10, note=None):
        cap = self.doc.add_paragraph()
        self._apply_break(cap)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_before = Pt(8)
        cap.paragraph_format.space_after = Pt(3)
        cap.paragraph_format.keep_with_next = True
        r = cap.add_run(caption)
        self.set_font(r, BODY_FONT, 10, True, (0x40, 0x40, 0x40))

        t = self.doc.add_table(rows=1, cols=len(headers))
        t.style = 'Table Grid'
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        # 表头
        hdr = t.rows[0]
        trPr = hdr._tr.get_or_add_trPr()
        th = OxmlElement('w:tblHeader')
        th.set(qn('w:val'), 'true')
        trPr.append(th)
        for i, h in enumerate(headers):
            cell = hdr.cells[i]
            cell.text = ''
            par = cell.paragraphs[0]
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            par.paragraph_format.line_spacing = 1.15
            par.paragraph_format.space_before = Pt(2)
            par.paragraph_format.space_after = Pt(2)
            run = par.add_run(h)
            self.set_font(run, BODY_FONT, size, True)
            self._shade(cell, 'F2EFE6')
        for row in rows:
            tr = t.add_row()
            trPr2 = tr._tr.get_or_add_trPr()
            cs = OxmlElement('w:cantSplit')
            cs.set(qn('w:val'), 'true')
            trPr2.append(cs)
            cells = tr.cells
            for i, val in enumerate(row):
                cells[i].text = ''
                par = cells[i].paragraphs[0]
                par.alignment = (WD_ALIGN_PARAGRAPH.LEFT if (i == 0 and align_first_left)
                                 else WD_ALIGN_PARAGRAPH.CENTER)
                par.paragraph_format.line_spacing = 1.15
                par.paragraph_format.space_before = Pt(2)
                par.paragraph_format.space_after = Pt(2)
                run = par.add_run(str(val))
                self.set_font(run, BODY_FONT, size)
        # 小表整体不跨页：除最后一行外，所有单元格段落 keep_with_next
        if len(rows) <= 8:
            for row in t.rows[:-1]:
                for cell in row.cells:
                    for par in cell.paragraphs:
                        par.paragraph_format.keep_with_next = True
        if widths:
            # 固定表格布局，否则 Word/LO 会按内容自动均分列宽
            tblPr = t._tbl.tblPr
            layout = OxmlElement('w:tblLayout')
            layout.set(qn('w:type'), 'fixed')
            tblPr.append(layout)
            tblW = OxmlElement('w:tblW')
            tblW.set(qn('w:w'), str(int(sum(widths) * 567)))
            tblW.set(qn('w:type'), 'dxa')
            tblPr.append(tblW)
            for i, w in enumerate(widths):
                t.columns[i].width = Cm(w)
                for row in t.rows:
                    row.cells[i].width = Cm(w)
        if note:
            n = self.doc.add_paragraph()
            n.paragraph_format.space_before = Pt(2)
            n.paragraph_format.space_after = Pt(after)
            r = n.add_run(note)
            self.set_font(r, BODY_FONT, 9, color=(0x59, 0x59, 0x59))
        else:
            spacer = self.doc.add_paragraph()
            spacer.paragraph_format.space_after = Pt(0)
            spacer.paragraph_format.line_spacing = 0.6
        return t

    @staticmethod
    def _shade(cell, hex_color):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), hex_color)
        tcPr.append(shd)

    # ---------------- 目录 / 分页 ----------------
    def toc(self):
        par = self.doc.add_paragraph()
        run = par.add_run()
        begin = OxmlElement('w:fldChar')
        begin.set(qn('w:fldCharType'), 'begin')
        instr = OxmlElement('w:instrText')
        instr.set(qn('xml:space'), 'preserve')
        instr.text = r'TOC \o "1-2" \h \z \u'
        sep = OxmlElement('w:fldChar')
        sep.set(qn('w:fldCharType'), 'separate')
        txt = OxmlElement('w:t')
        txt.text = '（在 Word 中右键此处 →“更新域”生成目录）'
        end = OxmlElement('w:fldChar')
        end.set(qn('w:fldCharType'), 'end')
        for el in (begin, instr, sep, txt, end):
            run._r.append(el)
        self.set_font(run, BODY_FONT, 10.5, color=(0x59, 0x59, 0x59))

    def page_break(self):
        self._break = True

    def save(self, path):
        self.doc.save(path)
        print('saved:', path)
        print('paragraphs:', len(self.doc.paragraphs), 'tables:', len(self.doc.tables))
