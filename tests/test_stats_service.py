"""Tests for :mod:`clinic.domain.stats_service`."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from clinic.domain import (
    cashier_service,
    doctor_service,
    reception_service,
    service_service,
    stats_service,
)
from clinic.domain.dto import (
    CashierItemInput,
    CashierPaymentInput,
    PatientInput,
    ReceptionInput,
)
from clinic.domain.stats_service import PeriodPreset

# ============================================================
# Period helpers
# ============================================================


class TestPeriodBuild:
    def test_today(self) -> None:
        ref = date(2026, 7, 12)
        p = stats_service.build_period(PeriodPreset.TODAY, ref=ref)
        assert p.start.date() == ref
        assert p.end.date() == ref
        assert p.end.hour == 23 and p.end.minute == 59

    def test_week_starts_on_monday(self) -> None:
        # 2026-07-12 is a Sunday; Monday of same week is 2026-07-06.
        ref = date(2026, 7, 12)
        p = stats_service.build_period(PeriodPreset.WEEK, ref=ref)
        assert p.start.date() == date(2026, 7, 6)
        assert p.end.date() == date(2026, 7, 12)

    def test_month(self) -> None:
        ref = date(2026, 7, 15)
        p = stats_service.build_period(PeriodPreset.MONTH, ref=ref)
        assert p.start.date() == date(2026, 7, 1)
        assert p.end.date() == date(2026, 7, 31)

    def test_year(self) -> None:
        ref = date(2026, 7, 15)
        p = stats_service.build_period(PeriodPreset.YEAR, ref=ref)
        assert p.start.date() == date(2026, 1, 1)
        assert p.end.date() == date(2026, 12, 31)

    def test_custom_swaps_order(self) -> None:
        p = stats_service.build_custom(date(2026, 8, 1), date(2026, 7, 1))
        assert p.start.date() == date(2026, 7, 1)
        assert p.end.date() == date(2026, 8, 1)


# ============================================================
# Patient statistics
# ============================================================


@pytest.fixture
def seeded_receptions() -> dict:
    """Two patients, three receptions across two days."""
    doctor = doctor_service.create(full_name="Karimov Ali")
    r1, p1, _ = reception_service.save(
        ReceptionInput(
            patient=PatientInput(full_name="Aliyev Anvar", birth_year=1990),
            patient_id=None,
            doctor_id=doctor.id,
            reception_date=datetime(2026, 7, 10, 10, 0),
            complaints_codes=["ear_pain"],
            diagnosis="Otitis media",
        )
    )
    r2, _, _ = reception_service.save(
        ReceptionInput(
            patient=PatientInput(full_name="Aliyev Anvar", birth_year=1990),
            patient_id=p1.id,
            doctor_id=doctor.id,
            reception_date=datetime(2026, 7, 11, 10, 0),
            complaints_codes=["ear_pain"],
            diagnosis="Otitis media",
        )
    )
    r3, p2, _ = reception_service.save(
        ReceptionInput(
            patient=PatientInput(full_name="Karimova Zulfiya", birth_year=1985),
            patient_id=None,
            doctor_id=doctor.id,
            reception_date=datetime(2026, 7, 11, 10, 30),
            complaints_codes=["ear_pain"],
            diagnosis="Rinit",
        )
    )
    return {
        "doctor_id": doctor.id,
        "patient1_id": p1.id,
        "patient2_id": p2.id,
        "receptions": [r1.id, r2.id, r3.id],
    }


def test_patient_stats_basic(seeded_receptions: dict) -> None:
    period = stats_service.build_custom(date(2026, 7, 1), date(2026, 7, 31))
    stats = stats_service.patient_stats(period)
    # 2 distinct patients, both new in July.
    assert stats.total_patients == 2
    assert stats.new_patients == 2
    # 3 total visits, 2 are new-patient first visits → 1 repeat.
    assert stats.repeat_receptions == 1


def test_patient_stats_top_diagnoses(seeded_receptions: dict) -> None:
    period = stats_service.build_custom(date(2026, 7, 1), date(2026, 7, 31))
    stats = stats_service.patient_stats(period)
    top = {(t.diagnosis, t.count) for t in stats.top_diagnoses}
    assert ("Otitis media", 2) in top
    assert ("Rinit", 1) in top


def test_patient_stats_by_day(seeded_receptions: dict) -> None:
    period = stats_service.build_custom(date(2026, 7, 1), date(2026, 7, 31))
    stats = stats_service.patient_stats(period)
    by_day = {pt.date: pt.value for pt in stats.by_day}
    assert by_day.get("2026-07-10") == 1.0
    assert by_day.get("2026-07-11") == 2.0


def test_patient_stats_outside_period_empty(seeded_receptions: dict) -> None:
    period = stats_service.build_custom(date(2026, 6, 1), date(2026, 6, 30))
    stats = stats_service.patient_stats(period)
    assert stats.total_patients == 0
    assert stats.new_patients == 0
    assert stats.repeat_receptions == 0
    assert stats.top_diagnoses == []


# ============================================================
# Cashier statistics
# ============================================================


@pytest.fixture
def seeded_cashier(seeded_receptions: dict) -> dict:
    svc1 = service_service.create(
        name_uz="Konsultatsiya", name_ru="Консультация", price=Decimal("100000")
    )
    svc2 = service_service.create(
        name_uz="Audiometriya", name_ru="Аудиометрия", price=Decimal("150000")
    )
    # Two receipts:
    #   receipt 1 (patient1, reception r1): 1x konsult + 2x audio = 100k + 300k = 400k
    #   receipt 2 (patient2, reception r3): 1x konsult = 100k
    cashier_service.save_payment(
        CashierPaymentInput(
            patient_id=seeded_receptions["patient1_id"],
            reception_id=seeded_receptions["receptions"][0],
            items=[
                CashierItemInput(service_id=svc1.id, quantity=1),
                CashierItemInput(service_id=svc2.id, quantity=2),
            ],
        )
    )
    cashier_service.save_payment(
        CashierPaymentInput(
            patient_id=seeded_receptions["patient2_id"],
            reception_id=seeded_receptions["receptions"][2],
            items=[CashierItemInput(service_id=svc1.id, quantity=1)],
        )
    )
    return {"svc1_id": svc1.id, "svc2_id": svc2.id, **seeded_receptions}


def test_cashier_stats_totals(seeded_cashier: dict) -> None:
    # today because cashier records use current time (paid_at)
    today = date.today()
    period = stats_service.build_custom(today - timedelta(days=1), today + timedelta(days=1))
    stats = stats_service.cashier_stats(period)
    assert stats.total_revenue == Decimal("500000.00")
    assert stats.payment_count == 3  # 2 items + 1 item
    assert stats.receipts_count == 2
    assert stats.average_receipt == Decimal("250000.00")


def test_cashier_stats_by_service(seeded_cashier: dict) -> None:
    today = date.today()
    period = stats_service.build_custom(today - timedelta(days=1), today + timedelta(days=1))
    stats = stats_service.cashier_stats(period)
    by_id = {entry.service_id: entry for entry in stats.by_service}
    assert by_id[seeded_cashier["svc1_id"]].units_sold == 2
    assert by_id[seeded_cashier["svc1_id"]].revenue == Decimal("200000.00")
    assert by_id[seeded_cashier["svc2_id"]].units_sold == 2
    assert by_id[seeded_cashier["svc2_id"]].revenue == Decimal("300000.00")


def test_cashier_stats_empty_period() -> None:
    period = stats_service.build_custom(date(2020, 1, 1), date(2020, 1, 31))
    stats = stats_service.cashier_stats(period)
    assert stats.total_revenue == Decimal("0.00")
    assert stats.payment_count == 0
    assert stats.receipts_count == 0
    assert stats.average_receipt == Decimal("0")
    assert stats.by_service == []
    assert stats.by_day == []
