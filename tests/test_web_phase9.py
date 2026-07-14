"""Phase 9 tests: complaints/LOR STATUS CRUD, all-time revenue card,
patient list on stats page, and Word doc Cyrillic labels."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from clinic.domain import (
    cashier_service,
    complaint_catalog_service,
    doctor_service,
    lor_catalog_service,
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
# 1. Complaints custom CRUD
# ---------------------------------------------------------------------------


class TestComplaintsCrud:
    def test_complaints_settings_page_loads(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/settings/complaints")
        assert resp.status_code == 200
        # Section options are present in the create form
        assert 'value="general"' in resp.text
        assert 'value="ear"' in resp.text
        assert 'value="nose"' in resp.text
        assert 'value="pharynx"' in resp.text
        assert 'value="larynx"' in resp.text

    def test_create_complaint_and_appears_in_list(self, admin_client: TestClient) -> None:
        r = admin_client.post(
            "/settings/complaints/new",
            data={
                "section": "ear",
                "name_uz": "Қулоқда ёпишқоқлик",
                "name_ru": "Липкость в ухе",
                "has_discharge_type": "1",
            },
            follow_redirects=False,
        )
        assert r.status_code == 303

        # Row appears on the settings page
        page = admin_client.get("/settings/complaints")
        assert "Қулоқда ёпишқоқлик" in page.text
        assert "Липкость в ухе" in page.text

        # And on the reception form (the merged catalog).
        rec_form = admin_client.get("/reception/new")
        assert rec_form.status_code == 200
        assert "Қулоқда ёпишқоқлик" in rec_form.text

    def test_create_complaint_validation_error(self, admin_client: TestClient) -> None:
        # Empty name_uz → validation error, but response still redirects with flash
        r = admin_client.post(
            "/settings/complaints/new",
            data={"section": "ear", "name_uz": "", "name_ru": ""},
            follow_redirects=False,
        )
        assert r.status_code == 303
        # No custom row was actually created
        assert not complaint_catalog_service.list_custom(active_only=False)

    def test_delete_complaint(self, admin_client: TestClient) -> None:
        created = complaint_catalog_service.create(
            section="nose", name_uz="Аниқ", name_ru="Ясно"
        )
        r = admin_client.post(
            f"/settings/complaints/{created.id}/delete",
            follow_redirects=False,
        )
        assert r.status_code == 303
        assert complaint_catalog_service.get(created.id) is None


# ---------------------------------------------------------------------------
# 2. LOR STATUS custom CRUD
# ---------------------------------------------------------------------------


class TestLorCrud:
    def test_lor_settings_page_loads(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/settings/lor_status")
        assert resp.status_code == 200
        # All four methods available in the picker
        for m in ("rhinoscopy", "pharyngoscopy", "laryngoscopy", "otoscopy"):
            assert f'value="{m}"' in resp.text
        # Field type picker has our expected shapes
        for ft in ("radio", "checkbox", "text", "side", "degree"):
            assert f'value="{ft}"' in resp.text

    def test_create_lor_item_and_appears_in_reception(
        self, admin_client: TestClient
    ) -> None:
        r = admin_client.post(
            "/settings/lor_status/new",
            data={
                "method": "otoscopy",
                "section": "custom_ear_extras",
                "field_type": "radio",
                "label_uz": "Ажралма ранг",
                "label_ru": "Цвет отделяемого",
                "options_raw": "оқ, сариқ, қизил",
            },
            follow_redirects=False,
        )
        assert r.status_code == 303

        # Row appears on the settings list
        listed = lor_catalog_service.list_custom(active_only=False)
        assert len(listed) == 1
        assert listed[0].method == "otoscopy"
        assert listed[0].options and len(listed[0].options) == 3

        # And on the reception form (merged into the catalog)
        rec_form = admin_client.get("/reception/new")
        assert rec_form.status_code == 200
        assert "оқ" in rec_form.text  # one of the option labels

    def test_create_lor_invalid_method_rejected(
        self, admin_client: TestClient
    ) -> None:
        r = admin_client.post(
            "/settings/lor_status/new",
            data={
                "method": "not_a_method",
                "section": "x",
                "field_type": "radio",
                "label_uz": "X",
                "label_ru": "X",
            },
            follow_redirects=False,
        )
        assert r.status_code == 303
        assert not lor_catalog_service.list_custom(active_only=False)


# ---------------------------------------------------------------------------
# 3. Cashier landing — all-time revenue card
# ---------------------------------------------------------------------------


class TestCashierAllTimeCard:
    def test_all_time_card_present_when_empty(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/cashier")
        assert resp.status_code == 200
        # New card label (Cyrillic Uzbek — Russian labels also acceptable)
        assert (
            "ЖАМИ КАССА" in resp.text
            or "ОБЩАЯ КАССА" in resp.text
        )
        # The existing "today" card is still there too.
        assert "Бугунги тушум" in resp.text or "сегодня" in resp.text.lower()

    def test_all_time_revenue_accumulates(self, admin_client: TestClient) -> None:
        # Seed one cash payment
        service = service_service.create(
            name_uz="Konsultatsiya", name_ru="Консультация", price=150_000
        )
        patient, _ = patient_service.find_or_create(PatientInput(
            full_name="All Time Payer",
            birth_year=1980, address=None, phone=None,
        ))
        cashier_service.save_payment(CashierPaymentInput(
            patient_id=patient.id, reception_id=None,
            items=[CashierItemInput(service_id=service.id, quantity=1)],
            note=None, payment_type="cash",
        ))
        resp = admin_client.get("/cashier")
        assert resp.status_code == 200
        # The 150000 total shows up somewhere in the card
        assert "150000" in resp.text or "150 000" in resp.text or "150,000" in resp.text


# ---------------------------------------------------------------------------
# 4. Patient stats page — patient list
# ---------------------------------------------------------------------------


class TestPatientStatsPatientList:
    def test_period_patient_list_renders(self, admin_client: TestClient) -> None:
        doctor = doctor_service.create(full_name="Karimov Ali")
        rec_in = ReceptionInput(
            patient=PatientInput(full_name="Nazarov Bek", birth_year=1990,
                                  address=None, phone=None),
            patient_id=None, doctor_id=doctor.id,
            reception_date=datetime.utcnow(),
            complaints_codes=["gen_headache"], complaints_details={},
            complaints_note=None, anamnesis=None, lor_status=None,
            diagnosis="Otitis", recommendation=None,
        )
        reception_service.save(rec_in)

        resp = admin_client.get("/stats?preset=today")
        assert resp.status_code == 200
        # Section heading appears
        assert (
            "Даврдаги беморлар рўйхати" in resp.text
            or "Пациенты за период" in resp.text
        )
        # Patient row
        assert "Nazarov Bek" in resp.text

    def test_period_patient_list_empty_state(self, admin_client: TestClient) -> None:
        # No receptions at all → shows empty-state row
        resp = admin_client.get("/stats?preset=today")
        assert resp.status_code == 200
        # Empty state uses stats.no_data string
        assert "Маълумот йўқ" in resp.text or "Нет данных" in resp.text
