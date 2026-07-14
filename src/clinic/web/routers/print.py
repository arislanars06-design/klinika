"""Word download endpoints (reception, receipt, patient stats, cashier stats)."""

from __future__ import annotations

import io
import unicodedata
from datetime import date
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from clinic.domain import (
    cashier_service,
    clinic_info_service,
    doctor_service,
    patient_service,
    reception_service,
    stats_service,
)
from clinic.domain.dto import CashierRecordDTO
from clinic.domain.stats_service import PeriodPreset
from clinic.printing.docx_builder import (
    build_reception_context,
    build_reception_document,
)
from clinic.printing.receipt_builder import build_receipt_document
from clinic.printing.stats_export import (
    build_cashier_stats_document,
    build_patient_stats_document,
)
from clinic.web.dependencies import render, require_login, resolve_language

router = APIRouter(prefix="/print")


DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


# ---------------------------------------------------------------------------
# Filename encoding for HTTP headers
# ---------------------------------------------------------------------------
#
# HTTP headers are latin-1 only. RFC 6266 (Content-Disposition) says that
# when the filename contains non-ASCII characters, the server should emit:
#
#     Content-Disposition: attachment;
#       filename="<ASCII-safe fallback>";
#       filename*=UTF-8''<percent-encoded UTF-8>
#
# We build both forms so that legacy clients get a readable name and modern
# browsers use the UTF-8 form for Cyrillic / other scripts.


# Simple Uzbek Cyrillic → Latin transliteration for the ASCII fallback name.
_CYR_TO_LAT = str.maketrans({
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "x", "ч": "ch", "ш": "sh", "ъ": "'", "ы": "i", "ь": "",
    "э": "e", "ю": "yu", "я": "ya", "ў": "o'", "ғ": "g'", "қ": "q", "ҳ": "h",
    "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Е": "E", "Ё": "Yo",
    "Ж": "J", "З": "Z", "И": "I", "Й": "Y", "К": "K", "Л": "L", "М": "M",
    "Н": "N", "О": "O", "П": "P", "Р": "R", "С": "S", "Т": "T", "У": "U",
    "Ф": "F", "Х": "X", "Ч": "Ch", "Ш": "Sh", "Ъ": "'", "Ы": "I", "Ь": "",
    "Э": "E", "Ю": "Yu", "Я": "Ya", "Ў": "O'", "Ғ": "G'", "Қ": "Q", "Ҳ": "H",
})


def _ascii_fallback(name: str) -> str:
    """Return a latin-1-safe rendering of ``name`` for legacy clients.

    Cyrillic characters are transliterated back to Latin Uzbek; any remaining
    non-ASCII cluster is stripped via NFKD decomposition. If the result is
    empty (defensive fallback), returns ``"document"``.
    """
    tr = name.translate(_CYR_TO_LAT)
    normalised = unicodedata.normalize("NFKD", tr)
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii").strip()
    # Backslashes and double quotes would corrupt the filename= parameter.
    ascii_only = ascii_only.replace("\\", "_").replace('"', "'")
    return ascii_only or "document"


def _content_disposition(filename: str) -> str:
    """Build an RFC 6266-compliant ``Content-Disposition`` header value."""
    fallback = _ascii_fallback(filename)
    quoted = quote(filename, safe="")
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quoted}"


def _stream_doc(doc, filename: str) -> StreamingResponse:
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type=DOCX_MIME,
        headers={"Content-Disposition": _content_disposition(filename)},
    )


def _clinic_dict():
    c = clinic_info_service.load()
    return {
        "name_uz": c.name_uz,
        "name_ru": c.name_ru,
        "address_uz": c.address_uz,
        "address_ru": c.address_ru,
        "phone": c.phone,
        "logo_path": c.logo_path,
    }


def _resolve_period(preset: str | None, start: str | None, end: str | None):
    if preset == "custom" and start and end:
        try:
            s = date.fromisoformat(start)
            e = date.fromisoformat(end)
        except ValueError as err:
            raise HTTPException(status_code=400, detail="bad_date") from err
        return stats_service.build_custom(s, e)
    if preset in {"today", "week", "month", "year"}:
        return stats_service.build_period(PeriodPreset(preset))
    return stats_service.build_period(PeriodPreset.MONTH)


@router.get("/reception/{reception_id}.docx")
def print_reception(request: Request, reception_id: int, _user: str = Depends(require_login)):
    rec = reception_service.get(reception_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="reception_not_found")
    patient = patient_service.get(rec.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="patient_not_found")
    doctor = doctor_service.get(rec.doctor_id)

    lang = resolve_language(request)
    doc = build_reception_document(
        reception=rec,
        patient=patient,
        doctor=doctor,
        clinic=_clinic_dict(),
        lang=lang,
    )
    filename = f"{patient.full_name} {patient.birth_year}.docx"
    return _stream_doc(doc, filename)


@router.get("/reception/{reception_id}/preview")
def preview_reception(
    request: Request, reception_id: int, _user: str = Depends(require_login)
):
    """HTML preview of the Word document that will be produced.

    Behavior:
      1. If an uploaded template exists → render the actual reception .docx
         (template + data), convert to HTML via mammoth, embed it in the
         page. What the operator sees IS what Word will show.
      2. If no template is installed → fall back to the programmatic HTML
         layout, driven by the same context dict as the built-in renderer.

    The result is that "Print" on the preview page always matches the
    "Download .docx" output.
    """
    rec = reception_service.get(reception_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="reception_not_found")
    patient = patient_service.get(rec.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="patient_not_found")
    doctor = doctor_service.get(rec.doctor_id)

    lang = resolve_language(request)
    context = build_reception_context(
        reception=rec,
        patient=patient,
        doctor=doctor,
        clinic=_clinic_dict(),
        lang=lang,
    )

    # Try to render the real template as HTML — this is the accurate preview.
    template_html: str | None = None
    try:
        from clinic.domain import template_service

        if template_service.status().exists:
            template_html = _render_template_as_html(
                reception=rec,
                patient=patient,
                doctor=doctor,
                lang=lang,
            )
    except Exception as exc:
        # Any mammoth / rendering error → fall through to the programmatic
        # preview so the operator still gets something useful.
        from loguru import logger
        logger.warning("Template preview failed, falling back to layout preview: {}", exc)
        template_html = None

    return render(request, "reception/print_preview.html", {
        "reception": rec,
        "patient": patient,
        "doctor": doctor,
        "doc_ctx": context,
        "template_html": template_html,
    })


def _render_template_as_html(
    *,
    reception: Any,
    patient: Any,
    doctor: Any,
    lang: str,
) -> str:
    """Render the reception .docx into an HTML fragment for the preview.

    Uses the same builder as the actual download, then converts the result
    to HTML with mammoth so the letterhead, tables, and inline formatting
    from the operator's template are all preserved.
    """
    import io

    import mammoth

    doc = build_reception_document(
        reception=reception,
        patient=patient,
        doctor=doctor,
        clinic=_clinic_dict(),
        lang=lang,
    )
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    result = mammoth.convert_to_html(buf)
    # We deliberately ignore result.messages here — mammoth emits warnings
    # for unmapped styles that don't affect readability of the preview.
    return _polish_template_html(result.value)


# Titles that mark the boundary between the letterhead block and the body
# of the reception document.  Everything before the first occurrence of
# any of these strings is considered "letterhead" and centred; everything
# from that paragraph on keeps its natural left alignment.  Matching is
# case-insensitive and substring-based so localised titles ("QABUL
# VARAQASI", "ЛИСТ ПРИЁМА", etc.) are all recognised.
_LETTERHEAD_STOP_MARKERS = (
    "qabul varaqasi",
    "лист приёма",
    "лист приема",
    "bemor ma'lumotlari",
    "bemor haqida ma'lumot",
    "сведения о пациенте",
)


def _polish_template_html(html: str) -> str:
    """Tidy up mammoth-produced HTML so the letterhead reads cleanly.

    Word documents put logos, QR codes, and stamps at their native pixel
    dimensions — often much larger than a browser preview column, which
    makes the resulting HTML look chaotic (letters wrap to a new line
    beside a giant image, address text shoved off-screen, etc.).

    This helper:

      1. Caps every ``<img>`` at 180x180 CSS pixels via an inline style,
         while preserving aspect ratio.
      2. Marks every ``<p>`` that appears before the reception title (e.g.
         ``QABUL VARAQASI``) with ``class="letterhead-line"`` so the
         template's CSS can centre them.  Word letterheads are almost
         always centred; mammoth doesn't preserve paragraph alignment.

    The transformation is intentionally minimal — anything unrelated to
    those two problems is left exactly as mammoth produced it, so the
    preview still reflects the operator's real template.
    """
    import re

    if not html:
        return html

    # ---- 1. Cap image sizes ------------------------------------------------
    _img_style = (
        "max-width:180px;max-height:180px;width:auto;height:auto;"
        "vertical-align:middle;display:inline-block;"
    )

    def _cap_image(match: "re.Match[str]") -> str:
        tag = match.group(0)
        if 'style="' in tag:
            # Prepend our caps so any inline style from the docx wins on
            # things we don't override (colour, opacity, etc.).
            return re.sub(
                r'style="([^"]*)"',
                lambda m: f'style="{_img_style}{m.group(1)}"',
                tag,
                count=1,
            )
        return tag.replace("<img", f'<img style="{_img_style}"', 1)

    html = re.sub(r"<img\b[^>]*>", _cap_image, html)

    # ---- 2. Centre the letterhead paragraphs -------------------------------
    lowered = html.lower()
    stop_idx = -1
    for marker in _LETTERHEAD_STOP_MARKERS:
        i = lowered.find(marker)
        if i != -1 and (stop_idx == -1 or i < stop_idx):
            stop_idx = i
    if stop_idx > 0:
        # Split at the start of the <p> that contains the stop marker.
        p_open = html.rfind("<p", 0, stop_idx)
        if p_open > 0:
            head, tail = html[:p_open], html[p_open:]
            head = re.sub(
                r"<p(\s+[^>]*)?>",
                lambda m: (
                    '<p class="letterhead-line"'
                    + (m.group(1) or "")
                    + ">"
                    if not m.group(1) or "class=" not in m.group(1)
                    else m.group(0).replace(
                        'class="', 'class="letterhead-line ', 1
                    )
                ),
                head,
            )
            html = head + tail
    return html


# ---------------------------------------------------------------------------
# Receipt (single record OR the receipt-group containing it)
# ---------------------------------------------------------------------------


@router.get("/receipt/{record_id}.docx")
def print_receipt(request: Request, record_id: int, _user: str = Depends(require_login)):
    from clinic.db.database import session_scope
    from clinic.db.repository import CashierRepository

    with session_scope() as session:
        anchor_orm = CashierRepository(session).get(record_id)
        if anchor_orm is None:
            raise HTTPException(status_code=404, detail="record_not_found")
        anchor = CashierRecordDTO.from_orm(anchor_orm)

    # Load every record in the same receipt (matches desktop grouping).
    all_for_patient = cashier_service.list_for_patient(anchor.patient_id)
    same = [
        r for r in all_for_patient
        if r.reception_id == anchor.reception_id
        and abs((r.paid_at - anchor.paid_at).total_seconds()) < 60
    ]
    same = sorted(same, key=lambda r: r.id)
    if not same:
        raise HTTPException(status_code=404, detail="receipt_empty")

    patient = patient_service.get(anchor.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="patient_not_found")

    lang = resolve_language(request)
    doc = build_receipt_document(
        records=same,
        patient=patient,
        clinic=_clinic_dict(),
        lang=lang,
    )
    return _stream_doc(doc, f"receipt_{record_id}.docx")


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


@router.get("/stats/patients.docx")
def print_patient_stats(
    request: Request,
    preset: str | None = "month",
    start: str | None = None,
    end: str | None = None,
    _user: str = Depends(require_login),
):
    period = _resolve_period(preset, start, end)
    stats = stats_service.patient_stats(period)
    lang = resolve_language(request)
    doc = build_patient_stats_document(
        stats=stats,
        period=period,
        clinic=_clinic_dict(),
        lang=lang,
    )
    return _stream_doc(doc, f"patients_{period.start.date()}_{period.end.date()}.docx")


@router.get("/stats/cashier.docx")
def print_cashier_stats(
    request: Request,
    preset: str | None = "month",
    start: str | None = None,
    end: str | None = None,
    _user: str = Depends(require_login),
):
    period = _resolve_period(preset, start, end)
    stats = stats_service.cashier_stats(period)
    lang = resolve_language(request)
    doc = build_cashier_stats_document(
        stats=stats,
        period=period,
        clinic=_clinic_dict(),
        lang=lang,
    )
    return _stream_doc(doc, f"cashier_{period.start.date()}_{period.end.date()}.docx")
