"""Repository layer for the clinic database.

Each repository accepts an active SQLAlchemy ``Session`` so callers control
transaction boundaries via ``session_scope()``. Repositories only speak in ORM
entities — validation and business rules belong in the domain layer.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from clinic.db.models import (
    CashierRecord,
    Doctor,
    Patient,
    Reception,
    Service,
)


def _clean_optional(value: str | None) -> str | None:
    """Return ``None`` for empty/whitespace-only strings, else the stripped value."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


# ============================================================================
# Patients
# ============================================================================


class PatientRepository:
    """CRUD and search helpers for the ``patients`` table."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, patient_id: int) -> Patient | None:
        return self._session.get(Patient, patient_id)

    def add(self, patient: Patient) -> Patient:
        self._session.add(patient)
        self._session.flush()
        return patient

    def create(
        self,
        *,
        full_name: str,
        birth_year: int,
        address: str | None = None,
        phone: str | None = None,
    ) -> Patient:
        patient = Patient(
            full_name=full_name.strip(),
            birth_year=birth_year,
            address=_clean_optional(address),
            phone=_clean_optional(phone),
        )
        return self.add(patient)

    def update(
        self,
        patient_id: int,
        *,
        full_name: str | None = None,
        birth_year: int | None = None,
        address: str | None = None,
        phone: str | None = None,
    ) -> Patient | None:
        patient = self.get(patient_id)
        if patient is None:
            return None
        if full_name is not None:
            patient.full_name = full_name.strip()
        if birth_year is not None:
            patient.birth_year = birth_year
        if address is not None:
            patient.address = _clean_optional(address)
        if phone is not None:
            patient.phone = _clean_optional(phone)
        return patient

    def delete(self, patient_id: int) -> bool:
        patient = self.get(patient_id)
        if patient is None:
            return False
        self._session.delete(patient)
        return True

    def search_by_name(self, query: str, *, limit: int = 20) -> list[Patient]:
        """Case-insensitive prefix/contains search on ``full_name``."""
        query = query.strip()
        if not query:
            return []
        stmt: Select[tuple[Patient]] = (
            select(Patient)
            .where(func.lower(Patient.full_name).like(f"%{query.lower()}%"))
            .order_by(Patient.full_name)
            .limit(limit)
        )
        return list(self._session.execute(stmt).scalars())

    def find_exact(self, full_name: str, birth_year: int) -> Patient | None:
        """Return the unique patient matching name (case-insensitive) and birth year."""
        stmt = select(Patient).where(
            and_(
                func.lower(Patient.full_name) == full_name.strip().lower(),
                Patient.birth_year == birth_year,
            )
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def list_all(self, *, limit: int | None = None) -> list[Patient]:
        stmt = select(Patient).order_by(Patient.full_name)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self._session.execute(stmt).scalars())

    def touch(self, patient: Patient) -> None:
        """Mark the patient as recently updated (used when they attend again)."""
        patient.updated_at = datetime.utcnow()


# ============================================================================
# Doctors
# ============================================================================


class DoctorRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, doctor_id: int) -> Doctor | None:
        return self._session.get(Doctor, doctor_id)

    def list_active(self) -> list[Doctor]:
        stmt = select(Doctor).where(Doctor.is_active.is_(True)).order_by(Doctor.full_name)
        return list(self._session.execute(stmt).scalars())

    def list_all(self) -> list[Doctor]:
        stmt = select(Doctor).order_by(Doctor.is_active.desc(), Doctor.full_name)
        return list(self._session.execute(stmt).scalars())

    def create(self, *, full_name: str, phone: str | None = None) -> Doctor:
        doctor = Doctor(full_name=full_name.strip(), phone=(phone or None))
        self._session.add(doctor)
        self._session.flush()
        return doctor

    def update(
        self,
        doctor_id: int,
        *,
        full_name: str | None = None,
        phone: str | None = None,
        is_active: bool | None = None,
    ) -> Doctor | None:
        doctor = self.get(doctor_id)
        if doctor is None:
            return None
        if full_name is not None:
            doctor.full_name = full_name.strip()
        if phone is not None:
            doctor.phone = phone.strip() or None
        if is_active is not None:
            doctor.is_active = is_active
        return doctor

    def set_active(self, doctor_id: int, is_active: bool) -> Doctor | None:
        """Soft delete/restore helper."""
        return self.update(doctor_id, is_active=is_active)


# ============================================================================
# Services
# ============================================================================


class ServiceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, service_id: int) -> Service | None:
        return self._session.get(Service, service_id)

    def list_active(self) -> list[Service]:
        stmt = select(Service).where(Service.is_active.is_(True)).order_by(Service.name_uz)
        return list(self._session.execute(stmt).scalars())

    def list_all(self) -> list[Service]:
        stmt = select(Service).order_by(Service.is_active.desc(), Service.name_uz)
        return list(self._session.execute(stmt).scalars())

    def create(
        self,
        *,
        name_uz: str,
        name_ru: str,
        price: Decimal,
    ) -> Service:
        service = Service(
            name_uz=name_uz.strip(),
            name_ru=name_ru.strip(),
            price=price,
        )
        self._session.add(service)
        self._session.flush()
        return service

    def update(
        self,
        service_id: int,
        *,
        name_uz: str | None = None,
        name_ru: str | None = None,
        price: Decimal | None = None,
        is_active: bool | None = None,
    ) -> Service | None:
        service = self.get(service_id)
        if service is None:
            return None
        if name_uz is not None:
            service.name_uz = name_uz.strip()
        if name_ru is not None:
            service.name_ru = name_ru.strip()
        if price is not None:
            service.price = price
        if is_active is not None:
            service.is_active = is_active
        return service


# ============================================================================
# Receptions
# ============================================================================


class ReceptionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, reception_id: int) -> Reception | None:
        return self._session.get(Reception, reception_id)

    def add(self, reception: Reception) -> Reception:
        self._session.add(reception)
        self._session.flush()
        return reception

    def list_for_patient(self, patient_id: int) -> list[Reception]:
        stmt = (
            select(Reception)
            .where(Reception.patient_id == patient_id)
            .order_by(Reception.reception_date.desc())
        )
        return list(self._session.execute(stmt).scalars())

    def search(
        self,
        *,
        text: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[Reception]:
        stmt: Select[tuple[Reception]] = select(Reception).join(Reception.patient)

        conditions = []
        if text:
            like = f"%{text.lower()}%"
            conditions.append(
                or_(
                    func.lower(Patient.full_name).like(like),
                    func.lower(Reception.diagnosis).like(like),
                    func.lower(Patient.phone).like(like),
                )
            )
        if date_from is not None:
            conditions.append(Reception.reception_date >= date_from)
        if date_to is not None:
            conditions.append(Reception.reception_date <= date_to)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(Reception.reception_date.desc()).limit(limit).offset(offset)
        return list(self._session.execute(stmt).scalars())


# ============================================================================
# Cashier records
# ============================================================================


class CashierRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: CashierRecord) -> CashierRecord:
        self._session.add(record)
        self._session.flush()
        return record

    def list_for_patient(self, patient_id: int) -> list[CashierRecord]:
        stmt = (
            select(CashierRecord)
            .where(CashierRecord.patient_id == patient_id)
            .order_by(CashierRecord.paid_at.desc())
        )
        return list(self._session.execute(stmt).scalars())

    def list_in_period(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[CashierRecord]:
        stmt = (
            select(CashierRecord)
            .where(and_(CashierRecord.paid_at >= start, CashierRecord.paid_at <= end))
            .order_by(CashierRecord.paid_at.desc())
        )
        return list(self._session.execute(stmt).scalars())


__all__ = [
    "CashierRepository",
    "DoctorRepository",
    "PatientRepository",
    "ReceptionRepository",
    "ServiceRepository",
]
