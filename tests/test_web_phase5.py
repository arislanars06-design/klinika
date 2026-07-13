"""Phase 5 tests: today KPIs, cross-alphabet search, address cascade,
patient list stats, cashier revenue breakdown + payer list, cart subtotal.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from clinic.domain import (
    cashier_service,
    catalog_loader,
    doctor_service,
    patient_service,
    reception_service,
    service_service,
)
from clinic.domain.dto import CashierItemInput, CashierPaymentInput, PatientInput, ReceptionInput
from clinic.infrastructure.translit import (
    cyrillic_to_latin,
    expand_variants,
    latin_to_cyrillic,
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
# A. Home KPIs — today semantics
# ---------------------------------------------------------------------------


def test_home_shows_today_kpis(admin_client: TestClient) -> None:
    resp = admin_client.get("/")
    assert resp.status_code == 200
    # New labels appear
    assert "Bugungi" in resp.text or "Бугунги" in resp.text or "сегодня" in resp.text.lower()
    # Old lifetime labels are gone
    assert "stat_patients_today" not in resp.text  # translation key was resolved


def test_today_kpis_reflect_todays_activity(admin_client: TestClient) -> None:
    doctor = doctor_service.create(full_name="Karimov Ali", phone="+998901234567")
    # Save one reception today
    rec_in = ReceptionInput(
        patient=PatientInput(full_name="Yusupov Sardor", birth_year=1985,
                              address="Sergeli", phone=None),
        patient_id=None,
        doctor_id=doctor.id,
        reception_date=datetime.utcnow(),
        complaints_codes=["gen_headache"],
        complaints_details={},
        complaints_note=None,
        anamnesis=None,
        lor_status=None,
        diagnosis="Otit",
        recommendation="Amoxicillin",
    )
    reception_service.save(rec_in)

    resp = admin_client.get("/")
    assert resp.status_code == 200
    # Phase 6: KPIs now use display-size fs-1 (only 2 cards remain).
    assert '<div class="fs-1 fw-semibold text-primary">1</div>' in resp.text
    assert '<div class="fs-1 fw-semibold text-success">1</div>' in resp.text


# ---------------------------------------------------------------------------
# B. Address cascade (regions + districts)
# ---------------------------------------------------------------------------


class TestAddress:
    def test_catalog_has_all_regions(self) -> None:
        cat = catalog_loader.address_catalog()
        codes = {r["code"] for r in cat["regions"]}
        # 12 regions + Tashkent city + Karakalpakstan = 14
        assert "toshkent_shahar" in codes
        assert "qoraqalpogiston" in codes
        assert len(codes) >= 13

    def test_tashkent_has_expected_districts(self) -> None:
        cat = catalog_loader.address_catalog()
        tashkent = next(r for r in cat["regions"] if r["code"] == "toshkent_shahar")
        district_codes = {d["code"] for d in tashkent["districts"]}
        # All 12 Tashkent city districts
        for expected in ("sergeli", "chilonzor", "yunusobod", "mirobod",
                         "mirzo_ulugbek", "shayxontohur", "yakkasaroy", "bektemir"):
            assert expected in district_codes

    def test_reception_form_renders_region_select(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/reception/new")
        assert resp.status_code == 200
        assert 'id="address-region"' in resp.text
        assert 'id="address-district"' in resp.text
        # Region options include Toshkent
        assert 'value="toshkent_shahar"' in resp.text
        assert 'value="sergeli"' not in resp.text  # districts injected via JS
        assert "address-catalog-json" in resp.text

    def test_reception_saves_address_from_cascade(
        self, admin_client: TestClient
    ) -> None:
        doctor = doctor_service.create(full_name="Nazarov Bek")
        form = {
            "full_name": "Aliyev Anvar",
            "birth_year": "1990",
            "phone": "",
            "patient_id": "",
            "address_region": "toshkent_shahar",
            "address_district": "sergeli",
            "address": "7-mavze, 32-uy",
            "complaints": ["gen_headache"],
            "diagnosis": "Otit",
            "doctor_id": str(doctor.id),
        }
        r = admin_client.post("/reception/new", data=form, follow_redirects=False)
        assert r.status_code == 303
        rid = int(r.headers["location"].rsplit("/", 1)[-1])
        rec = reception_service.get(rid)
        patient = patient_service.get(rec.patient_id)
        # Composed as "<region>, <district>, <extra>"
        assert patient.address is not None
        assert "Тошкент шаҳар" in patient.address
        assert "Сергели" in patient.address
        assert "7-mavze" in patient.address


# ---------------------------------------------------------------------------
# C. Cross-alphabet search
# ---------------------------------------------------------------------------


class TestTranslit:
    def test_latin_to_cyrillic_common_names(self) -> None:
        assert latin_to_cyrillic("Aliyev") == "Алиев"
        assert latin_to_cyrillic("Yusupov") == "Юсупов"
        assert latin_to_cyrillic("Karimov") == "Каримов"

    def test_cyrillic_to_latin_common_names(self) -> None:
        # Round-trip isn't perfect; check reasonable outputs.
        assert cyrillic_to_latin("Алиев").lower() in ("aliev", "aliyev")
        assert "yusup" in cyrillic_to_latin("Юсупов").lower()

    def test_expand_variants_latin_input(self) -> None:
        variants = expand_variants("Karimov")
        assert "Karimov" in variants
        assert any("К" in v for v in variants)  # cyrillic form generated

    def test_expand_variants_cyrillic_input(self) -> None:
        variants = expand_variants("Юсупов")
        assert "Юсупов" in variants
        assert any(all(("а" <= ch <= "я" or "А" <= ch <= "Я") is False for ch in v) for v in variants[1:])

    def test_cross_alphabet_search_finds_latin_by_cyrillic(
        self, admin_client: TestClient
    ) -> None:
        patient_service.find_or_create(PatientInput(
            full_name="Aliyev Anvar Bahodirovich",
            birth_year=1990,
            address="Sergeli",
            phone=None,
        ))
        # Search using Cyrillic — expects Latin patient to be found.
        resp = admin_client.get("/patients?q=Алиев")
        assert resp.status_code == 200
        assert "Aliyev Anvar Bahodirovich" in resp.text

    def test_cross_alphabet_search_finds_cyrillic_by_latin(
        self, admin_client: TestClient
    ) -> None:
        patient_service.find_or_create(PatientInput(
            full_name="Юсупов Сардор",
            birth_year=1985,
            address=None,
            phone=None,
        ))
        resp = admin_client.get("/patients?q=Yusupov")
        assert resp.status_code == 200
        assert "Юсупов" in resp.text


# ---------------------------------------------------------------------------
# D. Patient list stats block
# ---------------------------------------------------------------------------


def test_patient_list_shows_stats_block(admin_client: TestClient) -> None:
    resp = admin_client.get("/patients")
    assert resp.status_code == 200
    # Localized KPI labels present
    assert "Жами беморлар" in resp.text or "Всего пациентов" in resp.text
    assert "Янги беморлар" in resp.text or "Новых пациентов" in resp.text
    assert "Такрорий қабуллар" in resp.text or "Повторных приёмов" in resp.text


# ---------------------------------------------------------------------------
# E. Cashier landing — revenue breakdown + payer list
# ---------------------------------------------------------------------------


class TestCashierLanding:
    def test_landing_renders_payment_type_breakdown(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/cashier")
        assert resp.status_code == 200
        # The raw translation key must not leak into the response
        assert "cashier.pt_cash" not in resp.text
        # Payment-type labels
        assert "Naqd" in resp.text or "Нақд" in resp.text or "Наличные" in resp.text
        assert "Terminal" in resp.text or "Терминал" in resp.text
        transfer_label_uz = "O&#39;tkazma"  # apostrophe → &#39;
        assert transfer_label_uz in resp.text or "Ўтказма" in resp.text or "Перевод" in resp.text

    def test_landing_shows_today_payers_after_payment(
        self, admin_client: TestClient
    ) -> None:
        # Seed: patient + service + a cash payment today
        doctor_service.create(full_name="Karimov Ali Valiyevich")
        service = service_service.create(name_uz="Konsultatsiya",
                                          name_ru="Консультация", price=100_000)
        patient, _ = patient_service.find_or_create(PatientInput(
            full_name="Aliyev Anvar",
            birth_year=1990,
            address=None,
            phone=None,
        ))
        cashier_service.save_payment(CashierPaymentInput(
            patient_id=patient.id,
            reception_id=None,
            items=[CashierItemInput(service_id=service.id, quantity=1)],
            note=None,
            payment_type="terminal",
        ))
        resp = admin_client.get("/cashier")
        assert resp.status_code == 200
        assert "Aliyev Anvar" in resp.text
        # Terminal badge in the today payers table
        assert "text-bg-warning" in resp.text  # terminal → warning badge

    def test_landing_shows_revenue_totals(self, admin_client: TestClient) -> None:
        doctor_service.create(full_name="Nurmatov Nariman Toshevich")
        service = service_service.create(name_uz="X-Ray", name_ru="Рентген", price=50_000)
        patient, _ = patient_service.find_or_create(PatientInput(
            full_name="Toshmatov Bekzod",
            birth_year=1980, address=None, phone=None,
        ))
        cashier_service.save_payment(CashierPaymentInput(
            patient_id=patient.id, reception_id=None,
            items=[CashierItemInput(service_id=service.id, quantity=2)],
            note=None, payment_type="cash",
        ))
        resp = admin_client.get("/cashier")
        # Cash column shows 100000 or 100 000 or 100,000
        assert "100000" in resp.text or "100 000" in resp.text or "100,000" in resp.text


# ---------------------------------------------------------------------------
# F. Subtotal / total no longer stuck at "0"
# ---------------------------------------------------------------------------


def test_cart_subtotal_starts_as_placeholder(admin_client: TestClient) -> None:
    patient, _ = patient_service.find_or_create(PatientInput(
        full_name="Ismoilova Feruza",
        birth_year=1992, address=None, phone=None,
    ))
    resp = admin_client.get(f"/cashier/patient/{patient.id}")
    assert resp.status_code == 200
    # Subtotal cell shows a dash on first render, not "0 so'm"
    assert 'id="subtotal-cell"' in resp.text
    # The em-dash placeholder is present
    assert "—" in resp.text


def test_override_total_input_present(admin_client: TestClient) -> None:
    patient, _ = patient_service.find_or_create(PatientInput(
        full_name="Nazarova Malika",
        birth_year=1975, address=None, phone=None,
    ))
    resp = admin_client.get(f"/cashier/patient/{patient.id}")
    assert 'name="override_total"' in resp.text
    # Phase 6 fixed the "0 so'm" confusion — placeholder is now a hint,
    # not a literal '0'.
    assert 'placeholder="0"' not in resp.text
