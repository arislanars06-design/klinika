"""(Re)generate ``templates/reception_template.docx``.

The template is a docxtpl document with Jinja placeholders. It renders one
reception (patient + complaints + LOR STATUS + diagnosis + recommendation)
as an A4 sheet.

All clinic identity fields (name, address, phone, logo) come from the
Settings → Клиника screen and are pulled through placeholders — the
template ships without any hard-coded clinic name.

To regenerate the shipped template:

    python scripts/build_reception_template.py

The Settings → Шаблон page invokes this same function via
``build_default_template()``.
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
DEFAULT_DST = ROOT / "templates" / "reception_template.docx"


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _set_cell_border(cell, *, size: int = 4, color: str = "808080") -> None:
    """Apply a thin grey border to all four edges of a table cell."""
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


def _shade_cell(cell, hex_color: str) -> None:
    """Fill a table cell with a background color (e.g. ``"F0F0F0"``)."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def _heading(doc, text: str, *, size: int = 11) -> None:
    """Add a section heading with a light grey background bar."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
    # Underline the heading with a thin bottom border on the paragraph.
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "808080")
    pBdr.append(bottom)
    pPr.append(pBdr)


def _body_para(doc, text: str, *, size: int = 11, bold: bool = False, color: tuple | None = None) -> None:
    """Add a plain body paragraph."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def _kv_table(doc, rows: list[tuple[str, str]]) -> None:
    """Two-column key/value table for the patient block."""
    tbl = doc.add_table(rows=len(rows), cols=2)
    tbl.autofit = False
    tbl.columns[0].width = Cm(4.5)
    tbl.columns[1].width = Cm(12.5)
    for i, (k, v) in enumerate(rows):
        c0, c1 = tbl.rows[i].cells
        c0.width = Cm(4.5)
        c1.width = Cm(12.5)
        c0.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        c1.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        _shade_cell(c0, "F5F5F5")
        r0 = c0.paragraphs[0].add_run(k)
        r0.bold = True
        r0.font.size = Pt(10)
        r0.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
        r1 = c1.paragraphs[0].add_run(v)
        r1.font.size = Pt(11)
        _set_cell_border(c0)
        _set_cell_border(c1)


# ---------------------------------------------------------------------------
# Template body
# ---------------------------------------------------------------------------


def _write_clinic_header(doc) -> None:
    """Clinic identity block — all values are docxtpl placeholders.

    Filled at render time from ``ClinicInfo`` (Settings → Клиника).
    """
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("{{ clinic.name }}")
    r.bold = True
    r.font.size = Pt(14)
    r.font.color.rgb = RGBColor(0x0A, 0x35, 0x66)

    # Address line
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_after = Pt(0)
    r2 = p2.add_run("{{ clinic.address }}")
    r2.font.size = Pt(10)
    r2.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    # Phone line
    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3.paragraph_format.space_after = Pt(6)
    r3 = p3.add_run("Тел: {{ clinic.phone }}")
    r3.font.size = Pt(10)
    r3.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    # Divider
    div = doc.add_paragraph()
    div.paragraph_format.space_before = Pt(0)
    div.paragraph_format.space_after = Pt(6)
    pPr = div._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "0A3566")
    pBdr.append(bottom)
    pPr.append(pBdr)


def build_default_template(dst: Path | None = None) -> Path:
    """Write the default template to disk and return its path.

    Called both from the CLI and from the Settings → Шаблон "Reset to
    default" button.
    """
    dst = Path(dst or DEFAULT_DST)

    doc = Document()

    # Page margins tuned for A4 portrait.
    for section in doc.sections:
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(2.0)

    # ---- Clinic identity header (all placeholders) ----
    _write_clinic_header(doc)

    # ---- Document title ----
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(6)
    title.paragraph_format.space_after = Pt(0)
    trun = title.add_run("QABUL VARAQASI  /  ЛИСТ ПРИЁМА")
    trun.bold = True
    trun.font.size = Pt(14)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_before = Pt(0)
    subtitle.paragraph_format.space_after = Pt(10)
    srun = subtitle.add_run("Sana / Дата: {{ reception.date }}    №{{ reception.id }}")
    srun.font.size = Pt(10)
    srun.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    # ---- Patient block ----
    _heading(doc, "BEMOR HAQIDA MA'LUMOT  /  СВЕДЕНИЯ О ПАЦИЕНТЕ")
    _kv_table(
        doc,
        [
            ("F.I.SH. / Ф.И.О.", "{{ patient.full_name }}"),
            (
                "Tug'ilgan yili / Год рождения",
                "{{ patient.birth_year }}  ({{ patient.age }} yosh / лет)",
            ),
            ("Manzil / Адрес", "{{ patient.address }}"),
            ("Telefon / Телефон", "{{ patient.phone }}"),
        ],
    )
    doc.add_paragraph()

    # ---- Sections ----
    _heading(doc, "SHIKOYATLAR  /  ЖАЛОБЫ")
    _body_para(doc, "{{ reception.complaints_text }}")
    doc.add_paragraph()

    _heading(doc, "ANAMNEZ  /  АНАМНЕЗ")
    _body_para(doc, "{{ reception.anamnesis }}")
    doc.add_paragraph()

    _heading(doc, "LOR STATUS  /  ЛОР СТАТУС")
    _body_para(doc, "{{ reception.lor_status_text }}")
    doc.add_paragraph()

    _heading(doc, "TASHXIS  /  ДИАГНОЗ")
    _body_para(doc, "{{ reception.diagnosis }}", size=12, bold=True)
    doc.add_paragraph()

    _heading(doc, "TAVSIYALAR  /  РЕКОМЕНДАЦИИ")
    _body_para(doc, "{{ reception.recommendation }}")
    doc.add_paragraph()
    doc.add_paragraph()

    # ---- Doctor signature block ----
    sig_tbl = doc.add_table(rows=1, cols=2)
    sig_tbl.autofit = True
    left_cell, right_cell = sig_tbl.rows[0].cells
    left_cell.width = Cm(10)
    right_cell.width = Cm(7)

    # Left cell: doctor name + phone
    lp = left_cell.paragraphs[0]
    r1 = lp.add_run("Shifokor / Врач: ")
    r1.bold = True
    r1.font.size = Pt(11)
    r2 = lp.add_run("{{ doctor.full_name }}")
    r2.font.size = Pt(11)

    lp2 = left_cell.add_paragraph()
    r3 = lp2.add_run("Tel: {{ doctor.phone }}")
    r3.font.size = Pt(10)
    r3.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

    # Right cell: signature line + date
    rp = right_cell.paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r4 = rp.add_run("Imzo / Подпись: ______________________")
    r4.font.size = Pt(11)

    rp2 = right_cell.add_paragraph()
    rp2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r5 = rp2.add_run("Sana / Дата: {{ today }}")
    r5.font.size = Pt(10)
    r5.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

    dst.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(dst))
    return dst


def main() -> None:
    path = build_default_template()
    print(f"[OK] Wrote: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
