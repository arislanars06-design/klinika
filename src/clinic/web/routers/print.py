"""Word download endpoints (reception, receipt, patient stats, cashier stats)."""

from __future__ import annotations

import io
import unicodedata
from datetime import date
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
from clinic.printing.docx_builder import build_reception_document
from clinic.printing.receipt_builder import build_receipt_document
from clinic.printing.stats_export import (
    build_cashier_stats_document,
    build_patient_stats_document,
)
from clinic.web.dependencies import require_login, resolve_language

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
