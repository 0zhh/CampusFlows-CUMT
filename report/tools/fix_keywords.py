# -*- coding: utf-8 -*-
"""在原文件上补齐/美化摘要的关键词行，不重排全文、不改动其他内容。

用法：python fix_keywords.py
说明：文档若正在 Word 中打开会保存失败，脚本会改存为 *_关键词版.docx 并提示。
"""
import os
import shutil

from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn

DOC = r'D:\java大作业\report\Java语言及网络编程_课程报告_终版.docx'

CN_LABEL = '关键词：'
CN_WORDS = '校园物流；离散事件仿真；数据可信度分级；规格驱动开发；Vue 3；Spring Boot'
EN_LABEL = 'Keywords: '
EN_WORDS = ('campus logistics; discrete-event simulation; data trustworthiness; '
            'specification-driven development; Vue 3; Spring Boot')


def set_run(run, bold=False, size=12, font='宋体', color=(0, 0, 0)):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = font
    run.font.color.rgb = None
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        from docx.oxml import OxmlElement
        rf = OxmlElement('w:rFonts')
        rpr.append(rf)
    rf.set(qn('w:eastAsia'), font)
    rf.set(qn('w:ascii'), font)
    rf.set(qn('w:hAnsi'), font)


def rewrite(par, label, words, font):
    # 清空原有 run，保留段落属性（缩进/行距）
    for r in list(par.runs):
        r._element.getparent().remove(r._element)
    r1 = par.add_run(label)
    set_run(r1, bold=True, size=12, font=font)
    r2 = par.add_run(words)
    set_run(r2, bold=False, size=12, font=font)
    pf = par.paragraph_format
    pf.space_before = Pt(8)
    pf.space_after = Pt(0)
    pf.first_line_indent = Pt(0)


def main():
    doc = Document(DOC)
    hits = 0
    for par in doc.paragraphs:
        t = par.text.strip()
        if t.startswith('关键词'):
            rewrite(par, CN_LABEL, CN_WORDS, '宋体')
            hits += 1
        elif t.startswith('Keywords'):
            rewrite(par, EN_LABEL, EN_WORDS, 'Times New Roman')
            hits += 1
    print('rewritten paragraphs:', hits)

    try:
        doc.save(DOC)
        print('saved in place:', DOC)
    except PermissionError:
        alt = DOC.replace('.docx', '_关键词版.docx')
        doc.save(alt)
        print('原文件被 Word 占用，已另存为:', alt)


if __name__ == '__main__':
    main()
