"""Phase 6 tests: home KPI simplification, patient delete + date filter,
cashier stats simplification with paying-patients list and delete."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from clinic.domain import (
    cashier_service,
    doctor_service,
    patient_service,
    reception_service,
    service_service,
)
from clinic.domain.dto import (
    CashierItemInput,
    CashierPaymentInput,
    PatientInput,
    ReceptionInput,
)
from clinic.web.app import create_app

ADMIN_USER = "admin"
ADMIN_PASSWORD = "clinic"


@pytest.fixture()
def admin_client() -> TestClient:
    with TestClient(create_app()) as c:
        resp = c.post(
            "/login",
            data={"username": ADMIN_USER, "password": ADMIN_PASSWORD},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        yield c


# ---------------------------------------------------------------------------
# A. Home KPI simplification
# ---------------------------------------------------------------------------


class TestHome:
    def test_home_shows_only_two_kpi_cards(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/")
        assert resp.status_code == 200
        # New: two prominent 'today' cards
        assert 'text-primary">' in resp.text  # patients_today
        assert 'text-success">' in resp.text  # receptions_today
        # Removed: active doctors + active services labels no longer appear
        assert "home.stat_doctors" not in resp.text
        assert "home.stat_services" not in resp.text
        # The Uzbek text for the removed labels
        assert "Faol shifokorlar" not in resp.text
        assert "Faol xizmatlar" not in resp.text


# ---------------------------------------------------------------------------
# B. LOR STATUS layout — three nasopharynx sections moved into pharyngoscopy
# ---------------------------------------------------------------------------


class TestLorLayout:
    def test_pharyngoscopy_owns_nasopharynx_sections(self) -> None:
        from clinic.domain import catalog_loader

        cat = catalog_loader.lor_status_catalog()
        methods = {m["code"]: m for m in cat["methods"]}
        pharyn_codes = {s["code"] for s in methods["pharyngoscopy"]["sections"]}
        rhino_codes = {s["code"] for s in methods["rhinoscopy"]["sections"]}

        for expected in ("posterior_choanae", "posterior_vault", "auditory_tubes"):
            assert expected in pharyn_codes, f"{expected} should be under pharyngoscopy"
            assert expected not in rhino_codes, f"{expected} should NOT still be under rhinoscopy"


# ---------------------------------------------------------------------------
# C. Patient list — date filter + delete
# ---------------------------------------------------------------------------


class TestPatientList:
    def test_date_range_inputs_are_rendered(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/patients")
        assert 'name="date_from"' in resp.text
        assert 'name="date_to"' in resp.text
        assert 'type="date"' in resp.text

    def test_date_filter_narrows_the_list(self, admin_client: TestClient) -> None:
        doctor = doctor_service.create(full_name="Karimov Ali Valiyevich")
        old_patient = PatientInput(full_name="Aliyev Anvar", birth_year=1980,
                                    address=None, phone=None)
        new_patient = PatientInput(full_name="Toshmatov Bekzod", birth_year=1990,
                                    address=None, phone=None)

        # Reception dated 60 days ago
        rec_old = ReceptionInput(
            patient=old_patient, patient_id=None,
            doctor_id=doctor.id,
            reception_date=datetime.utcnow() - timedelta(days=60),
            complaints_codes=["gen_headache"], complaints_details={},
            complaints_note=None, anamnesis=None, lor_status=None,
            diagnosis="Old", recommendation=None,
        )
        reception_service.save(rec_old)

        # Reception dated today
        rec_new = ReceptionInput(
            patient=new_patient, patient_id=None,
            doctor_id=doctor.id,
            reception_date=datetime.utcnow(),
            complaints_codes=["gen_headache"], complaints_details={},
            complaints_note=None, anamnesis=None, lor_status=None,
            diagnosis="New", recommendation=None,
        )
        reception_service.save(rec_new)

        today_iso = datetime.utcnow().date().isoformat()
        # Filter to today only — should show only Toshmatov
        resp = admin_client.get(f"/patients?date_from={today_iso}&date_to={today_iso}")
        assert resp.status_code == 200
        assert "Toshmatov Bekzod" in resp.text
        assert "Aliyev Anvar" not in resp.text

    def test_delete_button_present_in_row(self, admin_client: TestClient) -> None:
        patient_service.find_or_create(PatientInput(
            full_name="Ismoilova Feruza", birth_year=1985,
            address=None, phone=None,
        ))
        resp = admin_client.get("/patients")
        assert '/delete' in resp.text
        assert 'btn-outline-danger' in resp.text

    def test_delete_removes_patient_with_cascade(self, admin_client: TestClient) -> None:
        doctor = doctor_service.create(full_name="Yusupov Botir Karimovich")
        rec_in = ReceptionInput(
            patient=PatientInput(full_name="Delete Me Please", birth_year=1990,
                                  address=None, phone=None),
            patient_id=None, doctor_id=doctor.id,
            reception_date=datetime.utcnow(),
            complaints_codes=["gen_headache"], complaints_details={},
            complaints_note=None, anamnesis=None, lor_status=None,
            diagnosis="Test", recommendation=None,
        )
        rec, patient, _ = reception_service.save(rec_in)
        assert patient_service.get(patient.id) is not None

        resp = admin_client.post(f"/patients/{patient.id}/delete", follow_redirects=False)
        assert resp.status_code == 303

        assert patient_service.get(patient.id) is None
        # Reception cascaded away too
        assert reception_service.get(rec.id) is None

    def test_stats_labels_reflect_selected_range(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/patients?date_from=2026-01-01&date_to=2026-12-31")
        # KPI hint switches to the range phrase
        assert "tanlangan davrda" in resp.text or "выбранный период" in resp.text


# ---------------------------------------------------------------------------
# D. Cashier stats page — simplified + paying-patients list + delete
# ---------------------------------------------------------------------------


class TestCashierStats:
    @pytest.fixture()
    def seeded(self, admin_client: TestClient) -> dict:
        doctor = doctor_service.create(full_name="Karimov Ali")
        svc = service_service.create(name_uz="Konsultatsiya",
                                      name_ru="Консультация", price=100_000)
        patient, _ = patient_service.find_or_create(PatientInput(
            full_name="Rakhimov Timur", birth_year=1985,
            address=None, phone=None,
        ))
        cashier_service.save_payment(CashierPaymentInput(
            patient_id=patient.id, reception_id=None,
            items=[CashierItemInput(service_id=svc.id, quantity=1)],
            note=None, payment_type="cash",
        ))
        return {"patient_id": patient.id, "doctor_id": doctor.id}

    def test_removed_kpi_cards_are_gone(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/stats/cashier")
        assert resp.status_code == 200
        # These translation keys are no longer used on the page
        for key in ("stats.kpi_receipts", "stats.kpi_payments", "stats.kpi_avg"):
            assert key not in resp.text
        # And their Uzbek labels shouldn't appear either
        assert "Cheklar soni" not in resp.text
        assert "Qatorlar soni" not in resp.text
        assert "O&#39;rtacha chek" not in resp.text  # apostrophe encoded

    def test_paying_patients_list_visible(
        self, admin_client: TestClient, seeded: dict
    ) -> None:
        resp = admin_client.get("/stats/cashier?preset=today")
        assert resp.status_code == 200
        assert "Rakhimov Timur" in resp.text
        assert "To&#39;lov qilgan bemorlar" in resp.text or "Оплатившие" in resp.text

    def test_delete_button_present_in_paying_list(
        self, admin_client: TestClient, seeded: dict
    ) -> None:
        resp = admin_client.get("/stats/cashier?preset=today")
        # Delete form is emitted per row
        assert f'/patients/{seeded["patient_id"]}/delete' in resp.text
        assert 'btn-outline-danger' in resp.text

    def test_delete_from_cashier_stats_actually_deletes(
        self, admin_client: TestClient, seeded: dict
    ) -> None:
        r = admin_client.post(
            f"/patients/{seeded['patient_id']}/delete",
            follow_redirects=False,
        )
        assert r.status_code == 303
        assert patient_service.get(seeded["patient_id"]) is None


# ---------------------------------------------------------------------------
# E. "0 so'm" bug fix on cashier cart
# ---------------------------------------------------------------------------


def test_cashier_cart_no_longer_shows_placeholder_zero(admin_client: TestClient) -> None:
    patient, _ = patient_service.find_or_create(PatientInput(
        full_name="Boboyev Otabek", birth_year=1995,
        address=None, phone=None,
    ))
    resp = admin_client.get(f"/cashier/patient/{patient.id}")
    assert resp.status_code == 200
    # Neither the override input nor the subtotal cell renders a stale '0'
    assert 'placeholder="0"' not in resp.text
    # New descriptive helper text now appears
    assert "avtomatik hisoblanadi" in resp.text or "рассчитывается автоматически" in resp.text
