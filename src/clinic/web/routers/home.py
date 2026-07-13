"""Home / dashboard route.

The KPIs displayed on the landing page count *today's activity* — this is
what an operator opening the app first thing in the morning wants to see, not
lifetime totals.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Request

from clinic.db.database import session_scope
from clinic.db.models import CashierRecord, Doctor, Reception, Service
from clinic.domain import stats_service
from clinic.web.dependencies import render, require_login

router = APIRouter()


@router.get("/")
def home(request: Request, _user: str = Depends(require_login)):
    from sqlalchemy import func

    today = stats_service.build_period(stats_service.PeriodPreset.TODAY, ref=date.today())

    with session_scope() as session:
        # Reception count = only receptions the doctor recorded today.
        receptions_today = (
            session.query(func.count(Reception.id))
            .filter(Reception.reception_date >= today.start)
            .filter(Reception.reception_date <= today.end)
            .scalar()
            or 0
        )

        # Patient count = distinct patients who have EITHER a reception OR a
        # cashier payment today. Union is done in Python from two subqueries
        # so we don't lean on dialect-specific UNION features.
        reception_patient_ids = {
            pid
            for (pid,) in session.query(Reception.patient_id)
            .filter(Reception.reception_date >= today.start)
            .filter(Reception.reception_date <= today.end)
            .all()
        }
        cashier_patient_ids = {
            pid
            for (pid,) in session.query(CashierRecord.patient_id)
            .filter(CashierRecord.paid_at >= today.start)
            .filter(CashierRecord.paid_at <= today.end)
            .all()
        }
        patients_today = len(reception_patient_ids | cashier_patient_ids)

        doctors = (
            session.query(func.count(Doctor.id))
            .filter(Doctor.is_active.is_(True))
            .scalar()
            or 0
        )
        services = (
            session.query(func.count(Service.id))
            .filter(Service.is_active.is_(True))
            .scalar()
            or 0
        )

    return render(request, "home.html", {
        "stats": {
            "patients_today": patients_today,
            "receptions_today": receptions_today,
            "doctors": doctors,
            "services": services,
        },
    })
