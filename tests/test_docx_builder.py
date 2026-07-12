"""Tests for :mod:`clinic.printing.docx_builder`."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from docx import Document

from clinic.domain import doctor_service, reception_service
from clinic.domain.dto import PatientInput, ReceptionInput
from clinic.printing.docx_builder import (
    build_reception_document,
    save_reception_document,
)


@pytest.fixture
def sample() -> dict:
    doc = doctor_service.create(full_name="Karimov Ali", phone="+998901234567")
    reception, patient, _ = reception_service.save(
        ReceptionInput(
            patient=PatientInput(
                full_name="Aliyev Anvar",
                birth_year=1990,
                phone="+998901112233",
                address="Toshkent, Yunusobod",
            ),
            patient_id=None,
            doctor_id=doc.id,
            reception_date=datetime(2026, 7, 12, 10, 30),
            complaints_codes=["ear_pain", "ear_discharge"],
            complaints_details={"ear_discharge": "purulent"},
            complaints_note="3 kundan beri",
            anamnesis="5 kun oldin boshlangan.",
            lor_status={
                "rhinoscopy": {"breathing": {"state": "free"}},
                "otoscopy": {
                    "AS": {
                        "tympanic_membrane": {
                            "color": "hyperemic",
                            "perforation": "central",
                        }
                    }
                },
            },
            diagnosis="Otitis media akuta",
            recommendation="Antibiotik + kompress",
        )
    )
    return {
        "doctor": doctor_service.get(doc.id),
        "reception": reception,
        "patient": patient,
        "clinic": {
            "name_uz": "LOR klinikasi",
            "name_ru": "ЛОР клиника",
            "address_uz": "Toshkent, Yunusobod",
            "address_ru": "Ташкент, Юнусабад",
            "phone": "+998 71 XX XX XX",
        },
    }


def _all_text(doc) -> str:  # type: ignore[no-untyped-def]
    return "\n".join(p.text for p in doc.paragraphs)


def test_reception_default_uz(sample: dict) -> None:
    doc = build_reception_document(
        reception=sample["reception"],
        patient=sample["patient"],
        doctor=sample["doctor"],
        clinic=sample["clinic"],
        lang="uz",
    )
    text = _all_text(doc)
    assert "LOR klinikasi" in text
    assert "QABUL VARAQASI" in text
    assert "Aliyev Anvar" in text
    assert "Otitis media akuta" in text
    assert "quloqda og'riq" in text.lower()
    assert "LOR STATUS" in text


def test_reception_default_ru(sample: dict) -> None:
    doc = build_reception_document(
        reception=sample["reception"],
        patient=sample["patient"],
        doctor=sample["doctor"],
        clinic=sample["clinic"],
        lang="ru",
    )
    text = _all_text(doc)
    assert "ЛОР клиника" in text
    assert "ЛИСТ ПРИЁМА" in text
    assert "ЛОР СТАТУС" in text


def test_reception_omits_optional_sections(sample: dict) -> None:
    """Recommendation/anamnesis are optional — no heading when empty."""
    reception = sample["reception"]
    reception.recommendation = None
    reception.anamnesis = None

    doc = build_reception_document(
        reception=reception,
        patient=sample["patient"],
        doctor=sample["doctor"],
        clinic=sample["clinic"],
        lang="uz",
    )
    text = _all_text(doc)
    # No RECOMMENDATION / ANAMNEZ heading should appear.
    assert "TAVSIYA" not in text
    assert "ANAMNEZ" not in text


def test_save_reception_document_writes_valid_file(
    sample: dict, tmp_path: Path
) -> None:
    dest = tmp_path / "out.docx"
    save_reception_document(
        output_path=dest,
        reception=sample["reception"],
        patient=sample["patient"],
        doctor=sample["doctor"],
        clinic=sample["clinic"],
        lang="uz",
    )
    assert dest.exists()
    # Round-trip: re-open the file.
    doc = Document(str(dest))
    assert any("QABUL VARAQASI" in p.text for p in doc.paragraphs)


def test_reception_with_user_template(sample: dict, tmp_path: Path) -> None:
    """When a template with Jinja placeholders is provided, docxtpl fills it in."""
    # Build a minimal template on the fly.
    template_path = tmp_path / "reception_template.docx"
    tpl = Document()
    tpl.add_paragraph("Custom title: {{ clinic.name }}")
    tpl.add_paragraph("Bemor: {{ patient.full_name }} ({{ patient.age }})")
    tpl.add_paragraph("Tashxis: {{ reception.diagnosis }}")
    tpl.save(str(template_path))

    doc = build_reception_document(
        reception=sample["reception"],
        patient=sample["patient"],
        doctor=sample["doctor"],
        clinic=sample["clinic"],
        lang="uz",
        template_path=template_path,
    )
    text = _all_text(doc)
    # The placeholders should have been substituted, not left literal.
    assert "{{" not in text
    assert "LOR klinikasi" in text
    assert "Aliyev Anvar" in text
    assert "Otitis media akuta" in text


def test_missing_template_falls_back_to_default(sample: dict, tmp_path: Path) -> None:
    ghost = tmp_path / "not_here.docx"
    doc = build_reception_document(
        reception=sample["reception"],
        patient=sample["patient"],
        doctor=sample["doctor"],
        clinic=sample["clinic"],
        lang="uz",
        template_path=ghost,
    )
    text = _all_text(doc)
    # Default header wins.
    assert "QABUL VARAQASI" in text
