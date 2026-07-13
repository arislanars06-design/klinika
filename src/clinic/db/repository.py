"""Repository layer for the clinic database.

Each repository accepts an active SQLAlchemy ``Session`` so callers control
transaction boundaries via ``session_scope()``. Repositories only speak in ORM
entities — validation and business rules belong in the domain layer.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import NamedTuple

from sqlalchemy import Select, and_, distinct, func, or_, select
from sqlalchemy.orm import Session, joinedload

from clinic.db.models import (
    CashierRecord,
    Doctor,
    Patient,
    Reception,
    Service,
)


class PatientSearchField(NamedTuple):
    """Named tuple describing which fields a patient search should target."""

    full_name: bool = True
    phone: bool = True
    diagnosis: bool = False
    birth_year: bool = False
    # Phase 4: allow searching medications / recommendations text.
    medication: bool = False


ANY_FIELD_SEARCH = PatientSearchField(
    full_name=True, phone=True, diagnosis=True, birth_year=True, medication=True
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

    def paginated_search(
        self,
        *,
        text: str | None = None,
        search_in: PatientSearchField = ANY_FIELD_SEARCH,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Patient], int]:
        """Search patients with pagination + last-reception filtering.

        Returns ``(rows, total_count)``. ``date_from`` / ``date_to`` restrict to
        patients whose *last* reception falls in that range. Text queries can
        target any of full_name / phone / diagnosis / birth_year as configured
        via ``search_in``.
        """
        # Build a subquery that gives every patient's most recent reception date.
        last_reception = (
            select(
                Reception.patient_id.label("pid"),
                func.max(Reception.reception_date).label("last_date"),
            )
            .group_by(Reception.patient_id)
            .subquery()
        )

        base = (
            select(Patient, last_reception.c.last_date)
            .outerjoin(last_reception, last_reception.c.pid == Patient.id)
        )
        count_base = select(func.count(distinct(Patient.id))).select_from(Patient).outerjoin(
            last_reception, last_reception.c.pid == Patient.id
        )

        conditions: list = []
        if text:
            query = text.strip()
            if query:
                # Cross-alphabet: expand ``query`` into both Latin and
                # Cyrillic script variants so operators can search in either.
                # SQLite's default ``LIKE`` is ASCII-case-insensitive but
                # case-sensitive for Cyrillic. To cover both, we generate
                # multiple case forms of each variant and OR them together;
                # this stays index-friendly (no ``lower()`` on the column).
                from clinic.infrastructure.translit import expand_variants

                variants = expand_variants(query) or [query]
                cases: set[str] = set()
                for v in variants:
                    for form in {v, v.lower(), v.upper(), v.title(), v.capitalize()}:
                        if form:
                            cases.add(f"%{form}%")
                likes = list(cases)
                clauses = []

                def _like_any(col):
                    return or_(*(col.like(pat) for pat in likes))

                if search_in.full_name:
                    clauses.append(_like_any(Patient.full_name))
                if search_in.phone:
                    # Numbers rarely change script — a single like on the raw
                    # column is enough (SQLite ASCII LIKE handles digits).
                    clauses.append(Patient.phone.like(f"%{query}%"))
                if search_in.birth_year and query.isdigit():
                    clauses.append(Patient.birth_year == int(query))
                if search_in.diagnosis:
                    diagnosis_subq = (
                        select(Reception.patient_id)
                        .where(_like_any(Reception.diagnosis))
                    )
                    clauses.append(Patient.id.in_(diagnosis_subq))
                if search_in.medication:
                    medication_subq = (
                        select(Reception.patient_id)
                        .where(_like_any(Reception.recommendation))
                    )
                    clauses.append(Patient.id.in_(medication_subq))
                if clauses:
                    conditions.append(or_(*clauses))

        if date_from is not None:
            conditions.append(last_reception.c.last_date >= date_from)
        if date_to is not None:
            conditions.append(last_reception.c.last_date <= date_to)

        if conditions:
            base = base.where(and_(*conditions))
            count_base = count_base.where(and_(*conditions))

        # Prefer patients with the most recent activity first; brand-new
        # patients (no receptions) fall back to their created_at.
        order_key = func.coalesce(last_reception.c.last_date, Patient.created_at).desc()
        base = base.order_by(order_key).limit(limit).offset(offset)

        rows = [row[0] for row in self._session.execute(base).all()]
        total = int(self._session.execute(count_base).scalar_one())
        return rows, total

    def last_reception_map(self, patient_ids: list[int]) -> dict[int, datetime]:
        """Return ``{patient_id: latest_reception_date}`` for the given ids."""
        if not patient_ids:
            return {}
        stmt = (
            select(Reception.patient_id, func.max(Reception.reception_date))
            .where(Reception.patient_id.in_(patient_ids))
            .group_by(Reception.patient_id)
        )
        return {pid: dt for pid, dt in self._session.execute(stmt).all()}

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
            .options(joinedload(Reception.doctor))
            .order_by(Reception.reception_date.desc())
        )
        return list(self._session.execute(stmt).scalars())

    def latest_for_patient(self, patient_id: int) -> Reception | None:
        stmt = (
            select(Reception)
            .where(Reception.patient_id == patient_id)
            .order_by(Reception.reception_date.desc())
            .limit(1)
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def update_full(
        self,
        reception_id: int,
        *,
        doctor_id: int,
        reception_date: datetime,
        complaints_codes: list[str],
        complaints_details: dict[str, str] | None,
        complaints_note: str | None,
        anamnesis: str | None,
        lor_status: dict | None,
        diagnosis: str,
        recommendation: str | None,
    ) -> Reception | None:
        reception = self.get(reception_id)
        if reception is None:
            return None
        reception.doctor_id = doctor_id
        reception.reception_date = reception_date
        reception.complaints_codes = complaints_codes
        reception.complaints_details = complaints_details
        reception.complaints_note = complaints_note
        reception.anamnesis = anamnesis
        reception.lor_status = lor_status
        reception.diagnosis = diagnosis
        reception.recommendation = recommendation
        return reception

    def delete(self, reception_id: int) -> bool:
        reception = self.get(reception_id)
        if reception is None:
            return False
        self._session.delete(reception)
        return True

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

    # ----- statistics helpers -----

    def count_in_period(self, *, start: datetime, end: datetime) -> int:
        stmt = select(func.count(Reception.id)).where(
            and_(Reception.reception_date >= start, Reception.reception_date <= end)
        )
        return int(self._session.execute(stmt).scalar_one())

    def distinct_patients_in_period(self, *, start: datetime, end: datetime) -> int:
        stmt = select(func.count(distinct(Reception.patient_id))).where(
            and_(Reception.reception_date >= start, Reception.reception_date <= end)
        )
        return int(self._session.execute(stmt).scalar_one())

    def new_patients_in_period(self, *, start: datetime, end: datetime) -> int:
        """Patients whose FIRST reception falls in the period."""
        first_reception = (
            select(
                Reception.patient_id.label("pid"),
                func.min(Reception.reception_date).label("first_date"),
            )
            .group_by(Reception.patient_id)
            .subquery()
        )
        stmt = select(func.count()).where(
            and_(first_reception.c.first_date >= start, first_reception.c.first_date <= end)
        )
        return int(self._session.execute(stmt.select_from(first_reception)).scalar_one())

    def top_diagnoses(
        self,
        *,
        start: datetime,
        end: datetime,
        limit: int = 10,
    ) -> list[tuple[str, int]]:
        stmt = (
            select(Reception.diagnosis, func.count(Reception.id).label("cnt"))
            .where(and_(Reception.reception_date >= start, Reception.reception_date <= end))
            .group_by(Reception.diagnosis)
            .order_by(func.count(Reception.id).desc())
            .limit(limit)
        )
        return [(row[0], int(row[1])) for row in self._session.execute(stmt).all()]

    def receptions_by_day(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[tuple[str, int]]:
        """Return ``[(YYYY-MM-DD, count), ...]`` sorted by date ascending."""
        day = func.strftime("%Y-%m-%d", Reception.reception_date)
        stmt = (
            select(day, func.count(Reception.id))
            .where(and_(Reception.reception_date >= start, Reception.reception_date <= end))
            .group_by(day)
            .order_by(day)
        )
        return [(row[0], int(row[1])) for row in self._session.execute(stmt).all()]


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

    def add_many(self, records: list[CashierRecord]) -> list[CashierRecord]:
        self._session.add_all(records)
        self._session.flush()
        return records

    def get(self, record_id: int) -> CashierRecord | None:
        return self._session.get(CashierRecord, record_id)

    def delete(self, record_id: int) -> bool:
        record = self.get(record_id)
        if record is None:
            return False
        self._session.delete(record)
        return True

    def list_for_patient(self, patient_id: int) -> list[CashierRecord]:
        stmt = (
            select(CashierRecord)
            .where(CashierRecord.patient_id == patient_id)
            .options(joinedload(CashierRecord.service))
            .order_by(CashierRecord.paid_at.desc())
        )
        return list(self._session.execute(stmt).scalars())

    def list_for_reception(self, reception_id: int) -> list[CashierRecord]:
        stmt = (
            select(CashierRecord)
            .where(CashierRecord.reception_id == reception_id)
            .options(joinedload(CashierRecord.service))
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
            .options(joinedload(CashierRecord.service))
            .order_by(CashierRecord.paid_at.desc())
        )
        return list(self._session.execute(stmt).scalars())

    # ----- statistics -----

    def revenue_in_period(self, *, start: datetime, end: datetime) -> Decimal:
        stmt = select(func.coalesce(func.sum(CashierRecord.total), 0)).where(
            and_(CashierRecord.paid_at >= start, CashierRecord.paid_at <= end)
        )
        raw = self._session.execute(stmt).scalar_one()
        return Decimal(raw) if not isinstance(raw, Decimal) else raw

    def count_in_period(self, *, start: datetime, end: datetime) -> int:
        stmt = select(func.count(CashierRecord.id)).where(
            and_(CashierRecord.paid_at >= start, CashierRecord.paid_at <= end)
        )
        return int(self._session.execute(stmt).scalar_one())

    def distinct_receipts_in_period(self, *, start: datetime, end: datetime) -> int:
        """Number of unique (patient, reception) receipts in the period."""
        stmt = select(
            func.count(distinct(func.coalesce(CashierRecord.reception_id, -CashierRecord.patient_id)))
        ).where(and_(CashierRecord.paid_at >= start, CashierRecord.paid_at <= end))
        return int(self._session.execute(stmt).scalar_one())

    def revenue_by_service(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[tuple[int, str, str, int, Decimal]]:
        """Return ``[(service_id, name_uz, name_ru, units_sold, revenue), ...]``."""
        stmt = (
            select(
                Service.id,
                Service.name_uz,
                Service.name_ru,
                func.coalesce(func.sum(CashierRecord.quantity), 0),
                func.coalesce(func.sum(CashierRecord.total), 0),
            )
            .join(Service, Service.id == CashierRecord.service_id)
            .where(and_(CashierRecord.paid_at >= start, CashierRecord.paid_at <= end))
            .group_by(Service.id)
            .order_by(func.sum(CashierRecord.total).desc())
        )
        result = []
        for sid, uz, ru, units, revenue in self._session.execute(stmt).all():
            rev = Decimal(revenue) if not isinstance(revenue, Decimal) else revenue
            result.append((int(sid), uz, ru, int(units), rev))
        return result

    def revenue_by_day(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[tuple[str, Decimal]]:
        day = func.strftime("%Y-%m-%d", CashierRecord.paid_at)
        stmt = (
            select(day, func.coalesce(func.sum(CashierRecord.total), 0))
            .where(and_(CashierRecord.paid_at >= start, CashierRecord.paid_at <= end))
            .group_by(day)
            .order_by(day)
        )
        result = []
        for date_str, total in self._session.execute(stmt).all():
            rev = Decimal(total) if not isinstance(total, Decimal) else total
            result.append((date_str, rev))
        return result


__all__ = [
    "ANY_FIELD_SEARCH",
    "CashierRepository",
    "DoctorRepository",
    "PatientRepository",
    "PatientSearchField",
    "ReceptionRepository",
    "ServiceRepository",
]
