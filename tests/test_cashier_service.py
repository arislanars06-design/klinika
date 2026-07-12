"""Tests for :mod:`clinic.domain.cashier_service`."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from clinic.domain import (
    cashier_service,
    doctor_service,
    reception_service,
    service_service,
)
from clinic.domain.dto import (
    CashierItemInput,
    CashierPaymentInput,
    PatientInput,
    ReceptionInput,
)
from clinic.infrastructure.validators import ValidationError


@pytest.fixture
def seeded() -> dict:
    """Return a dict with ids of a doctor, a service, a patient, and a reception."""
    doctor = doctor_service.create(full_name="Karimov Ali")
    service = service_service.create(
        name_uz="Konsultatsiya", name_ru="Консультация", price=Decimal("100000")
    )
    other_service = service_service.create(
        name_uz="Audiometriya", name_ru="Аудиометрия", price=Decimal("150000")
    )
    reception, patient, _ = reception_service.save(
        ReceptionInput(
            patient=PatientInput(full_name="Aliyev Anvar", birth_year=1990),
            patient_id=None,
            doctor_id=doctor.id,
            reception_date=datetime(2026, 7, 12, 10, 0),
            complaints_codes=["ear_pain"],
            diagnosis="Otitis media",
        )
    )
    return {
        "doctor_id": doctor.id,
        "service_id": service.id,
        "other_service_id": other_service.id,
        "patient_id": patient.id,
        "reception_id": reception.id,
    }


def test_save_payment_creates_one_row_per_item(seeded: dict) -> None:
    records = cashier_service.save_payment(
        CashierPaymentInput(
            patient_id=seeded["patient_id"],
            reception_id=seeded["reception_id"],
            items=[
                CashierItemInput(service_id=seeded["service_id"], quantity=1),
                CashierItemInput(service_id=seeded["other_service_id"], quantity=2),
            ],
            note="test",
        )
    )
    assert len(records) == 2
    total = sum((r.total for r in records), Decimal("0"))
    assert total == Decimal("400000.00")


def test_save_payment_price_at_moment_captures_current_price(seeded: dict) -> None:
    records = cashier_service.save_payment(
        CashierPaymentInput(
            patient_id=seeded["patient_id"],
            reception_id=seeded["reception_id"],
            items=[CashierItemInput(service_id=seeded["service_id"], quantity=3)],
        )
    )
    assert len(records) == 1
    assert records[0].price_at_moment == Decimal("100000.00")
    assert records[0].total == Decimal("300000.00")
    assert records[0].quantity == 3

    # Now change the service price and confirm existing record didn't change.
    service_service.update(seeded["service_id"], price=Decimal("200000"))
    fresh = cashier_service.list_for_reception(seeded["reception_id"])
    assert fresh[0].price_at_moment == Decimal("100000.00")


def test_save_payment_empty_items_raises(seeded: dict) -> None:
    with pytest.raises(ValidationError) as exc:
        cashier_service.save_payment(
            CashierPaymentInput(
                patient_id=seeded["patient_id"],
                reception_id=seeded["reception_id"],
                items=[],
            )
        )
    assert "items" in exc.value.errors


def test_save_payment_zero_quantity_raises(seeded: dict) -> None:
    with pytest.raises(ValidationError) as exc:
        cashier_service.save_payment(
            CashierPaymentInput(
                patient_id=seeded["patient_id"],
                reception_id=seeded["reception_id"],
                items=[CashierItemInput(service_id=seeded["service_id"], quantity=0)],
            )
        )
    assert any("quantity" in k for k in exc.value.errors)


def test_save_payment_unknown_service_raises(seeded: dict) -> None:
    with pytest.raises(ValidationError):
        cashier_service.save_payment(
            CashierPaymentInput(
                patient_id=seeded["patient_id"],
                reception_id=seeded["reception_id"],
                items=[CashierItemInput(service_id=9999, quantity=1)],
            )
        )


def test_save_payment_unknown_patient_raises(seeded: dict) -> None:
    with pytest.raises(ValidationError):
        cashier_service.save_payment(
            CashierPaymentInput(
                patient_id=9999,
                reception_id=None,
                items=[CashierItemInput(service_id=seeded["service_id"], quantity=1)],
            )
        )


def test_save_payment_without_reception(seeded: dict) -> None:
    records = cashier_service.save_payment(
        CashierPaymentInput(
            patient_id=seeded["patient_id"],
            reception_id=None,
            items=[CashierItemInput(service_id=seeded["service_id"], quantity=1)],
        )
    )
    assert records[0].reception_id is None


def test_total_for_reception(seeded: dict) -> None:
    cashier_service.save_payment(
        CashierPaymentInput(
            patient_id=seeded["patient_id"],
            reception_id=seeded["reception_id"],
            items=[
                CashierItemInput(service_id=seeded["service_id"], quantity=1),
                CashierItemInput(service_id=seeded["other_service_id"], quantity=1),
            ],
        )
    )
    assert cashier_service.total_for_reception(seeded["reception_id"]) == Decimal(
        "250000.00"
    )


def test_delete(seeded: dict) -> None:
    records = cashier_service.save_payment(
        CashierPaymentInput(
            patient_id=seeded["patient_id"],
            reception_id=seeded["reception_id"],
            items=[CashierItemInput(service_id=seeded["service_id"], quantity=1)],
        )
    )
    assert cashier_service.delete(records[0].id) is True
    assert cashier_service.list_for_reception(seeded["reception_id"]) == []
    assert cashier_service.delete(999) is False
