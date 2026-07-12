"""Tests for :mod:`clinic.domain.patient_service`."""

from __future__ import annotations

from clinic.domain import patient_service
from clinic.domain.dto import PatientInput


def _make(full_name: str, birth_year: int = 1990, address: str | None = None, phone: str | None = None):
    return PatientInput(
        full_name=full_name,
        birth_year=birth_year,
        address=address,
        phone=phone,
    )


def test_find_or_create_creates_new() -> None:
    patient, created = patient_service.find_or_create(_make("Aliyev Anvar"))
    assert created is True
    assert patient.id > 0
    assert patient.full_name == "Aliyev Anvar"


def test_find_or_create_reuses_by_name_and_year() -> None:
    first, _ = patient_service.find_or_create(_make("Aliyev Anvar", 1985))
    second, created = patient_service.find_or_create(_make("Aliyev Anvar", 1985))
    assert created is False
    assert second.id == first.id


def test_case_insensitive_match() -> None:
    first, _ = patient_service.find_or_create(_make("Aliyev Anvar", 1985))
    second, created = patient_service.find_or_create(_make("aliyev anvar", 1985))
    assert created is False
    assert second.id == first.id


def test_different_year_creates_second_record() -> None:
    a, _ = patient_service.find_or_create(_make("Aliyev Anvar", 1985))
    b, created = patient_service.find_or_create(_make("Aliyev Anvar", 1990))
    assert created is True
    assert a.id != b.id


def test_find_or_create_updates_contact_info() -> None:
    first, _ = patient_service.find_or_create(_make("Aliyev Anvar", 1985))
    assert first.phone is None
    second, _ = patient_service.find_or_create(
        _make("Aliyev Anvar", 1985, phone="+998901112233"),
    )
    assert second.phone == "+998901112233"


def test_search_by_substring() -> None:
    patient_service.find_or_create(_make("Aliyev Anvar"))
    patient_service.find_or_create(_make("Karimov Bekzod"))
    patient_service.find_or_create(_make("Aliyeva Nodira"))

    hits = patient_service.search("Ali")
    assert len(hits) == 2
    assert {p.full_name for p in hits} == {"Aliyev Anvar", "Aliyeva Nodira"}


def test_search_too_short_returns_empty() -> None:
    patient_service.find_or_create(_make("Aliyev Anvar"))
    assert patient_service.search("A") == []




# ============================================================
# Paginated search
# ============================================================


def test_paginated_search_returns_all_patients() -> None:
    patient_service.find_or_create(_make("Aliyev Anvar", 1990))
    patient_service.find_or_create(_make("Karimova Zulfiya", 1985))
    patient_service.find_or_create(_make("Toshmatov Bekzod", 1980))
    page = patient_service.paginated_search(page=1, page_size=10)
    assert page.total == 3
    assert len(page.items) == 3
    assert page.page_count == 1


def test_paginated_search_pagination() -> None:
    # 25 unique alphabetical names so they all pass validate_full_name.
    for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXY"):
        patient_service.find_or_create(_make(f"Testov {letter}ovich Aliyev", 1970 + i))
    page1 = patient_service.paginated_search(page=1, page_size=10)
    assert page1.total == 25
    assert len(page1.items) == 10
    assert page1.page_count == 3

    page3 = patient_service.paginated_search(page=3, page_size=10)
    assert len(page3.items) == 5  # remaining
    assert page3.page == 3


def test_paginated_search_by_text_filters_name() -> None:
    patient_service.find_or_create(_make("Aliyev Anvar"))
    patient_service.find_or_create(_make("Karimova Zulfiya"))
    page = patient_service.paginated_search(text="ali")
    assert page.total == 1
    assert page.items[0].patient.full_name == "Aliyev Anvar"


def test_delete_cascades_to_receptions_and_payments() -> None:
    # This test lives here because it verifies patient_service.delete acts as
    # a cascade — see reception + cashier tests for more focused coverage.
    from datetime import datetime

    from clinic.domain import (
        cashier_service,
        doctor_service,
        reception_service,
        service_service,
    )
    from clinic.domain.dto import (
        CashierItemInput,
        CashierPaymentInput,
        ReceptionInput,
    )

    doctor = doctor_service.create(full_name="Karimov Ali")
    svc = service_service.create(name_uz="A", name_ru="А", price=100)
    reception, patient, _ = reception_service.save(
        ReceptionInput(
            patient=PatientInput(full_name="Aliyev Anvar", birth_year=1990),
            patient_id=None,
            doctor_id=doctor.id,
            reception_date=datetime.now(),
            complaints_codes=["ear_pain"],
            diagnosis="Test",
        )
    )
    cashier_service.save_payment(
        CashierPaymentInput(
            patient_id=patient.id,
            reception_id=reception.id,
            items=[CashierItemInput(service_id=svc.id, quantity=1)],
        )
    )
    assert patient_service.delete(patient.id) is True
    assert reception_service.get(reception.id) is None
    assert cashier_service.list_for_patient(patient.id) == []


def test_get_detail_returns_receptions_and_payments() -> None:
    from datetime import datetime

    from clinic.domain import (
        cashier_service,
        doctor_service,
        reception_service,
        service_service,
    )
    from clinic.domain.dto import (
        CashierItemInput,
        CashierPaymentInput,
        ReceptionInput,
    )

    doctor = doctor_service.create(full_name="Karimov Ali")
    svc = service_service.create(name_uz="A", name_ru="А", price=100)
    reception, patient, _ = reception_service.save(
        ReceptionInput(
            patient=PatientInput(full_name="Aliyev Anvar", birth_year=1990),
            patient_id=None,
            doctor_id=doctor.id,
            reception_date=datetime.now(),
            complaints_codes=["ear_pain"],
            diagnosis="Test",
        )
    )
    cashier_service.save_payment(
        CashierPaymentInput(
            patient_id=patient.id,
            reception_id=reception.id,
            items=[CashierItemInput(service_id=svc.id, quantity=2)],
        )
    )

    detail = patient_service.get_detail(patient.id)
    assert detail is not None
    assert detail.patient.id == patient.id
    assert len(detail.receptions) == 1
    assert len(detail.payments) == 1
    assert detail.total_paid == 200
    assert detail.doctor_names[doctor.id] == "Karimov Ali"


def test_get_detail_missing_returns_none() -> None:
    assert patient_service.get_detail(9999) is None
