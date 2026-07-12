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
