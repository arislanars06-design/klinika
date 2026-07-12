"""Period-based statistics aggregation for the History and Cashier screens.

All queries take a ``(start, end)`` window that the UI computes from a
:class:`PeriodPreset` (today / week / month / year / custom).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from clinic.db.database import session_scope
from clinic.db.repository import CashierRepository, ReceptionRepository
from clinic.domain.dto import (
    CashierStats,
    DayPoint,
    DiagnosisCount,
    PatientStats,
    ServiceRevenue,
)

# ============================================================================
# Period helpers
# ============================================================================


class PeriodPreset(StrEnum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    CUSTOM = "custom"


@dataclass
class Period:
    start: datetime
    end: datetime
    preset: PeriodPreset = PeriodPreset.CUSTOM


def _end_of_day(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, 23, 59, 59)


def _start_of_day(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, 0, 0, 0)


def build_period(preset: PeriodPreset, *, ref: date | None = None) -> Period:
    """Compute a start/end window from a preset relative to ``ref`` (today)."""
    ref = ref or date.today()
    if preset == PeriodPreset.TODAY:
        return Period(_start_of_day(ref), _end_of_day(ref), preset)
    if preset == PeriodPreset.WEEK:
        # Monday of the current week
        monday = ref - timedelta(days=ref.weekday())
        sunday = monday + timedelta(days=6)
        return Period(_start_of_day(monday), _end_of_day(sunday), preset)
    if preset == PeriodPreset.MONTH:
        first = ref.replace(day=1)
        # last day: subtract 1 from first of next month
        next_month = first + timedelta(days=32)
        last = next_month.replace(day=1) - timedelta(days=1)
        return Period(_start_of_day(first), _end_of_day(last), preset)
    if preset == PeriodPreset.YEAR:
        return Period(
            _start_of_day(ref.replace(month=1, day=1)),
            _end_of_day(ref.replace(month=12, day=31)),
            preset,
        )
    # CUSTOM: caller supplies both bounds directly via build_custom below.
    return Period(_start_of_day(ref), _end_of_day(ref), preset)


def build_custom(start: date, end: date) -> Period:
    if end < start:
        start, end = end, start
    return Period(_start_of_day(start), _end_of_day(end), PeriodPreset.CUSTOM)


# ============================================================================
# Patient statistics
# ============================================================================


def patient_stats(period: Period) -> PatientStats:
    """Compute the KPI + chart data for the patient history statistics screen."""
    with session_scope() as session:
        rec_repo = ReceptionRepository(session)
        total_visits = rec_repo.count_in_period(start=period.start, end=period.end)
        distinct_patients = rec_repo.distinct_patients_in_period(
            start=period.start, end=period.end
        )
        new_patients = rec_repo.new_patients_in_period(
            start=period.start, end=period.end
        )
        repeat = max(0, total_visits - new_patients)
        top = rec_repo.top_diagnoses(start=period.start, end=period.end, limit=10)
        by_day = rec_repo.receptions_by_day(start=period.start, end=period.end)

    return PatientStats(
        total_patients=distinct_patients,
        new_patients=new_patients,
        repeat_receptions=repeat,
        top_diagnoses=[DiagnosisCount(d, c) for d, c in top],
        by_day=[DayPoint(date=d, value=float(c)) for d, c in by_day],
    )


# ============================================================================
# Cashier statistics
# ============================================================================


def cashier_stats(period: Period) -> CashierStats:
    with session_scope() as session:
        cash_repo = CashierRepository(session)
        revenue = cash_repo.revenue_in_period(start=period.start, end=period.end)
        payment_count = cash_repo.count_in_period(start=period.start, end=period.end)
        receipts = cash_repo.distinct_receipts_in_period(start=period.start, end=period.end)
        by_service = cash_repo.revenue_by_service(start=period.start, end=period.end)
        by_day = cash_repo.revenue_by_day(start=period.start, end=period.end)

    average = Decimal("0")
    if receipts > 0:
        average = (revenue / Decimal(receipts)).quantize(Decimal("0.01"))

    return CashierStats(
        total_revenue=Decimal(revenue).quantize(Decimal("0.01")),
        payment_count=payment_count,
        receipts_count=receipts,
        average_receipt=average,
        by_service=[
            ServiceRevenue(sid, uz, ru, units, Decimal(rev))
            for sid, uz, ru, units, rev in by_service
        ],
        by_day=[DayPoint(date=d, value=float(v)) for d, v in by_day],
    )


__all__ = [
    "Period",
    "PeriodPreset",
    "build_custom",
    "build_period",
    "cashier_stats",
    "patient_stats",
]
