"""Aggregate statistics for the patients/cashier dashboards.

All functions take an explicit ``[start, end]`` window. Callers use the
``period_bounds`` helper to translate ``today|week|month|year|custom``
into concrete datetimes.
"""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from clinic.db.models import CashierRecord, Patient, Reception, Service


# ----- period helpers --------------------------------------------------------


def period_bounds(period: str, ref: date | None = None) -> tuple[datetime, datetime]:
    """Return an inclusive ``[start, end]`` datetime window for ``period``."""
    ref = ref or date.today()
    if period == "today":
        start = ref
        end = ref
    elif period == "week":
        start = ref - timedelta(days=ref.weekday())
        end = start + timedelta(days=6)
    elif period == "month":
        start = ref.replace(day=1)
        end = ref.replace(day=monthrange(ref.year, ref.month)[1])
    elif period == "year":
        start = ref.replace(month=1, day=1)
        end = ref.replace(month=12, day=31)
    else:
        # Fallback: single day.
        start = ref
        end = ref

    return (
        datetime.combine(start, time.min),
        datetime.combine(end, time.max),
    )


# ----- return types ----------------------------------------------------------


@dataclass(slots=True)
class PatientStats:
    total_receptions: int
    unique_patients: int
    new_patients: int
    returning_receptions: int
    top_diagnoses: list[tuple[str, int]]
    top_complaints: list[tuple[str, int]]


@dataclass(slots=True)
class CashierStats:
    total_revenue: Decimal
    receipts_count: int
    unique_visits: int
    average_check: Decimal
    by_service: list[tuple[str, int, Decimal]]  # (name_uz, units, revenue)


# ----- patient dashboard ----------------------------------------------------


def patient_stats(session: Session, start: datetime, end: datetime) -> PatientStats:
    total = session.execute(
        select(func.count()).select_from(Reception).where(
            Reception.reception_date.between(start, end)
        )
    ).scalar_one() or 0

    unique = session.execute(
        select(func.count(distinct(Reception.patient_id))).where(
            Reception.reception_date.between(start, end)
        )
    ).scalar_one() or 0

    new_patients = session.execute(
        select(func.count()).select_from(Patient).where(
            Patient.created_at.between(start, end)
        )
    ).scalar_one() or 0

    top_diagnoses_rows = session.execute(
        select(Reception.diagnosis, func.count().label("cnt"))
        .where(Reception.reception_date.between(start, end))
        .group_by(Reception.diagnosis)
        .order_by(func.count().desc())
        .limit(10)
    ).all()

    # Complaint codes are stored inside a JSON list, so we unnest them via
    # ``json_each`` (SQLite) — done in Python to stay portable across dialects.
    complaint_counts: dict[str, int] = {}
    rows = session.execute(
        select(Reception.complaints_codes).where(
            Reception.reception_date.between(start, end)
        )
    ).all()
    for (codes,) in rows:
        for code in codes or ():
            complaint_counts[code] = complaint_counts.get(code, 0) + 1
    top_complaints = sorted(
        complaint_counts.items(), key=lambda kv: kv[1], reverse=True
    )[:10]

    return PatientStats(
        total_receptions=int(total),
        unique_patients=int(unique),
        new_patients=int(new_patients),
        returning_receptions=int(total) - int(new_patients),
        top_diagnoses=[(d or "?", int(c)) for d, c in top_diagnoses_rows],
        top_complaints=top_complaints,
    )


# ----- cashier dashboard ----------------------------------------------------


def cashier_stats(session: Session, start: datetime, end: datetime) -> CashierStats:
    total_revenue = session.execute(
        select(func.coalesce(func.sum(CashierRecord.total), 0)).where(
            CashierRecord.paid_at.between(start, end)
        )
    ).scalar_one() or Decimal(0)

    receipts = session.execute(
        select(func.count()).select_from(CashierRecord).where(
            CashierRecord.paid_at.between(start, end)
        )
    ).scalar_one() or 0

    # A "visit" is a distinct (patient, reception) pairing (or (patient, day)
    # if reception_id is NULL). Approximated via distinct patient_id + date.
    unique_visits = session.execute(
        select(
            func.count(
                distinct(
                    func.coalesce(CashierRecord.reception_id, case((CashierRecord.reception_id.is_(None), CashierRecord.patient_id)))
                )
            )
        ).where(CashierRecord.paid_at.between(start, end))
    ).scalar_one() or 0

    avg_check = Decimal(0)
    if unique_visits:
        avg_check = (Decimal(total_revenue) / Decimal(unique_visits)).quantize(Decimal("1.00"))

    by_service_rows = session.execute(
        select(
            Service.name_uz,
            func.sum(CashierRecord.quantity),
            func.sum(CashierRecord.total),
        )
        .join(Service, CashierRecord.service_id == Service.id)
        .where(CashierRecord.paid_at.between(start, end))
        .group_by(Service.id)
        .order_by(func.sum(CashierRecord.total).desc())
    ).all()

    return CashierStats(
        total_revenue=Decimal(total_revenue),
        receipts_count=int(receipts),
        unique_visits=int(unique_visits),
        average_check=avg_check,
        by_service=[(name, int(units), Decimal(rev)) for name, units, rev in by_service_rows],
    )
