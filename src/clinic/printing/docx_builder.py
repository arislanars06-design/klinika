"""Generate the reception paper (``.docx``) and statistics reports.

If the user has dropped a ``docxtpl``-style Jinja template at
``templates/reception_template.docx``, we render into that so the clinic's
letterhead is preserved verbatim. Otherwise, we build a minimal default
document from scratch — the doctor can print immediately without any setup.
"""

from __future__ import annotations

import io
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from docxtpl import DocxTemplate
from loguru import logger

from clinic.config import settings as app_settings
from clinic.db.models import Reception
from clinic.domain import doctor_service, patient_service, settings_service
from clinic.printing.text_composer import render_reception_body

RECEPTION_TEMPLATE_NAME = "reception_template.docx"
STATS_TEMPLATE_NAME = "stats_template.docx"


# ----- reception paper -------------------------------------------------------


def _reception_context(reception: Reception, lang: str) -> dict[str, Any]:
    body = render_reception_body(reception, lang)
    patient = reception.patient
    doctor = reception.doctor
    return {
        "clinic": {
            "name": settings_service.get(f"clinic_name_{lang}") or "Klinika LOR",
            "address": settings_service.get(f"clinic_address_{lang}") or "",
            "phone": settings_service.get("clinic_phone") or "",
        },
        "reception": {
            "id": reception.id,
            "date": reception.reception_date.strftime("%d.%m.%Y %H:%M"),
            **body,
        },
        "patient": {
            "full_name": patient.full_name,
            "birth_year": patient.birth_year,
            "age": max(0, datetime.now().year - patient.birth_year),
            "address": patient.address or "",
            "phone": patient.phone or "",
        },
        "doctor": {
            "full_name": doctor.full_name,
            "phone": doctor.phone or "",
        },
    }


def build_reception_docx(reception: Reception, lang: str = "uz") -> bytes:
    """Return the reception paper as raw docx bytes.

    Uses the user-provided template if available; otherwise falls back to a
    minimalist default so print always works.
    """
    template_path = app_settings.templates_dir / RECEPTION_TEMPLATE_NAME
    context = _reception_context(reception, lang)

    if template_path.is_file():
        logger.debug("Rendering reception via user template: {}", template_path)
        tpl = DocxTemplate(str(template_path))
        tpl.render(context)
        buffer = io.BytesIO()
        tpl.save(buffer)
        return buffer.getvalue()

    logger.debug("Rendering reception via built-in default (no template found)")
    return _default_reception_docx(context)


def _default_reception_docx(ctx: dict[str, Any]) -> bytes:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    def h(text: str, size: int = 14, bold: bool = True, center: bool = False) -> None:
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold = bold
        run.font.size = Pt(size)
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def kv(label: str, value: str) -> None:
        p = doc.add_paragraph()
        run = p.add_run(f"{label}: ")
        run.bold = True
        p.add_run(value or "-")

    h(ctx["clinic"]["name"], size=16, center=True)
    if ctx["clinic"]["address"] or ctx["clinic"]["phone"]:
        info = doc.add_paragraph(
            " • ".join(x for x in (ctx["clinic"]["address"], ctx["clinic"]["phone"]) if x)
        )
        info.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()
    h("QABUL VARAQASI", size=13, center=True)
    doc.add_paragraph()

    kv("Sana", ctx["reception"]["date"])
    kv("F.I.O", ctx["patient"]["full_name"])
    kv("Tug'ilgan yili", f"{ctx['patient']['birth_year']} ({ctx['patient']['age']} yosh)")
    kv("Manzil", ctx["patient"]["address"])
    kv("Telefon", ctx["patient"]["phone"])

    doc.add_paragraph()
    for label, key in [
        ("Shikoyatlar", "complaints"),
        ("Anamnez", "anamnesis"),
        ("LOR STATUS", "lor_status"),
        ("Tashxis", "diagnosis"),
        ("Tavsiya", "recommendation"),
    ]:
        value = ctx["reception"].get(key, "")
        if not value:
            continue
        h(label, size=11)
        doc.add_paragraph(value)

    doc.add_paragraph()
    doc.add_paragraph()
    signature = doc.add_paragraph()
    signature.add_run(f"Shifokor: {ctx['doctor']['full_name']}").bold = True
    doc.add_paragraph("Imzo: _____________________")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# ----- statistics reports ----------------------------------------------------


def build_patient_stats_docx(
    stats: Any,
    start: datetime,
    end: datetime,
    lang: str = "uz",
) -> bytes:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("BEMORLAR STATISTIKASI" if lang == "uz" else "СТАТИСТИКА ПАЦИЕНТОВ")
    r.bold = True
    r.font.size = Pt(16)

    doc.add_paragraph(f"{start:%d.%m.%Y} — {end:%d.%m.%Y}").alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()
    _kv_line(doc, "Jami qabullar" if lang == "uz" else "Всего приёмов", stats.total_receptions)
    _kv_line(doc, "Noyob bemorlar" if lang == "uz" else "Уникальных пациентов", stats.unique_patients)
    _kv_line(doc, "Yangi bemorlar" if lang == "uz" else "Новых пациентов", stats.new_patients)
    _kv_line(
        doc,
        "Takroriy qabullar" if lang == "uz" else "Повторные приёмы",
        stats.returning_receptions,
    )

    if stats.top_diagnoses:
        doc.add_paragraph()
        h = doc.add_paragraph()
        h.add_run("TOP tashxislar" if lang == "uz" else "TOP диагнозов").bold = True
        for name, count in stats.top_diagnoses:
            doc.add_paragraph(f"• {name} — {count}")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def build_cashier_stats_docx(
    stats: Any,
    start: datetime,
    end: datetime,
    lang: str = "uz",
) -> bytes:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("KASSA HISOBOTI" if lang == "uz" else "ОТЧЁТ ПО КАССЕ")
    r.bold = True
    r.font.size = Pt(16)

    doc.add_paragraph(f"{start:%d.%m.%Y} — {end:%d.%m.%Y}").alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()
    _kv_line(
        doc,
        "Jami tushum" if lang == "uz" else "Общая выручка",
        _money(stats.total_revenue, lang),
    )
    _kv_line(doc, "To'lovlar soni" if lang == "uz" else "Число операций", stats.receipts_count)
    _kv_line(doc, "Tashriflar" if lang == "uz" else "Визитов", stats.unique_visits)
    _kv_line(
        doc,
        "O'rtacha chek" if lang == "uz" else "Средний чек",
        _money(stats.average_check, lang),
    )

    if stats.by_service:
        doc.add_paragraph()
        h = doc.add_paragraph()
        h.add_run("Xizmatlar bo'yicha" if lang == "uz" else "По услугам").bold = True
        for name, units, revenue in stats.by_service:
            doc.add_paragraph(f"• {name}: {units} × — {_money(revenue, lang)}")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# ----- helpers ---------------------------------------------------------------


def _kv_line(doc: Any, label: str, value: Any) -> None:
    p = doc.add_paragraph()
    r = p.add_run(f"{label}: ")
    r.bold = True
    p.add_run(str(value))


def _money(value: Decimal | int | float, lang: str) -> str:
    amount = f"{Decimal(value):,.0f}".replace(",", " ")
    suffix = "so'm" if lang == "uz" else "сум"
    return f"{amount} {suffix}"


def user_template_exists() -> bool:
    """Convenience for UI banners: does the clinic have its own paper template?"""
    return (Path(app_settings.templates_dir) / RECEPTION_TEMPLATE_NAME).is_file()
