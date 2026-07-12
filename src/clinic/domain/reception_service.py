"""Reception service.

Wraps create/update/delete of a Reception, together with the transactional
side-effect of finding-or-creating the patient it belongs to.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence

from sqlalchemy import Select, and_, func, select
from sqlalchemy.orm import Session, selectinload

from clinic.db.models import Patient, Reception
from clinic.domain import patient_service


class ReceptionValidationError(ValueError):
    """Raised when a reception form fails validation."""


@dataclass(slots=True)
class ReceptionInput:
    patient: patient_service.PatientInput
    doctor_id: int
    reception_date: datetime
    diagnosis: str
    complaints_codes: list[str] = field(default_factory=list)
    complaints_details: dict[str, str] = field(default_factory=dict)
    complaints_note: str | None = None
    anamnesis: str | None = None
    lor_status: dict | None = None
    recommendation: str | None = None


def validate(data: ReceptionInput) -> list[str]:
    """Return a list of human-readable validation errors (empty if valid)."""
    errors: list[str] = []
    name = data.patient.full_name.strip()
    if len(name) < 5:
        errors.append("validation.name_too_short")
    year = data.patient.birth_year
    current = datetime.now().year
    if year < 1900 or year > current:
        errors.append("validation.year_range")
    if not (data.complaints_codes or (data.complaints_note or "").strip()):
        errors.append("validation.complaints_required")
    if len((data.diagnosis or "").strip()) < 3:
        errors.append("validation.diagnosis_required")
    if not data.doctor_id:
        errors.append("validation.doctor_required")
    return errors


def create(session: Session, data: ReceptionInput) -> Reception:
    errors = validate(data)
    if errors:
        raise ReceptionValidationError(errors)

    patient, _ = patient_service.find_or_create(session, data.patient)
    reception = Reception(
        patient_id=patient.id,
        doctor_id=data.doctor_id,
        reception_date=data.reception_date,
        complaints_codes=data.complaints_codes,
        complaints_details=data.complaints_details or None,
        complaints_note=data.complaints_note or None,
        anamnesis=data.anamnesis or None,
        lor_status=data.lor_status or None,
        diagnosis=data.diagnosis.strip(),
        recommendation=data.recommendation or None,
    )
    session.add(reception)
    session.flush()
    return reception


def update(session: Session, reception_id: int, data: ReceptionInput) -> Reception:
    errors = validate(data)
    if errors:
        raise ReceptionValidationError(errors)
    reception = session.get(Reception, reception_id)
    if reception is None:
        raise LookupError(f"Reception {reception_id} not found")

    # Refresh the linked patient record so contact info stays in sync.
    patient_service.update(session, reception.patient_id, data.patient)

    reception.doctor_id = data.doctor_id
    reception.reception_date = data.reception_date
    reception.complaints_codes = data.complaints_codes
    reception.complaints_details = data.complaints_details or None
    reception.complaints_note = data.complaints_note or None
    reception.anamnesis = data.anamnesis or None
    reception.lor_status = data.lor_status or None
    reception.diagnosis = data.diagnosis.strip()
    reception.recommendation = data.recommendation or None
    session.flush()
    return reception


def delete(session: Session, reception_id: int) -> None:
    reception = session.get(Reception, reception_id)
    if reception is not None:
        session.delete(reception)
        session.flush()


def get(session: Session, reception_id: int) -> Reception | None:
    stmt = (
        select(Reception)
        .options(selectinload(Reception.patient), selectinload(Reception.doctor))
        .where(Reception.id == reception_id)
    )
    return session.execute(stmt).scalar_one_or_none()


def list_by_patient(session: Session, patient_id: int) -> Sequence[Reception]:
    stmt = (
        select(Reception)
        .options(selectinload(Reception.doctor))
        .where(Reception.patient_id == patient_id)
        .order_by(Reception.reception_date.desc())
    )
    return session.execute(stmt).scalars().all()


def list_page(
    session: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    start: datetime | None = None,
    end: datetime | None = None,
) -> tuple[Sequence[Reception], int]:
    base: Select = select(Reception).options(
        selectinload(Reception.patient), selectinload(Reception.doctor)
    )
    conditions = []
    if start:
        conditions.append(Reception.reception_date >= start)
    if end:
        conditions.append(Reception.reception_date <= end)
    if conditions:
        base = base.where(and_(*conditions))

    total = session.execute(
        select(func.count()).select_from(base.subquery())
    ).scalar_one()
    rows = session.execute(
        base.order_by(Reception.reception_date.desc()).offset(offset).limit(limit)
    ).scalars().all()
    return rows, int(total)
