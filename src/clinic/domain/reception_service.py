"""Orchestrates saving/updating a patient reception.

Takes a :class:`ReceptionInput`, validates every field together (so the UI can
show all errors at once), then persists both patient and reception in a single
transaction.
"""

from __future__ import annotations

from datetime import datetime

from loguru import logger

from clinic.db.database import session_scope
from clinic.db.models import Reception
from clinic.db.repository import (
    DoctorRepository,
    PatientRepository,
    ReceptionRepository,
)
from clinic.domain.dto import PatientDTO, ReceptionDTO, ReceptionInput
from clinic.infrastructure.validators import (
    ValidationError,
    validate_birth_year,
    validate_complaints,
    validate_diagnosis,
    validate_doctor_selected,
    validate_full_name,
    validate_phone,
)

# ============================================================================
# Read helpers
# ============================================================================


def get(reception_id: int) -> ReceptionDTO | None:
    with session_scope() as session:
        row = ReceptionRepository(session).get(reception_id)
        return ReceptionDTO.from_orm(row) if row else None


def list_for_patient(patient_id: int) -> list[ReceptionDTO]:
    with session_scope() as session:
        rows = ReceptionRepository(session).list_for_patient(patient_id)
        return [ReceptionDTO.from_orm(r) for r in rows]


# ============================================================================
# Save orchestration
# ============================================================================


def _validate_input(data: ReceptionInput) -> tuple[str, int, str | None, str, int]:
    """Run every validator, collecting field errors before raising.

    Returns the normalized ``(full_name, birth_year, phone, diagnosis, doctor_id)``
    tuple on success.
    """
    errors = ValidationError()

    # Patient
    full_name = data.patient.full_name
    try:
        full_name = validate_full_name(full_name, field_name="full_name")
    except ValidationError as ve:
        errors.errors.update(ve.errors)

    birth_year = 0
    try:
        birth_year = validate_birth_year(data.patient.birth_year, field_name="birth_year")
    except ValidationError as ve:
        errors.errors.update(ve.errors)

    phone: str | None = None
    try:
        phone = validate_phone(data.patient.phone, field_name="phone")
    except ValidationError as ve:
        errors.errors.update(ve.errors)

    # Complaints
    try:
        validate_complaints(
            data.complaints_codes,
            data.complaints_note,
            field_name="complaints",
        )
    except ValidationError as ve:
        errors.errors.update(ve.errors)

    # Diagnosis
    diagnosis = ""
    try:
        diagnosis = validate_diagnosis(data.diagnosis, field_name="diagnosis")
    except ValidationError as ve:
        errors.errors.update(ve.errors)

    # Doctor
    doctor_id = 0
    try:
        doctor_id = validate_doctor_selected(data.doctor_id, field_name="doctor")
    except ValidationError as ve:
        errors.errors.update(ve.errors)

    if errors:
        raise errors
    return full_name, birth_year, phone, diagnosis, doctor_id


def save(data: ReceptionInput) -> tuple[ReceptionDTO, PatientDTO, bool]:
    """Persist the reception. Returns ``(reception, patient, patient_created)``.

    - Reuses an existing patient with the same name + birth year.
    - Runs *all* validators together so the UI can highlight every bad field.
    - Wraps the whole thing in a single transaction: partial writes never occur.
    """
    full_name, birth_year, phone, diagnosis, doctor_id = _validate_input(data)
    address = (data.patient.address or "").strip() or None

    with session_scope() as session:
        # Doctor sanity check inside the transaction (the caller could have
        # deleted the doctor between opening the form and saving).
        doctor_repo = DoctorRepository(session)
        doctor = doctor_repo.get(doctor_id)
        if doctor is None or not doctor.is_active:
            err = ValidationError()
            err.add("doctor", "validation.doctor_not_available")
            raise err

        # Patient: prefer the incoming id, else find/create by name+year
        patient_repo = PatientRepository(session)
        patient_created = False
        if data.patient_id is not None:
            patient = patient_repo.get(data.patient_id)
            if patient is None:
                err = ValidationError()
                err.add("patient", "validation.patient_not_found")
                raise err
            # Refresh mutable fields
            patient_repo.update(
                patient.id,
                full_name=full_name,
                birth_year=birth_year,
                phone=phone,
                address=address,
            )
        else:
            existing = patient_repo.find_exact(full_name, birth_year)
            if existing is not None:
                patient = existing
                # Fill in any newly provided contact info without overwriting.
                if phone and existing.phone != phone:
                    existing.phone = phone
                if address and existing.address != address:
                    existing.address = address
                patient_repo.touch(existing)
            else:
                patient = patient_repo.create(
                    full_name=full_name,
                    birth_year=birth_year,
                    address=address,
                    phone=phone,
                )
                patient_created = True

        reception = Reception(
            patient_id=patient.id,
            doctor_id=doctor_id,
            reception_date=data.reception_date or datetime.utcnow(),
            complaints_codes=list(data.complaints_codes),
            complaints_details=dict(data.complaints_details or {}) or None,
            complaints_note=(data.complaints_note or "").strip() or None,
            anamnesis=(data.anamnesis or "").strip() or None,
            lor_status=data.lor_status or None,
            diagnosis=diagnosis,
            recommendation=(data.recommendation or "").strip() or None,
        )
        ReceptionRepository(session).add(reception)

        logger.info(
            "Reception saved: id={} patient={} doctor={} diagnosis={!r}",
            reception.id,
            patient.id,
            doctor_id,
            diagnosis,
        )
        return (
            ReceptionDTO.from_orm(reception),
            PatientDTO.from_orm(patient),
            patient_created,
        )


def update(reception_id: int, data: ReceptionInput) -> tuple[ReceptionDTO, PatientDTO]:
    """Update an existing reception (and its patient) in one transaction."""
    full_name, birth_year, phone, diagnosis, doctor_id = _validate_input(data)
    address = (data.patient.address or "").strip() or None

    with session_scope() as session:
        doctor = DoctorRepository(session).get(doctor_id)
        if doctor is None or not doctor.is_active:
            err = ValidationError()
            err.add("doctor", "validation.doctor_not_available")
            raise err

        rec_repo = ReceptionRepository(session)
        reception = rec_repo.get(reception_id)
        if reception is None:
            err = ValidationError()
            err.add("reception", "validation.patient_not_found")
            raise err

        patient_repo = PatientRepository(session)
        # Update the underlying patient's mutable fields too.
        patient = patient_repo.update(
            reception.patient_id,
            full_name=full_name,
            birth_year=birth_year,
            phone=phone,
            address=address,
        )
        if patient is None:
            err = ValidationError()
            err.add("patient", "validation.patient_not_found")
            raise err

        rec_repo.update_full(
            reception_id,
            doctor_id=doctor_id,
            reception_date=data.reception_date or reception.reception_date,
            complaints_codes=list(data.complaints_codes),
            complaints_details=dict(data.complaints_details or {}) or None,
            complaints_note=(data.complaints_note or "").strip() or None,
            anamnesis=(data.anamnesis or "").strip() or None,
            lor_status=data.lor_status or None,
            diagnosis=diagnosis,
            recommendation=(data.recommendation or "").strip() or None,
        )
        session.flush()
        session.refresh(reception)

        logger.info(
            "Reception updated: id={} patient={} doctor={} diagnosis={!r}",
            reception.id,
            patient.id,
            doctor_id,
            diagnosis,
        )
        return ReceptionDTO.from_orm(reception), PatientDTO.from_orm(patient)


def delete(reception_id: int) -> bool:
    """Delete a single reception (payments linked to it get ``reception_id=NULL``)."""
    with session_scope() as session:
        if ReceptionRepository(session).delete(reception_id):
            logger.info("Reception {} deleted", reception_id)
            return True
        return False


__all__ = ["delete", "get", "list_for_patient", "save", "update"]
