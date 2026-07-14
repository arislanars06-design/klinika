"""Statistics dashboards: patient KPIs + cashier KPIs with Chart.js graphs."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request

from clinic.domain import stats_service
from clinic.domain.stats_service import PeriodPreset
from clinic.web.dependencies import render, require_login

router = APIRouter(prefix="/stats")


def _resolve_period(preset: str | None, start: str | None, end: str | None):
    """Build a ``Period`` from query-string arguments.

    ``preset`` wins unless it's ``custom`` and both ``start``/``end`` are set.
    """
    if preset == "custom" and start and end:
        try:
            s = date.fromisoformat(start)
            e = date.fromisoformat(end)
        except ValueError as err:
            raise HTTPException(status_code=400, detail="bad_date") from err
        return stats_service.build_custom(s, e), PeriodPreset.CUSTOM
    if preset in {"today", "week", "month", "year"}:
        return stats_service.build_period(PeriodPreset(preset)), PeriodPreset(preset)
    # default
    return stats_service.build_period(PeriodPreset.MONTH), PeriodPreset.MONTH


@router.get("")
def patient_stats(
    request: Request,
    preset: str | None = "month",
    start: str | None = None,
    end: str | None = None,
    _user: str = Depends(require_login),
):
    from sqlalchemy import func

    from clinic.db.database import session_scope
    from clinic.db.models import Patient, Reception

    period, resolved = _resolve_period(preset, start, end)
    stats = stats_service.patient_stats(period)

    # Per-patient rollup for the window — one row per patient who had at
    # least one reception in the period, with reception count + last visit.
    with session_scope() as session:
        rows = (
            session.query(
                Patient.id,
                Patient.full_name,
                Patient.birth_year,
                Patient.phone,
                func.count(Reception.id).label("reception_count"),
                func.max(Reception.reception_date).label("last_reception_at"),
            )
            .join(Reception, Reception.patient_id == Patient.id)
            .filter(Reception.reception_date >= period.start)
            .filter(Reception.reception_date <= period.end)
            .group_by(Patient.id)
            .order_by(func.max(Reception.reception_date).desc())
            .all()
        )
    period_patients = [
        {
            "id": r.id,
            "full_name": r.full_name,
            "birth_year": r.birth_year,
            "phone": r.phone,
            "reception_count": int(r.reception_count or 0),
            "last_reception_at": r.last_reception_at,
        }
        for r in rows
    ]

    return render(request, "stats/patients.html", {
        "stats": stats,
        "period": period,
        "preset": resolved.value,
        "labels_by_day": [pt.date for pt in stats.by_day],
        "values_by_day": [pt.value for pt in stats.by_day],
        "start_input": period.start.date().isoformat(),
        "end_input": period.end.date().isoformat(),
        "period_patients": period_patients,
    })


@router.get("/cashier")
def cashier_stats(
    request: Request,
    preset: str | None = "month",
    start: str | None = None,
    end: str | None = None,
    _user: str = Depends(require_login),
):
    from decimal import Decimal

    from sqlalchemy import func

    from clinic.db.database import session_scope
    from clinic.db.models import CashierRecord, Patient

    period, resolved = _resolve_period(preset, start, end)
    stats = stats_service.cashier_stats(period)

    # Per-patient rollup for the selected window — the table below the
    # revenue KPI. One row per paying patient with the total they paid.
    with session_scope() as session:
        rows = (
            session.query(
                Patient.id,
                Patient.full_name,
                Patient.birth_year,
                Patient.phone,
                func.coalesce(func.sum(CashierRecord.total), 0).label("paid"),
                func.count(CashierRecord.id).label("lines"),
                func.max(CashierRecord.paid_at).label("last_paid_at"),
            )
            .join(CashierRecord, CashierRecord.patient_id == Patient.id)
            .filter(CashierRecord.paid_at >= period.start)
            .filter(CashierRecord.paid_at <= period.end)
            .group_by(Patient.id)
            .order_by(func.max(CashierRecord.paid_at).desc())
            .all()
        )
    paying_patients = [
        {
            "id": r.id,
            "full_name": r.full_name,
            "birth_year": r.birth_year,
            "phone": r.phone,
            "paid": Decimal(r.paid or 0),
            "lines": int(r.lines or 0),
            "last_paid_at": r.last_paid_at,
        }
        for r in rows
    ]

    return render(request, "stats/cashier.html", {
        "stats": stats,
        "period": period,
        "preset": resolved.value,
        "labels_by_day": [pt.date for pt in stats.by_day],
        "values_by_day": [pt.value for pt in stats.by_day],
        "start_input": period.start.date().isoformat(),
        "end_input": period.end.date().isoformat(),
        "paying_patients": paying_patients,
    })
