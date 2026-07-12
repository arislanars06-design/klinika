"""Cashier — record payments and view revenue statistics."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from loguru import logger
from sqlalchemy.orm import Session

from clinic.domain import (
    cashier_service,
    patient_service,
    reception_service,
    service_catalog_service,
    stats_service,
)
from clinic.printing import docx_builder
from clinic.web.deps import DbDep, get_lang

router = APIRouter(prefix="/cashier", tags=["cashier"])


@router.get("", response_class=HTMLResponse)
def index(
    request: Request,
    patient_id: int | None = None,
    reception_id: int | None = None,
    session: Session = DbDep,
) -> HTMLResponse:
    patient = None
    reception = None
    if reception_id:
        reception = reception_service.get(session, reception_id)
        if reception:
            patient = reception.patient
    elif patient_id:
        patient = patient_service.get(session, patient_id)

    rows, total = cashier_service.list_page(session, limit=10)

    return request.app.state.templates.TemplateResponse(
        request,
        "cashier/index.html",
        {
            "lang": get_lang(request),
            "services": service_catalog_service.list_active(session),
            "patient": patient,
            "reception": reception,
            "recent": rows,
            "recent_total": total,
            "flash": request.query_params.get("flash"),
        },
    )


@router.get("/patient-picker", response_class=HTMLResponse)
def patient_picker(
    request: Request,
    q: str = "",
    session: Session = DbDep,
) -> HTMLResponse:
    matches = patient_service.search(session, q, limit=8) if len(q.strip()) >= 2 else []
    return request.app.state.templates.TemplateResponse(
        request,
        "cashier/_patient_picker.html",
        {"lang": get_lang(request), "matches": matches, "q": q},
    )


@router.post("")
async def save(request: Request, session: Session = DbDep) -> Response:
    form = await request.form()
    try:
        patient_id = int(form.get("patient_id") or 0)
        reception_id_raw = form.get("reception_id")
        reception_id = int(reception_id_raw) if reception_id_raw else None
        service_ids = [int(x) for x in form.getlist("service_id[]") if x]
        quantities = [int(x) for x in form.getlist("quantity[]") if x]
        lines = [
            cashier_service.CashierLine(service_id=sid, quantity=qty)
            for sid, qty in zip(service_ids, quantities, strict=True)
            if qty > 0
        ]
        batch = cashier_service.CashierBatch(
            patient_id=patient_id,
            reception_id=reception_id,
            lines=lines,
            note=(form.get("note") or "").strip() or None,
        )
        records = cashier_service.create_batch(session, batch)
        session.commit()
        logger.info("Saved {} cashier records for patient {}", len(records), patient_id)
    except (cashier_service.CashierValidationError, ValueError) as exc:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return RedirectResponse(f"/patients/{patient_id}?flash=paid", status_code=303)


@router.get("/statistics", response_class=HTMLResponse)
def statistics(
    request: Request,
    period: str = "month",
    start_raw: str | None = None,
    end_raw: str | None = None,
    session: Session = DbDep,
) -> HTMLResponse:
    start, end = _resolve_period(period, start_raw, end_raw)
    stats = stats_service.cashier_stats(session, start, end)
    return request.app.state.templates.TemplateResponse(
        request,
        "cashier/statistics.html",
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
    stats = stats_service.cashier_stats(session, start, end)
    payload = docx_builder.build_cashier_stats_docx(stats, start, end, get_lang(request))
    filename = f"kassa_stats_{start:%Y%m%d}_{end:%Y%m%d}.docx"
    return Response(
        content=payload,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
