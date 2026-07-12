"""Doctor service.

Doctors are soft-deleted (``is_active=False``) so historical receptions
keep their author reference intact.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from clinic.db.models import Doctor


@dataclass(slots=True)
class DoctorInput:
    full_name: str
    phone: str | None = None


def get(session: Session, doctor_id: int) -> Doctor | None:
    return session.get(Doctor, doctor_id)


def list_active(session: Session) -> Sequence[Doctor]:
    stmt = select(Doctor).where(Doctor.is_active.is_(True)).order_by(Doctor.full_name)
    return session.execute(stmt).scalars().all()


def list_all(session: Session) -> Sequence[Doctor]:
    return session.execute(select(Doctor).order_by(Doctor.full_name)).scalars().all()


def create(session: Session, data: DoctorInput) -> Doctor:
    doctor = Doctor(full_name=data.full_name.strip(), phone=data.phone)
    session.add(doctor)
    session.flush()
    return doctor


def update(session: Session, doctor_id: int, data: DoctorInput) -> Doctor:
    doctor = session.get(Doctor, doctor_id)
    if doctor is None:
        raise LookupError(f"Doctor {doctor_id} not found")
    doctor.full_name = data.full_name.strip()
    doctor.phone = data.phone
    session.flush()
    return doctor


def set_active(session: Session, doctor_id: int, active: bool) -> Doctor:
    doctor = session.get(Doctor, doctor_id)
    if doctor is None:
        raise LookupError(f"Doctor {doctor_id} not found")
    doctor.is_active = active
    session.flush()
    return doctor
