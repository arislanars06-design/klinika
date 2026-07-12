"""Regenerate ``templates/reception_template.docx``.

The template contains a clinic header (name, services, address, phones) —
copy those from the current template file itself — and a body of ``docxtpl``
placeholders for reception data.

To customize the header, edit ``reception_template.docx`` directly in Word;
this script only needs to run when you want to reset to a known baseline
after breaking the placeholder block.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
DST = ROOT / "templates" / "reception_template.docx"


# Baseline clinic header text if no existing template exists yet.
DEFAULT_HEADER = [
    ("ЎЗБЕКИСТОН РЕСПУБЛИКАСИ СОҒЛИҚНИ САҚЛАШ ВАЗИРЛИГИ", "bold_big"),
    ("ОТОРИНОЛАРИНГОЛОГИЯ КАСАЛЛИКЛАРИНИ ЗАМОНАВИЙ ТЕКШИРИШ ВА ДАВОЛАШ ХУСУСИЙ", "bold_big"),
    ("КЛИНИКАСИ", "bold_big"),
    ("       * ЛОР", "plain"),
    ("       * Ревматолог", "plain"),
    ("       * Гирудотерапия (зулук билан даволаш)", "plain"),
    ("       * Хиджама (банка ёрдамида даволаш)", "plain"),
    ("       * Лаборатория", "plain"),
    ("       * Массаж", "plain"),
    ("", "plain"),
    ("Манзил: Сергели тумани, 7 - мавзе, 32-уй, 55 - хонадон", "small"),
    ("Телефонлар:  + 998 93 391 91 64     + 998 99 981 91 64", "small"),
]


def _set_cell_border(cell, *, size: int = 4, color: str = "808080") -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_borders = tc_pr.find(qn("w:tcBorders"))
    if tc_borders is None:
        tc_borders = OxmlElement("w:tcBorders")
        tc_pr.append(tc_borders)
    for edge in ("top", "left", "bottom", "right"):
        existing = tc_borders.find(qn(f"w:{edge}"))
        if existing is not None:
            tc_borders.remove(existing)
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:color"), color)
        tc_borders.append(el)


def _heading(doc, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x11, 0x11, 0x11)


def _plain(doc, text: str, *, size: int = 11, bold: bool = False) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.bold = bold


def _kv_table(doc, rows: list[tuple[str, str]]) -> None:
    """Two-column key/value table for the patient block."""
    tbl = doc.add_table(rows=len(rows), cols=2)
    tbl.autofit = False
    tbl.columns[0].width = Cm(5.5)
    tbl.columns[1].width = Cm(11.5)
    for i, (k, v) in enumerate(rows):
        c0, c1 = tbl.rows[i].cells
        c0.width = Cm(5.5)
        c1.width = Cm(11.5)
        c0.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        c1.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        r0 = c0.paragraphs[0].add_run(k)
        r0.bold = True
        r0.font.size = Pt(10)
        r1 = c1.paragraphs[0].add_run(v)
        r1.font.size = Pt(11)
        _set_cell_border(c0)
        _set_cell_border(c1)


def _write_default_header(doc) -> None:
    """Fresh document — insert the baseline header."""
    for text, style in DEFAULT_HEADER:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if style != "small" else WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(text)
        if style == "bold_big":
            run.bold = True
            run.font.size = Pt(13)
        elif style == "small":
            run.font.size = Pt(10)
        else:
            run.font.size = Pt(11)


def main() -> None:
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(2.0)

    _write_default_header(doc)

    # Separator + title.
    doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    trun = title.add_run("QABUL VARAQASI")
    trun.bold = True
    trun.font.size = Pt(14)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    srun = subtitle.add_run("Sana: {{ reception.date }}    №{{ reception.id }}")
    srun.font.size = Pt(10)
    srun.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    doc.add_paragraph()

    # Patient block
    _heading(doc, "BEMOR HAQIDA MA'LUMOT")
    _kv_table(
        doc,
        [
            ("F.I.SH.", "{{ patient.full_name }}"),
            ("Tug'ilgan yili", "{{ patient.birth_year }}  ({{ patient.age }} yosh)"),
            ("Manzil", "{{ patient.address }}"),
            ("Telefon", "{{ patient.phone }}"),
        ],
    )
    doc.add_paragraph()

    # Sections
    for section_title, placeholder, *style in [
        ("SHIKOYATLAR", "{{ reception.complaints_text }}"),
        ("ANAMNEZ", "{{ reception.anamnesis }}"),
        ("LOR STATUS", "{{ reception.lor_status_text }}"),
        ("TASHXIS", "{{ reception.diagnosis }}", {"size": 12, "bold": True}),
        ("TAVSIYA", "{{ reception.recommendation }}"),
    ]:
        opts = style[0] if style else {}
        _heading(doc, section_title)
        _plain(doc, placeholder, **opts)
        doc.add_paragraph()

    doc.add_paragraph()

    # Signature line
    sig = doc.add_paragraph()
    r1 = sig.add_run("Shifokor: {{ doctor.full_name }}")
    r1.font.size = Pt(11)
    r1.bold = True
    sig.add_run("\t" * 4)
    r2 = sig.add_run("Imzo: ______________________")
    r2.font.size = Pt(11)

    tel = doc.add_paragraph()
    r3 = tel.add_run("Tel: {{ doctor.phone }}")
    r3.font.size = Pt(10)
    r3.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

    date_line = doc.add_paragraph()
    r4 = date_line.add_run("Hujjat sanasi: {{ today }}")
    r4.font.size = Pt(9)
    r4.font.color.rgb = RGBColor(0x80, 0x80, 0x80)

    DST.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(DST))
    print(f"[OK] Wrote: {DST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
