#!/usr/bin/env python3
"""Сборка PDF книги «Арьергард»: пролог + глава первая."""
import re
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
    KeepTogether,
)
from reportlab.pdfgen import canvas as pdfcanvas

# ---------------------------------------------------------------- шрифты
SYS = "/usr/share/fonts/truetype/dejavu/"
OWN = "/home/user/-/build/fonts/"
pdfmetrics.registerFont(TTFont("Serif", SYS + "DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Bold", SYS + "DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Italic", OWN + "DejaVuSerif-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Serif-BoldItalic", OWN + "DejaVuSerif-BoldItalic.ttf"))
pdfmetrics.registerFontFamily(
    "Serif", normal="Serif", bold="Serif-Bold",
    italic="Serif-Italic", boldItalic="Serif-BoldItalic",
)

PAGE_W, PAGE_H = A5
LM = RM = 17 * mm
TM = 16 * mm
BM = 17 * mm

# ---------------------------------------------------------------- стили
st_title = ParagraphStyle(
    "title", fontName="Serif-Bold", fontSize=30, leading=36,
    alignment=TA_CENTER, spaceAfter=6,
)
st_title_sub = ParagraphStyle(
    "titlesub", fontName="Serif", fontSize=13, leading=18,
    alignment=TA_CENTER, spaceBefore=4,
)
st_title_small = ParagraphStyle(
    "titlesmall", fontName="Serif-Italic", fontSize=11, leading=16,
    alignment=TA_CENTER, spaceBefore=4,
)
st_heading = ParagraphStyle(
    "heading", fontName="Serif-Bold", fontSize=17, leading=22,
    alignment=TA_CENTER, spaceBefore=10, spaceAfter=2,
)
st_subheading = ParagraphStyle(
    "subheading", fontName="Serif-Italic", fontSize=12.5, leading=17,
    alignment=TA_CENTER, spaceAfter=14,
)
st_body = ParagraphStyle(
    "body", fontName="Serif", fontSize=10.5, leading=15.4,
    alignment=TA_JUSTIFY, firstLineIndent=13, spaceAfter=0,
)
st_body_first = ParagraphStyle(
    "bodyfirst", parent=st_body, firstLineIndent=0,
    # компенсация высоты буквицы: reportlab не учитывает высоту строки
    # с увеличенной первой буквой (30pt вместо leading 15.4)
    spaceAfter=30 - 15.4,
)
st_break = ParagraphStyle(
    "brk", fontName="Serif", fontSize=10.5, leading=15,
    alignment=TA_CENTER, spaceBefore=10, spaceAfter=10,
)

# ---------------------------------------------------------------- разметка
SHIP_RE = re.compile(r"«(Тальон[^»]*|Мегги|Бетти)»")

def escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def markup(s: str) -> str:
    s = escape(s)
    # курсив для названий кораблей
    s = SHIP_RE.sub(lambda m: "<i>«%s»</i>" % m.group(1), s)
    # курсив *слово*
    s = re.sub(r"\*([^*\n]+)\*", r"<i>\1</i>", s)
    return s

def dropcap(s: str) -> str:
    """Увеличенная первая буква абзаца."""
    s = markup(s)
    m = re.match(r"(\S)(\s*)", s)
    if not m:
        return s
    first, rest = m.group(1), s[m.end():]
    return '<font size="30">%s</font>%s%s' % (first, rest[:0] if False else "", rest)

def read_blocks(path):
    raw = open(path, encoding="utf-8").read()
    parts = re.split(r"\n\s*\n", raw.strip())
    return [p.strip() for p in parts if p.strip()]

def build_story():
    story = []
    # ---- титульный лист
    story.append(Spacer(1, 38 * mm))
    story.append(Paragraph("АРЬЕРГАРД", st_title))
    rule = ParagraphStyle("rule", fontName="Serif", fontSize=12, leading=14,
                          alignment=TA_CENTER, spaceBefore=8, spaceAfter=8)
    story.append(Paragraph("— ◆ —", rule))
    story.append(Paragraph("Пролог и глава первая", st_title_sub))
    story.append(Spacer(1, 26 * mm))
    story.append(Paragraph(
        "«Кто стоит за другого —<br/>того ветер не сдует»", st_title_small))
    story.append(Paragraph("— из корабельных поговорок", st_title_small))
    story.append(PageBreak())

    for path in ("/home/user/-/ms/prologue.txt",
                 "/home/user/-/ms/chapter1_part1.txt",
                 "/home/user/-/ms/chapter1_part2.txt"):
        blocks = read_blocks(path)
        first_body_seen = False
        i = 0
        while i < len(blocks):
            b = blocks[i]
            if b == "* * *":
                story.append(Paragraph("∗ ∗ ∗", st_break))
                i += 1
                continue
            lines = [ln.strip() for ln in b.split("\n") if ln.strip()]
            if len(lines) == 1 and (lines[0].startswith("ПРОЛОГ")
                                    or lines[0].startswith("ГЛАВА")):
                # заголовок + подзаголовок следующим блоком
                grp = [Paragraph(lines[0].upper(), st_heading)]
                if i + 1 < len(blocks) and "\n" not in blocks[i + 1] \
                        and not blocks[i + 1].startswith("*"):
                    grp.append(Paragraph(markup(blocks[i + 1]), st_subheading))
                    i += 1
                story.append(KeepTogether(grp))
                first_body_seen = False
                i += 1
                continue
            text = b.replace("\n", " ")
            if not first_body_seen:
                if len(text) >= 120:  # буквица только у развёрнутого абзаца
                    style = st_body_first
                    text = dropcap(text)
                else:
                    style = st_body
                    text = markup(text)
                first_body_seen = True
            else:
                style = st_body
                text = markup(text)
            story.append(Paragraph(text, style))
            i += 1
    return story

class NumberedCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for idx, state in enumerate(self._saved, start=1):
            self.__dict__.update(state)
            if idx > 1:  # без номера на титуле
                self.draw_page_number(idx, total)
            super().showPage()
        super().save()

    def draw_page_number(self, idx, total):
        self.saveState()
        self.setFont("Serif", 8.5)
        self.setFillColorRGB(0.35, 0.35, 0.35)
        self.drawCentredString(PAGE_W / 2, 9 * mm, "— %d —" % idx)
        # колонтитул: только на разворотных страницах
        if idx % 2 == 0:
            self.setFont("Serif-Italic", 7.5)
            self.drawString(LM, PAGE_H - 11 * mm, "Арьергард")
        else:
            self.setFont("Serif-Italic", 7.5)
            self.drawRightString(PAGE_W - RM, PAGE_H - 11 * mm,
                                 "Пролог · Глава первая")
        self.restoreState()

def main():
    out = "/home/user/-/Арьергард — пролог и глава первая.pdf"
    doc = BaseDocTemplate(
        out, pagesize=A5,
        leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
        title="Арьергард — Пролог и глава первая",
        author="", subject="",
    )
    frame = Frame(LM, BM, PAGE_W - LM - RM, PAGE_H - TM - BM,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])
    doc.build(build_story(), canvasmaker=NumberedCanvas)
    print("OK:", out)

if __name__ == "__main__":
    main()
