"""Domain service for doctors (CRUD + soft delete)."""

from __future__ import annotations

from clinic.db.database import session_scope
from clinic.db.repository import DoctorRepository
from clinic.domain.dto import DoctorDTO
from clinic.infrastructure.validators import (
    ValidationError,
    validate_full_name,
    validate_phone,
)


def list_all(*, active_only: bool = False) -> list[DoctorDTO]:
    with session_scope() as session:
        repo = DoctorRepository(session)
        rows = repo.list_active() if active_only else repo.list_all()
        return [DoctorDTO.from_orm(d) for d in rows]


def get(doctor_id: int) -> DoctorDTO | None:
    with session_scope() as session:
        row = DoctorRepository(session).get(doctor_id)
        return DoctorDTO.from_orm(row) if row else None


def create(
    *,
    full_name: str,
    phone: str | None = None,
    save_folder: str | None = None,
) -> DoctorDTO:
    """Validate and persist a new doctor.

    ``save_folder`` is an optional per-doctor override for the clinic-wide
    Word auto-save folder. Empty / whitespace is stored as ``None``.
    """
    errors = ValidationError()
    try:
        name = validate_full_name(full_name)
    except ValidationError as ve:
        errors.errors.update(ve.errors)
        name = full_name  # placeholder for type-checker

    try:
        cleaned_phone = validate_phone(phone)
    except ValidationError as ve:
        errors.errors.update(ve.errors)
        cleaned_phone = None

    if errors:
        raise errors

    folder = (save_folder or "").strip() or None

    with session_scope() as session:
        repo = DoctorRepository(session)
        created = repo.create(
            full_name=name, phone=cleaned_phone, save_folder=folder
        )
        return DoctorDTO.from_orm(created)


# Sentinel that signals "the caller is not touching save_folder" — distinct
# from ``None`` which means "clear it".
_UNSET = object()


def update(
    doctor_id: int,
    *,
    full_name: str | None = None,
    phone: str | None = None,
    is_active: bool | None = None,
    save_folder=_UNSET,
) -> DoctorDTO | None:
    """Update any subset of doctor fields.

    ``phone`` is validated when supplied. ``save_folder`` uses a sentinel
    default so callers can distinguish "leave unchanged" from "clear".
    """
    errors = ValidationError()
    normalized_name: str | None = None
    normalized_phone: str | None = None

    if full_name is not None:
        try:
            normalized_name = validate_full_name(full_name)
        except ValidationError as ve:
            errors.errors.update(ve.errors)

    if phone is not None:
        try:
            normalized_phone = validate_phone(phone)
        except ValidationError as ve:
            errors.errors.update(ve.errors)

    if errors:
        raise errors

    with session_scope() as session:
        repo = DoctorRepository(session)
        row = repo.update(
            doctor_id,
            full_name=normalized_name,
            phone=normalized_phone if phone is not None else None,
            is_active=is_active,
            save_folder=None if save_folder is _UNSET else save_folder,
            save_folder_set=save_folder is not _UNSET,
        )
        return DoctorDTO.from_orm(row) if row else None


def set_active(doctor_id: int, is_active: bool) -> DoctorDTO | None:
    with session_scope() as session:
        row = DoctorRepository(session).set_active(doctor_id, is_active)
        return DoctorDTO.from_orm(row) if row else None


def delete(doctor_id: int) -> bool:
    """Permanently delete a doctor by id. Returns True if deleted."""
    from clinic.db.models import Doctor

    with session_scope() as session:
        doctor = session.get(Doctor, doctor_id)
        if doctor is None:
            return False
        session.delete(doctor)
        return True
