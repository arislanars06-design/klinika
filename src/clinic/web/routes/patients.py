"""Patients history — list, view, edit, delete, statistics."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from clinic.domain import (
    cashier_service,
    patient_service,
    reception_service,
    stats_service,
)
from clinic.printing import docx_builder
from clinic.web.deps import DbDep, get_lang

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_class=HTMLResponse)
def index(
    request: Request,
    q: str | None = None,
    page: int = 1,
    session: Session = DbDep,
) -> HTMLResponse:
    page = max(1, page)
    limit = 20
    rows, total = patient_service.list_page(
        session, offset=(page - 1) * limit, limit=limit, query=q
    )
    return request.app.state.templates.TemplateResponse(
        request,
        "patients/index.html",
        {
            "lang": get_lang(request),
            "patients": rows,
            "total": total,
            "page": page,
            "limit": limit,
            "q": q or "",
            "flash": request.query_params.get("flash"),
            "current_year": datetime.now().year,
        },
    )


@router.get("/statistics", response_class=HTMLResponse)
def statistics(
    request: Request,
    period: str = "month",
    start_raw: str | None = None,
    end_raw: str | None = None,
    session: Session = DbDep,
) -> HTMLResponse:
    start, end = _resolve_period(period, start_raw, end_raw)
    stats = stats_service.patient_stats(session, start, end)
    return request.app.state.templates.TemplateResponse(
        request,
        "patients/statistics.html",
        {
            "lang": get_lang(request),
            "stats": stats,
            "period": period,
            "start": start,
            "end": end,
        },
    )


@router.get("/statistics/export")
def statistics_export(
    request: Request,
    period: str = "month",
    start_raw: str | None = None,
    end_raw: str | None = None,
    session: Session = DbDep,
) -> Response:
    start, end = _resolve_period(period, start_raw, end_raw)
    stats = stats_service.patient_stats(session, start, end)
    payload = docx_builder.build_patient_stats_docx(stats, start, end, get_lang(request))
    filename = f"bemorlar_stats_{start:%Y%m%d}_{end:%Y%m%d}.docx"
    return Response(
        content=payload,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{patient_id}", response_class=HTMLResponse)
def show(patient_id: int, request: Request, session: Session = DbDep) -> HTMLResponse:
    patient = patient_service.get(session, patient_id)
    if patient is None:
        raise HTTPException(404)
    receptions = reception_service.list_by_patient(session, patient_id)
    payments = cashier_service.list_by_patient(session, patient_id)
    return request.app.state.templates.TemplateResponse(
        request,
        "patients/show.html",
        {
            "lang": get_lang(request),
            "patient": patient,
            "receptions": receptions,
            "payments": payments,
            "payments_total": sum((p.total for p in payments), start=_zero_decimal()),
            "flash": request.query_params.get("flash"),
            "current_year": datetime.now().year,
        },
    )


@router.post("/{patient_id}/delete")
def delete(patient_id: int, request: Request, session: Session = DbDep) -> Response:  # noqa: ARG001
    patient_service.delete(session, patient_id)
    session.commit()
    return RedirectResponse("/patients?flash=deleted", status_code=303)


# ----- helpers ---------------------------------------------------------------


def _resolve_period(period: str, start_raw: str | None, end_raw: str | None) -> tuple[datetime, datetime]:
    if period == "custom" and start_raw and end_raw:
        try:
            s = datetime.combine(date.fromisoformat(start_raw), datetime.min.time())
            e = datetime.combine(date.fromisoformat(end_raw), datetime.max.time())
            return s, e
        except ValueError:
            pass
    return stats_service.period_bounds(period)


def _zero_decimal() -> Any:
    from decimal import Decimal
    return Decimal(0)
