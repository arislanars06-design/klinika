"""Word download endpoints (reception, receipt, patient stats, cashier stats)."""

from __future__ import annotations

import io
from datetime import date

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


def _stream_doc(doc, filename: str) -> StreamingResponse:
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type=DOCX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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
    return _stream_doc(doc, f"reception_{reception_id}.docx")


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
