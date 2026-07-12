"""Full-flow integration test: seed -> reception -> cashier -> statistics."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    from clinic.db.database import init_db, session_scope
    from clinic.domain import doctor_service, service_catalog_service, settings_service

    init_db()
    settings_service.set_value("clinic_name_uz", "Test klinikasi")
    with session_scope() as session:
        doctor_service.create(session, doctor_service.DoctorInput(full_name="Dr. Test"))
        service_catalog_service.create(
            session,
            service_catalog_service.ServiceInput(name_uz="Konsultatsiya", name_ru="Консультация", price=Decimal(100000)),
        )
        service_catalog_service.create(
            session,
            service_catalog_service.ServiceInput(name_uz="Audiometriya", name_ru="Аудиометрия", price=Decimal(150000)),
        )

    from clinic.web.app import create_app
    c = TestClient(create_app())
    c.post("/language/uz", follow_redirects=False)
    return c


def test_full_reception_to_cashier_flow(client: TestClient) -> None:
    # 1. Save a reception
    resp = client.post(
        "/reception",
        data={
            "reception_date": "2025-03-15T10:30",
            "patient_full_name": "Aliyev Ali",
            "patient_birth_year": "1990",
            "patient_phone": "+998901234567",
            "complaints_codes": ["ear_pain", "ear_discharge"],
            "discharge__ear_discharge": "purulent",
            "diagnosis": "Otit media",
            "doctor_id": "1",
            "lor_status_text": "Norma",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    patient_url = resp.headers["location"]

    # 2. Patient page loads and shows the reception
    resp = client.get(patient_url.split("?")[0])
    assert resp.status_code == 200
    assert "Aliyev Ali" in resp.text
    assert "Otit media" in resp.text

    # 3. Add cashier payment
    resp = client.post(
        "/cashier",
        data={
            "patient_id": "1",
            "reception_id": "1",
            "service_id[]": ["1", "2"],
            "quantity[]": ["1", "1"],
            "note": "sinovdan",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303

    # 4. Payments show on patient page
    resp = client.get("/patients/1")
    assert resp.status_code == 200
    assert "Konsultatsiya" in resp.text
    assert "Audiometriya" in resp.text

    # 5. Patient statistics load
    resp = client.get("/patients/statistics?period=month")
    assert resp.status_code == 200
    assert "1" in resp.text  # at least one reception

    # 6. Cashier statistics load
    resp = client.get("/cashier/statistics?period=month")
    assert resp.status_code == 200

    # 7. Word export downloads
    resp = client.get("/patients/statistics/export?period=month")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/vnd.openxml")
    assert len(resp.content) > 1000


def test_search_finds_saved_patient(client: TestClient) -> None:
    client.post(
        "/reception",
        data={
            "reception_date": "2025-03-15T10:30",
            "patient_full_name": "Karimova Sitora",
            "patient_birth_year": "1985",
            "complaints_codes": ["nose_congestion"],
            "diagnosis": "Rinit",
            "doctor_id": "1",
        },
        follow_redirects=False,
    )
    resp = client.get("/patients?q=Sitora")
    assert resp.status_code == 200
    assert "Karimova Sitora" in resp.text


def test_settings_page_and_updates(client: TestClient) -> None:
    resp = client.get("/settings")
    assert resp.status_code == 200
    assert "Test klinikasi" in resp.text

    resp = client.post(
        "/settings/clinic",
        data={
            "clinic_name_uz": "Yangi klinika",
            "clinic_name_ru": "Новая клиника",
            "clinic_address_uz": "Yangi manzil",
            "clinic_address_ru": "Новый адрес",
            "clinic_phone": "+998 71 111 22 33",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303

    resp = client.get("/settings")
    assert "Yangi klinika" in resp.text


def test_period_bounds_helper() -> None:
    from datetime import date
    from clinic.domain.stats_service import period_bounds

    start, end = period_bounds("today", date(2025, 3, 15))
    assert start.date() == date(2025, 3, 15)
    assert end.date() == date(2025, 3, 15)

    start, end = period_bounds("month", date(2025, 3, 15))
    assert start.date() == date(2025, 3, 1)
    assert end.date() == date(2025, 3, 31)


def test_text_composer_renders_grouped_complaints() -> None:
    from clinic.printing.text_composer import render_complaints

    text = render_complaints(
        codes=["ear_pain", "ear_noise", "nose_congestion", "pharynx_discharge"],
        details={"pharynx_discharge": "purulent"},
        note="3 kundan beri",
        lang="uz",
    )
    assert "QULOQ" in text or "Quloq" in text.upper() or "quloq" in text.lower()
    assert "yiring" in text.lower() or "purulent" in text.lower()
    assert "3 kundan beri" in text
