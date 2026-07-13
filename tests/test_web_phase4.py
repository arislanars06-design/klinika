"""Phase 4 web UX overhaul — dark theme, general complaints, structured LOR
STATUS, cashier payment types + editable total + quick create, medication
search, doctor phone hint, and settings for theme/save-folder.
"""

from __future__ import annotations

import re
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from clinic.domain import (
    cashier_service,
    catalog_loader,
    clinic_info_service,
    doctor_service,
    patient_service,
    reception_service,
    service_service,
)
from clinic.domain.dto import PatientInput, ReceptionInput
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
# A. Theme (dark/light/auto)
# ---------------------------------------------------------------------------


class TestTheme:
    def test_default_theme_is_light(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/")
        assert resp.status_code == 200
        assert 'data-bs-theme="light"' in resp.text

    def test_switch_to_dark(self, admin_client: TestClient) -> None:
        r = admin_client.get("/theme/dark?next=/", follow_redirects=False)
        assert r.status_code == 303
        r = admin_client.get("/")
        assert 'data-bs-theme="dark"' in r.text

    def test_auto_theme_is_light_data_but_flagged(self, admin_client: TestClient) -> None:
        admin_client.get("/theme/auto?next=/", follow_redirects=False)
        r = admin_client.get("/")
        # ``data-bs-theme`` stays ``light`` (safe fallback for print / server
        # renders) but ``data-clinic-theme`` marks the client-side hook.
        assert 'data-clinic-theme="auto"' in r.text

    def test_invalid_theme_code_is_ignored(self, admin_client: TestClient) -> None:
        r = admin_client.get("/theme/hotpink?next=/", follow_redirects=False)
        assert r.status_code == 303
        assert 'data-bs-theme="light"' in admin_client.get("/").text

    def test_theme_setting_saved_to_clinic_info(self, admin_client: TestClient) -> None:
        admin_client.post(
            "/settings/clinic",
            data={
                "name_uz": "LOR", "name_ru": "ЛОР",
                "address_uz": "", "address_ru": "",
                "phone": "", "logo_path": "",
                "language": "uz",
                "theme": "dark",
                "save_folder": "C:\\Klinika",
            },
            follow_redirects=False,
        )
        info = clinic_info_service.load()
        assert info.theme == "dark"
        assert info.save_folder == "C:\\Klinika"


# ---------------------------------------------------------------------------
# B. Complaints — general section + no emoji
# ---------------------------------------------------------------------------


class TestComplaints:
    def test_catalog_has_general_first(self) -> None:
        cat = catalog_loader.complaints_catalog()
        sections = cat["sections"]
        assert sections[0]["code"] == "general"
        assert len(sections[0]["items"]) == 11

    def test_general_section_items_uz_ru(self) -> None:
        cat = catalog_loader.complaints_catalog()
        general = next(s for s in cat["sections"] if s["code"] == "general")
        expected_uz = {
            "gen_headache", "gen_fever_subfebrile", "gen_fever_febrile",
            "gen_fever_pyretic", "gen_weakness", "gen_dizziness",
            "gen_nausea", "gen_vomiting", "gen_diarrhea",
            "gen_joint_pain", "gen_back_pain",
        }
        codes = {i["code"] for i in general["items"]}
        assert codes == expected_uz
        # Every item has both translations
        for item in general["items"]:
            assert item["uz"] and item["ru"]

    def test_no_emoji_icons_in_sections(self) -> None:
        cat = catalog_loader.complaints_catalog()
        for section in cat["sections"]:
            # We dropped the ``icon`` field entirely for Phase 4
            assert "icon" not in section, f"section {section['code']} still has icon"

    def test_reception_form_shows_general_accordion(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/reception/new")
        assert 'complaints-general' in resp.text
        assert 'gen_headache' in resp.text


# ---------------------------------------------------------------------------
# C. Structured LOR STATUS
# ---------------------------------------------------------------------------


class TestLorStatus:
    def test_lor_status_editor_has_norma_button(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/reception/new")
        assert 'norma-btn' in resp.text
        # NORMA is what the user asked for — the translation should appear.
        assert 'NORMA' in resp.text

    def test_form_field_names_use_structured_prefix(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/reception/new")
        # Structured names look like ``lor__<method>__[<ear>__]<section>__<field>``
        assert re.search(r'name="lor__rhinoscopy__\w+__\w+"', resp.text)
        assert re.search(r'name="lor__otoscopy__AD__\w+__\w+"', resp.text)

    def test_structured_selection_persists_and_composes_text(
        self, admin_client: TestClient
    ) -> None:
        doctor = doctor_service.create(full_name="Nazarov Bek", phone="+998901112233")

        form = {
            "full_name": "Karimova Zulfiya",
            "birth_year": "1988",
            "address": "Sergeli",
            "phone": "+998901234444",
            "patient_id": "",
            "complaints": ["gen_headache", "ear_pain"],
            "diagnosis": "Otit",
            "doctor_id": str(doctor.id),
            # Structured LOR selections
            "lor__rhinoscopy__mucosa__color":     "hyperemic",
            "lor__rhinoscopy__mucosa__moisture":  "dry",
            "lor__otoscopy__AD__tympanic_membrane__color": "hyperemic",
        }
        resp = admin_client.post("/reception/new", data=form, follow_redirects=False)
        assert resp.status_code == 303
        rid = int(resp.headers["location"].rsplit("/", 1)[-1])

        rec = reception_service.get(rid)
        # Structured lor_status: {method[__ear]: {section: {field: value}}}
        assert rec.lor_status is not None
        assert rec.lor_status.get("rhinoscopy", {}).get("mucosa", {}).get("color") == "hyperemic"
        assert (
            rec.lor_status.get("otoscopy__AD", {}).get("tympanic_membrane", {}).get("color")
            == "hyperemic"
        )

        # Detail view should compose that into human-readable text
        detail = admin_client.get(f"/reception/{rid}")
        low = detail.text.lower()
        assert "hyperem" in low or "гиперем" in low or "giperem" in low


# ---------------------------------------------------------------------------
# D. Doctor phone hint on reception form
# ---------------------------------------------------------------------------


def test_reception_form_exposes_doctor_phone_as_data_attr(admin_client: TestClient) -> None:
    doctor_service.create(full_name="Karimov Ali", phone="+998977778899")
    resp = admin_client.get("/reception/new")
    assert 'data-phone="+998977778899"' in resp.text


# ---------------------------------------------------------------------------
# E. Selected complaints live panel — server-side scaffolding is present
# ---------------------------------------------------------------------------


def test_selected_complaints_panel_scaffolding(admin_client: TestClient) -> None:
    resp = admin_client.get("/reception/new")
    assert 'id="selected-complaints-panel"' in resp.text
    assert 'complaint-checkbox' in resp.text
    # Each checkbox carries the localized label for the JS to render
    assert 'data-label="Bosh og' in resp.text  # gen_headache uz


# ---------------------------------------------------------------------------
# F. Patient medication search
# ---------------------------------------------------------------------------


class TestMedicationSearch:
    def test_medication_option_in_search_select(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/patients")
        assert 'value="medication"' in resp.text

    def test_medication_search_finds_patient(self, admin_client: TestClient) -> None:
        doctor = doctor_service.create(full_name="Ismoilov Tolib Kamolovich")
        patient_in = PatientInput(
            full_name="Toshmatov Bekzod",
            birth_year=1975,
            address=None,
            phone=None,
        )
        rec_in = ReceptionInput(
            patient=patient_in,
            patient_id=None,
            doctor_id=doctor.id,
            reception_date=None,  # service fills it
            complaints_codes=["gen_headache"],
            complaints_details={},
            complaints_note=None,
            anamnesis=None,
            lor_status=None,
            diagnosis="Gaymorit",
            recommendation="Amoxicillin 500 mg 3 mahal, 7 kun",
        )
        # ``reception_date`` is required — pass it explicitly.
        from datetime import datetime
        rec_in.reception_date = datetime.utcnow()
        reception_service.save(rec_in)

        resp = admin_client.get("/patients?q=Amoxicillin&search_in=medication")
        assert resp.status_code == 200
        assert "Toshmatov Bekzod" in resp.text


# ---------------------------------------------------------------------------
# G. Cashier — payment types, editable total, quick create
# ---------------------------------------------------------------------------


class TestCashier:
    @pytest.fixture()
    def seeded(self, admin_client: TestClient) -> dict:
        doctor = doctor_service.create(full_name="Karimov Ali")
        s1 = service_service.create(
            name_uz="Konsultatsiya", name_ru="Консультация", price=100_000
        )
        s2 = service_service.create(
            name_uz="Audiometriya", name_ru="Аудиометрия", price=150_000
        )
        # Create patient inline via reception form
        rec_form = {
            "full_name": "Aliyev Anvar",
            "birth_year": "1990",
            "address": "Sergeli",
            "phone": "",
            "patient_id": "",
            "complaints": ["gen_headache"],
            "diagnosis": "Otit",
            "doctor_id": str(doctor.id),
        }
        r = admin_client.post("/reception/new", data=rec_form, follow_redirects=False)
        assert r.status_code == 303
        rid = int(r.headers["location"].rsplit("/", 1)[-1])
        rec = reception_service.get(rid)
        return {
            "doctor_id": doctor.id,
            "service_ids": [s1.id, s2.id],
            "reception_id": rid,
            "patient_id": rec.patient_id,
        }

    def test_patient_page_has_payment_type_selector(
        self, admin_client: TestClient, seeded: dict
    ) -> None:
        resp = admin_client.get(f"/cashier/patient/{seeded['patient_id']}")
        assert 'name="payment_type"' in resp.text
        assert 'value="cash"' in resp.text
        assert 'value="transfer"' in resp.text
        assert 'value="terminal"' in resp.text

    def test_patient_page_has_editable_total(
        self, admin_client: TestClient, seeded: dict
    ) -> None:
        resp = admin_client.get(f"/cashier/patient/{seeded['patient_id']}")
        assert 'name="override_total"' in resp.text

    def test_save_with_transfer_payment_type(
        self, admin_client: TestClient, seeded: dict
    ) -> None:
        r = admin_client.post(
            f"/cashier/patient/{seeded['patient_id']}/save",
            data={
                "service_id": [str(sid) for sid in seeded["service_ids"]],
                "quantity": ["1", "1"],
                "reception_id": str(seeded["reception_id"]),
                "payment_type": "transfer",
                "override_total": "",
            },
            follow_redirects=False,
        )
        assert r.status_code == 303
        history = cashier_service.list_for_patient(seeded["patient_id"])
        assert history
        assert all(rec.payment_type == "transfer" for rec in history)

    def test_override_total_scales_proportionally(
        self, admin_client: TestClient, seeded: dict
    ) -> None:
        # Two services at 100k + 150k = 250k. Override to 200k → each shrinks.
        r = admin_client.post(
            f"/cashier/patient/{seeded['patient_id']}/save",
            data={
                "service_id": [str(sid) for sid in seeded["service_ids"]],
                "quantity": ["1", "1"],
                "reception_id": str(seeded["reception_id"]),
                "payment_type": "cash",
                "override_total": "200000",
            },
            follow_redirects=False,
        )
        assert r.status_code == 303
        history = cashier_service.list_for_patient(seeded["patient_id"])
        assert history
        total = sum(rec.total for rec in history)
        assert Decimal("199.99") < total < Decimal("200000.01")

    def test_invalid_payment_type_defaults_to_cash(
        self, admin_client: TestClient, seeded: dict
    ) -> None:
        r = admin_client.post(
            f"/cashier/patient/{seeded['patient_id']}/save",
            data={
                "service_id": [str(seeded["service_ids"][0])],
                "quantity": ["1"],
                "payment_type": "crypto_or_something",
            },
            follow_redirects=False,
        )
        assert r.status_code == 303
        history = cashier_service.list_for_patient(seeded["patient_id"])
        assert history[0].payment_type == "cash"

    def test_quick_create_makes_patient_and_redirects(
        self, admin_client: TestClient
    ) -> None:
        r = admin_client.post(
            "/cashier/quick",
            data={
                "full_name": "Yusupov Sardor",
                "birth_year": "1992",
                "phone": "+998900001111",
            },
            follow_redirects=False,
        )
        assert r.status_code == 303
        # Should land on that patient's cashier page
        assert re.match(r"/cashier/patient/\d+", r.headers["location"])

        # The patient must actually exist
        matches = patient_service.search("Yusupov Sardor", limit=5)
        assert any(p.full_name == "Yusupov Sardor" for p in matches)

    def test_landing_has_quick_create_button(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/cashier")
        assert 'data-bs-target="#quick-bill-modal"' in resp.text


# ---------------------------------------------------------------------------
# H. Settings for clinic-wide save folder + theme
# ---------------------------------------------------------------------------


def test_settings_clinic_form_has_theme_and_save_folder(admin_client: TestClient) -> None:
    resp = admin_client.get("/settings/clinic")
    assert 'name="theme"' in resp.text
    assert 'name="save_folder"' in resp.text
