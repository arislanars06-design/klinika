"""Tests for the structured LOR STATUS flow: form parsing + rendering + preview page."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    from clinic.db.database import init_db, session_scope
    from clinic.domain import doctor_service, service_catalog_service

    init_db()
    with session_scope() as session:
        doctor_service.create(session, doctor_service.DoctorInput(full_name="Dr. Test"))
        service_catalog_service.create(
            session,
            service_catalog_service.ServiceInput(
                name_uz="Konsultatsiya", name_ru="Консультация", price=Decimal(100000)
            ),
        )

    from clinic.web.app import create_app
    c = TestClient(create_app())
    c.post("/language/uz", follow_redirects=False)
    return c


# ---------- server-side parsing --------------------------------------------


def test_parse_lor_status_ignores_empty_and_builds_nested_tree() -> None:
    from starlette.datastructures import FormData

    from clinic.web.routes.reception import _parse_lor_status

    form = FormData(
        [
            ("lor__rhinoscopy__external_nose__state", "deformed"),
            ("lor__rhinoscopy__external_nose__deformity_type[]", "hump"),
            ("lor__rhinoscopy__external_nose__deformity_type[]", "scoliosis"),
            ("lor__rhinoscopy__external_nose__side", "right"),
            ("lor__rhinoscopy__breathing__state", "free"),
            ("lor__rhinoscopy__mucosa__color", ""),  # empty -> should be pruned
            ("lor__otoscopy__AD__tympanic_membrane__color", "pearly_gray"),
            ("lor__otoscopy__AS__tympanic_membrane__perforation", "central"),
            ("lor_status_text", "Manual note"),
        ]
    )

    result = _parse_lor_status(form)

    assert result is not None
    assert result["rhinoscopy"]["external_nose"]["state"] == "deformed"
    assert result["rhinoscopy"]["external_nose"]["deformity_type"] == ["hump", "scoliosis"]
    assert result["rhinoscopy"]["external_nose"]["side"] == "right"
    assert result["rhinoscopy"]["breathing"]["state"] == "free"
    assert "color" not in result["rhinoscopy"].get("mucosa", {})  # empty pruned
    assert result["otoscopy"]["AD"]["tympanic_membrane"]["color"] == "pearly_gray"
    assert result["otoscopy"]["AS"]["tympanic_membrane"]["perforation"] == "central"
    assert result["text"] == "Manual note"


def test_parse_lor_status_returns_none_when_all_empty() -> None:
    from starlette.datastructures import FormData

    from clinic.web.routes.reception import _parse_lor_status

    result = _parse_lor_status(FormData([("lor__rhinoscopy__breathing__state", "")]))
    assert result is None


# ---------- text composer ---------------------------------------------------


def test_render_lor_status_groups_methods_and_labels_options() -> None:
    from clinic.printing.text_composer import render_lor_status

    status = {
        "rhinoscopy": {
            "external_nose": {"state": "deformed", "deformity_type": ["hump"], "side": "right"},
            "breathing": {"state": "free"},
        },
        "otoscopy": {
            "AD": {"tympanic_membrane": {"color": "pearly_gray", "perforation": "none"}},
            "AS": {"tympanic_membrane": {"perforation": "central"}},
        },
        "text": "izoh matni",
    }

    text = render_lor_status(status, lang="uz")

    # Method headers should be present (Uzbek names)
    assert "RINOSKOPIYA" in text
    assert "OTOSKOPIYA" in text

    # Option codes should be humanized
    assert "Deformatsiya" in text or "deformatsiya" in text.lower()
    assert "Bukrilik" in text or "bukrilik" in text.lower()
    assert "O'ngda" in text or "o'ngda" in text.lower()

    # Per-ear otoscopy renders both AD and AS lines
    assert "AD" in text and "AS" in text

    # Free-form tail
    assert "izoh matni" in text


def test_render_lor_status_free_form_only() -> None:
    from clinic.printing.text_composer import render_lor_status

    assert render_lor_status({"text": "Only free-form"}, "uz") == "Only free-form"
    assert render_lor_status({}, "uz") == ""
    assert render_lor_status(None, "uz") == ""


# ---------- end-to-end: form submit + preview -------------------------------


def test_reception_saves_structured_lor_and_preview_renders(client: TestClient) -> None:
    # httpx TestClient only encodes ``data`` as a form when given a mapping.
    # A list-of-tuples argument is treated as raw content, so we pass a dict.
    resp = client.post(
        "/reception",
        data={
            "reception_date": "2025-03-15T10:30",
            "patient_full_name": "Aliyev Ali",
            "patient_birth_year": "1990",
            "patient_address": "Toshkent",
            "complaints_codes": ["ear_pain"],
            "diagnosis": "Otit media",
            "doctor_id": "1",
            "lor__rhinoscopy__external_nose__state": "unchanged",
            "lor__rhinoscopy__breathing__state": "free",
            "lor__otoscopy__AD__tympanic_membrane__color": "pearly_gray",
            "lor__otoscopy__AS__tympanic_membrane__color": "hyperemic",
            "lor__otoscopy__AS__tympanic_membrane__perforation": "central",
            "lor__laryngoscopy__voice__state": "sonorous",
            "lor_status_text": "",  # empty free-form
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303, resp.text[:2000]

    # Reception was persisted with the structured lor_status
    from clinic.db.database import session_scope
    from clinic.db.models import Reception

    with session_scope() as session:
        reception = session.query(Reception).one()
        assert reception.lor_status is not None
        assert reception.lor_status["rhinoscopy"]["external_nose"]["state"] == "unchanged"
        assert reception.lor_status["otoscopy"]["AS"]["tympanic_membrane"]["perforation"] == "central"

    # Preview page renders and includes both AD and AS labels + humanized values
    resp = client.get("/reception/1/preview")
    assert resp.status_code == 200
    text = resp.text
    assert "Aliyev Ali" in text
    assert "Otit media" in text
    assert "AD" in text
    assert "AS" in text
    assert "Jarangdor" in text or "jarangdor" in text.lower()  # laryngoscopy voice=sonorous
    # No-print controls exist so users have both Print and Word buttons
    assert "window.print" in text
    assert "/reception/1/print" in text  # Word download link


def test_phone_field_is_not_in_reception_form(client: TestClient) -> None:
    resp = client.get("/reception")
    assert resp.status_code == 200
    # The phone input's name must not appear anywhere in the reception form now
    assert 'name="patient_phone"' not in resp.text


def test_structured_lor_status_ui_is_rendered_in_form(client: TestClient) -> None:
    resp = client.get("/reception")
    assert resp.status_code == 200
    # Tabs
    assert "RINOSKOPIYA" in resp.text
    assert "FARINGOSKOPIYA" in resp.text
    assert "OTOSKOPIYA" in resp.text
    assert "LARINGOSKOPIYA" in resp.text
    # A structured field name proves the tree is emitted
    assert "lor__rhinoscopy__" in resp.text
    assert "lor__otoscopy__AD__" in resp.text
    assert "lor__otoscopy__AS__" in resp.text
    # Norma button
    assert "Norma" in resp.text or "Норма" in resp.text
