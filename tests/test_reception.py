"""End-to-end tests for the reception (Qabul) flow."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client_with_seed() -> TestClient:
    """A TestClient wired to a fresh DB with one doctor and two services seeded."""
    from clinic.db.database import init_db, session_scope
    from clinic.domain import doctor_service, service_catalog_service

    init_db()
    with session_scope() as session:
        doctor_service.create(session, doctor_service.DoctorInput(full_name="Test Doctor"))
        service_catalog_service.create(
            session,
            service_catalog_service.ServiceInput(name_uz="Konsultatsiya", name_ru="Консультация", price=Decimal(100000)),
        )

    from clinic.web.app import create_app
    return TestClient(create_app())


def test_reception_form_renders(client_with_seed: TestClient) -> None:
    # Bypass first-run splash
    client_with_seed.post("/language/uz", follow_redirects=False)
    resp = client_with_seed.get("/reception")
    assert resp.status_code == 200
    assert "Qabulni boshlash" in resp.text
    assert "F.I.O" in resp.text
    assert "QULOQ" in resp.text  # complaints section header


def test_reception_save_creates_patient_and_reception(client_with_seed: TestClient) -> None:
    client_with_seed.post("/language/uz", follow_redirects=False)
    # Doctor + service IDs are known: 1 and 1 respectively
    resp = client_with_seed.post(
        "/reception",
        data={
            "reception_date": "2025-03-15T10:30",
            "patient_full_name": "Aliyev Ali",
            "patient_birth_year": "1990",
            "patient_address": "Toshkent",
            "patient_phone": "+998900000000",
            "complaints_codes": ["ear_pain", "nose_congestion"],
            "diagnosis": "Rinit",
            "doctor_id": "1",
            "lor_status_text": "Norma",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"].startswith("/patients/")

    # Confirm persistence
    from clinic.db.database import session_scope
    from clinic.db.models import Patient, Reception

    with session_scope() as session:
        patients = session.query(Patient).all()
        receptions = session.query(Reception).all()
        assert len(patients) == 1
        assert patients[0].full_name == "Aliyev Ali"
        assert len(receptions) == 1
        assert receptions[0].diagnosis == "Rinit"
        assert receptions[0].complaints_codes == ["ear_pain", "nose_congestion"]


def test_reception_validation_rejects_empty_complaints(client_with_seed: TestClient) -> None:
    client_with_seed.post("/language/uz", follow_redirects=False)
    resp = client_with_seed.post(
        "/reception",
        data={
            "reception_date": "2025-03-15T10:30",
            "patient_full_name": "Karimov Bekzod",
            "patient_birth_year": "1985",
            "diagnosis": "Otit",
            "doctor_id": "1",
        },
    )
    assert resp.status_code == 422
    # Localized error message appears near the top of the form
    assert "Kamida bitta shikoyat" in resp.text or "хотя бы одну жалобу" in resp.text


def test_htmx_patient_search_returns_matches(client_with_seed: TestClient) -> None:
    # First create a patient
    client_with_seed.post("/language/uz", follow_redirects=False)
    client_with_seed.post(
        "/reception",
        data={
            "reception_date": "2025-03-15T10:30",
            "patient_full_name": "Nazarov Umid",
            "patient_birth_year": "1990",
            "complaints_codes": ["ear_pain"],
            "diagnosis": "Otit",
            "doctor_id": "1",
        },
        follow_redirects=False,
    )

    # Now search should match
    resp = client_with_seed.get("/reception/search-patient?q=Naz")
    assert resp.status_code == 200
    assert "Nazarov Umid" in resp.text


def test_reception_print_returns_docx(client_with_seed: TestClient) -> None:
    client_with_seed.post("/language/uz", follow_redirects=False)
    client_with_seed.post(
        "/reception",
        data={
            "reception_date": "2025-03-15T10:30",
            "patient_full_name": "Xolmatov Sardor",
            "patient_birth_year": "1988",
            "complaints_codes": ["ear_pain"],
            "diagnosis": "Otit media",
            "doctor_id": "1",
            "lor_status_text": "Norma",
        },
        follow_redirects=False,
    )

    resp = client_with_seed.get("/reception/1/print")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert len(resp.content) > 1000  # docx never smaller than a few KB
