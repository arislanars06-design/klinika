"""Patient service.

Central place for patient CRUD, dedup, and search. Keeps route handlers thin.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from clinic.db.models import Patient


@dataclass(slots=True)
class PatientInput:
    full_name: str
    birth_year: int
    address: str | None = None
    phone: str | None = None


def _normalize_name(name: str) -> str:
    return " ".join(name.split()).strip()


def get(session: Session, patient_id: int) -> Patient | None:
    return session.get(Patient, patient_id)


def find_by_identity(
    session: Session, full_name: str, birth_year: int
) -> Patient | None:
    """Match on normalized ``full_name`` + ``birth_year`` (case-insensitive)."""
    stmt = select(Patient).where(
        func.lower(Patient.full_name) == _normalize_name(full_name).lower(),
        Patient.birth_year == birth_year,
    )
    return session.execute(stmt).scalar_one_or_none()


def find_or_create(session: Session, data: PatientInput) -> tuple[Patient, bool]:
    """Return ``(patient, created)``. Existing patients get their contact info refreshed."""
    normalized_name = _normalize_name(data.full_name)
    existing = find_by_identity(session, normalized_name, data.birth_year)
    if existing:
        # Keep the freshest address/phone we've seen for this person.
        if data.address:
            existing.address = data.address
        if data.phone:
            existing.phone = data.phone
        session.flush()
        return existing, False

    patient = Patient(
        full_name=normalized_name,
        birth_year=data.birth_year,
        address=data.address,
        phone=data.phone,
    )
    session.add(patient)
    session.flush()
    return patient, True


def search(session: Session, query: str, limit: int = 10) -> Sequence[Patient]:
    """Free-text search across name/phone/address."""
    q = query.strip()
    if not q:
        return []
    like = f"%{q}%"
    stmt = (
        select(Patient)
        .where(
            or_(
                Patient.full_name.ilike(like),
                Patient.phone.ilike(like),
                Patient.address.ilike(like),
            )
        )
        .order_by(Patient.full_name)
        .limit(limit)
    )
    return session.execute(stmt).scalars().all()


def list_page(
    session: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    query: str | None = None,
) -> tuple[Sequence[Patient], int]:
    """Return ``(patients_page, total_count)``."""
    base = select(Patient)
    if query and query.strip():
        like = f"%{query.strip()}%"
        base = base.where(
            or_(
                Patient.full_name.ilike(like),
                Patient.phone.ilike(like),
                Patient.address.ilike(like),
            )
        )

    total = session.execute(
        select(func.count()).select_from(base.subquery())
    ).scalar_one()

    rows = session.execute(
        base.order_by(Patient.updated_at.desc()).offset(offset).limit(limit)
    ).scalars().all()

    return rows, int(total)


def update(session: Session, patient_id: int, data: PatientInput) -> Patient:
    patient = session.get(Patient, patient_id)
    if patient is None:
        raise LookupError(f"Patient {patient_id} not found")
    patient.full_name = _normalize_name(data.full_name)
    patient.birth_year = data.birth_year
    patient.address = data.address
    patient.phone = data.phone
    session.flush()
    return patient


def delete(session: Session, patient_id: int) -> None:
    patient = session.get(Patient, patient_id)
    if patient is None:
        return
    session.delete(patient)
    session.flush()
