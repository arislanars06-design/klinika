"""Domain service for patient search, lookup, and creation."""

from __future__ import annotations

from datetime import datetime

from loguru import logger

from clinic.db.database import session_scope
from clinic.db.repository import (
    ANY_FIELD_SEARCH,
    CashierRepository,
    PatientRepository,
    PatientSearchField,
    ReceptionRepository,
)
from clinic.domain.dto import (
    CashierRecordDTO,
    PatientDetail,
    PatientDTO,
    PatientHistoryPage,
    PatientInput,
    PatientSummaryDTO,
    ReceptionDTO,
)
from clinic.infrastructure.validators import (
    validate_birth_year,
    validate_full_name,
    validate_phone,
)

PAGE_SIZE_DEFAULT = 20


def search(query: str, *, limit: int = 20) -> list[PatientDTO]:
    """Return patients whose ``full_name`` contains ``query`` (case-insensitive)."""
    if not query or len(query.strip()) < 2:
        return []
    with session_scope() as session:
        repo = PatientRepository(session)
        rows = repo.search_by_name(query, limit=limit)
        return [PatientDTO.from_orm(p) for p in rows]


def paginated_search(
    *,
    text: str | None = None,
    search_in: PatientSearchField = ANY_FIELD_SEARCH,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: int = PAGE_SIZE_DEFAULT,
) -> PatientHistoryPage:
    """Return the paginated patient list for the history screen.

    ``date_from`` / ``date_to`` filter by *last reception* date so the history
    view emphasises recent activity.
    """
    page = max(1, page)
    page_size = max(1, min(200, page_size))
    offset = (page - 1) * page_size

    with session_scope() as session:
        repo = PatientRepository(session)
        rows, total = repo.paginated_search(
            text=text,
            search_in=search_in,
            date_from=date_from,
            date_to=date_to,
            limit=page_size,
            offset=offset,
        )
        last_map = repo.last_reception_map([p.id for p in rows])
        summaries = [
            PatientSummaryDTO(
                patient=PatientDTO.from_orm(p),
                last_reception_date=last_map.get(p.id),
            )
            for p in rows
        ]
        return PatientHistoryPage(
            items=summaries, total=total, page=page, page_size=page_size
        )


def get(patient_id: int) -> PatientDTO | None:
    with session_scope() as session:
        row = PatientRepository(session).get(patient_id)
        return PatientDTO.from_orm(row) if row else None


def get_detail(patient_id: int) -> PatientDetail | None:
    """Load everything the Patient Card dialog needs in a single transaction."""
    with session_scope() as session:
        patient = PatientRepository(session).get(patient_id)
        if patient is None:
            return None
        rec_rows = ReceptionRepository(session).list_for_patient(patient_id)
        cash_rows = CashierRepository(session).list_for_patient(patient_id)
        doctor_names: dict[int, str] = {}
        for r in rec_rows:
            if r.doctor is not None:
                doctor_names[r.doctor_id] = r.doctor.full_name
        return PatientDetail(
            patient=PatientDTO.from_orm(patient),
            receptions=[ReceptionDTO.from_orm(r) for r in rec_rows],
            payments=[CashierRecordDTO.from_orm(c) for c in cash_rows],
            doctor_names=doctor_names,
        )


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
    """Delete the patient and cascade to all receptions/payments."""
    with session_scope() as session:
        if PatientRepository(session).delete(patient_id):
            logger.info("Patient {} deleted (cascade)", patient_id)
            return True
        return False
