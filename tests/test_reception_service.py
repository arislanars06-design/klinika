"""Tests for :mod:`clinic.domain.reception_service`."""

from __future__ import annotations

from datetime import datetime

import pytest

from clinic.domain import doctor_service, reception_service
from clinic.domain.dto import PatientInput, ReceptionInput
from clinic.infrastructure.validators import ValidationError


def _base_input(doctor_id: int, **overrides) -> ReceptionInput:  # type: ignore[no-untyped-def]
    data = dict(
        patient=PatientInput(full_name="Aliyev Anvar", birth_year=1990),
        patient_id=None,
        doctor_id=doctor_id,
        reception_date=datetime(2026, 7, 12, 10, 0, 0),
        complaints_codes=["ear_pain"],
        complaints_details={},
        complaints_note=None,
        anamnesis="3 kundan beri",
        lor_status=None,
        diagnosis="Otitis media",
        recommendation=None,
    )
    data.update(overrides)
    return ReceptionInput(**data)


def test_save_happy_path_creates_patient_and_reception() -> None:
    doctor = doctor_service.create(full_name="Karimov Ali")
    reception, patient, created = reception_service.save(_base_input(doctor.id))
    assert created is True
    assert reception.id > 0
    assert reception.patient_id == patient.id
    assert reception.doctor_id == doctor.id
    assert reception.diagnosis == "Otitis media"
    assert reception.complaints_codes == ["ear_pain"]


def test_save_reuses_existing_patient() -> None:
    doctor = doctor_service.create(full_name="Karimov Ali")
    r1, p1, created1 = reception_service.save(_base_input(doctor.id))
    r2, p2, created2 = reception_service.save(
        _base_input(doctor.id, diagnosis="Rinit")
    )
    assert created1 is True
    assert created2 is False
    assert p1.id == p2.id
    assert r1.id != r2.id


def test_missing_diagnosis_raises_validation() -> None:
    doctor = doctor_service.create(full_name="Karimov Ali")
    with pytest.raises(ValidationError) as exc:
        reception_service.save(_base_input(doctor.id, diagnosis=""))
    assert "diagnosis" in exc.value.errors


def test_missing_complaints_raises_validation() -> None:
    doctor = doctor_service.create(full_name="Karimov Ali")
    with pytest.raises(ValidationError) as exc:
        reception_service.save(
            _base_input(doctor.id, complaints_codes=[], complaints_note=None)
        )
    assert "complaints" in exc.value.errors


def test_aggregates_multiple_errors() -> None:
    doctor = doctor_service.create(full_name="Karimov Ali")
    with pytest.raises(ValidationError) as exc:
        reception_service.save(
            _base_input(
                doctor.id,
                patient=PatientInput(full_name="A", birth_year=1500),
                diagnosis="",
                complaints_codes=[],
                complaints_note=None,
            )
        )
    keys = set(exc.value.errors)
    assert "full_name" in keys
    assert "birth_year" in keys
    assert "diagnosis" in keys
    assert "complaints" in keys


def test_archived_doctor_rejected() -> None:
    doctor = doctor_service.create(full_name="Karimov Ali")
    doctor_service.set_active(doctor.id, False)
    with pytest.raises(ValidationError) as exc:
        reception_service.save(_base_input(doctor.id))
    assert "doctor" in exc.value.errors


def test_saves_lor_status_json() -> None:
    doctor = doctor_service.create(full_name="Karimov Ali")
    lor = {"rhinoscopy": {"breathing": {"state": "free"}}}
    reception, _, _ = reception_service.save(_base_input(doctor.id, lor_status=lor))
    fresh = reception_service.get(reception.id)
    assert fresh is not None
    assert fresh.lor_status == lor




# ============================================================
# Update + delete
# ============================================================


def test_update_changes_fields() -> None:
    doctor = doctor_service.create(full_name="Karimov Ali")
    reception, patient, _ = reception_service.save(_base_input(doctor.id))

    new_input = _base_input(
        doctor.id,
        patient=PatientInput(
            full_name="Aliyev Anvar", birth_year=1990, phone="+998901112233"
        ),
        patient_id=patient.id,
        diagnosis="Updated diagnosis",
        complaints_codes=["ear_pain", "nose_congestion"],
        complaints_note="new note",
    )
    updated_reception, updated_patient = reception_service.update(reception.id, new_input)
    assert updated_reception.id == reception.id
    assert updated_reception.diagnosis == "Updated diagnosis"
    assert set(updated_reception.complaints_codes) == {"ear_pain", "nose_congestion"}
    assert updated_reception.complaints_note == "new note"
    assert updated_patient.phone == "+998901112233"


def test_update_validation_error_bubbles() -> None:
    doctor = doctor_service.create(full_name="Karimov Ali")
    reception, patient, _ = reception_service.save(_base_input(doctor.id))
    with pytest.raises(ValidationError) as exc:
        reception_service.update(
            reception.id,
            _base_input(doctor.id, patient_id=patient.id, diagnosis=""),
        )
    assert "diagnosis" in exc.value.errors


def test_update_missing_reception_raises() -> None:
    doctor = doctor_service.create(full_name="Karimov Ali")
    with pytest.raises(ValidationError):
        reception_service.update(9999, _base_input(doctor.id))


def test_delete_reception_returns_true() -> None:
    doctor = doctor_service.create(full_name="Karimov Ali")
    reception, _, _ = reception_service.save(_base_input(doctor.id))
    assert reception_service.delete(reception.id) is True
    assert reception_service.get(reception.id) is None
    assert reception_service.delete(reception.id) is False
