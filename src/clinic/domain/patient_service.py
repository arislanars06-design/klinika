"""Domain service for patient search, lookup, and creation."""

from __future__ import annotations

from loguru import logger

from clinic.db.database import session_scope
from clinic.db.repository import PatientRepository
from clinic.domain.dto import PatientDTO, PatientInput
from clinic.infrastructure.validators import (
    validate_birth_year,
    validate_full_name,
    validate_phone,
)


def search(query: str, *, limit: int = 20) -> list[PatientDTO]:
    """Return patients whose ``full_name`` contains ``query`` (case-insensitive)."""
    if not query or len(query.strip()) < 2:
        return []
    with session_scope() as session:
        repo = PatientRepository(session)
        rows = repo.search_by_name(query, limit=limit)
        return [PatientDTO.from_orm(p) for p in rows]


def get(patient_id: int) -> PatientDTO | None:
    with session_scope() as session:
        row = PatientRepository(session).get(patient_id)
        return PatientDTO.from_orm(row) if row else None


def find_or_create(data: PatientInput) -> tuple[PatientDTO, bool]:
    """Return an existing patient with the same name+year, or create a new one.

    Runs the standard field validators so callers get consistent errors.
    Second tuple element is ``True`` if the patient was newly created.
    """
    full_name = validate_full_name(data.full_name)
    birth_year = validate_birth_year(data.birth_year)
    phone = validate_phone(data.phone)
    address = (data.address or "").strip() or None

    with session_scope() as session:
        repo = PatientRepository(session)
        existing = repo.find_exact(full_name, birth_year)
        if existing is not None:
            # Update contact info if the user provided fresher values
            updated = False
            if phone and existing.phone != phone:
                existing.phone = phone
                updated = True
            if address and existing.address != address:
                existing.address = address
                updated = True
            if updated:
                repo.touch(existing)
                logger.info("Patient {} touched with new contact info", existing.id)
            return PatientDTO.from_orm(existing), False

        created = repo.create(
            full_name=full_name,
            birth_year=birth_year,
            address=address,
            phone=phone,
        )
        logger.info("Created new patient id={} name={!r}", created.id, full_name)
        return PatientDTO.from_orm(created), True


def update(patient_id: int, data: PatientInput) -> PatientDTO | None:
    """Update mutable patient fields and return the fresh DTO."""
    full_name = validate_full_name(data.full_name)
    birth_year = validate_birth_year(data.birth_year)
    phone = validate_phone(data.phone)
    address = (data.address or "").strip() or None

    with session_scope() as session:
        repo = PatientRepository(session)
        updated = repo.update(
            patient_id,
            full_name=full_name,
            birth_year=birth_year,
            phone=phone,
            address=address,
        )
        return PatientDTO.from_orm(updated) if updated else None


def delete(patient_id: int) -> bool:
    with session_scope() as session:
        return PatientRepository(session).delete(patient_id)
