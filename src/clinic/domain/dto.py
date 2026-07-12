"""Plain data-transfer objects returned by domain services.

The UI layer works with these instead of live ORM entities so we can freely
close sessions between operations without hitting ``DetachedInstanceError``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from clinic.db.models import Doctor, Patient, Reception, Service


@dataclass
class PatientDTO:
    id: int
    full_name: str
    birth_year: int
    address: str | None
    phone: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, p: Patient) -> PatientDTO:
        return cls(
            id=p.id,
            full_name=p.full_name,
            birth_year=p.birth_year,
            address=p.address,
            phone=p.phone,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )

    def display_line(self) -> str:
        parts = [self.full_name, f"({self.birth_year})"]
        if self.address:
            parts.append(f"— {self.address}")
        return " ".join(parts)


@dataclass
class DoctorDTO:
    id: int
    full_name: str
    phone: str | None
    is_active: bool

    @classmethod
    def from_orm(cls, d: Doctor) -> DoctorDTO:
        return cls(
            id=d.id,
            full_name=d.full_name,
            phone=d.phone,
            is_active=d.is_active,
        )


@dataclass
class ServiceDTO:
    id: int
    name_uz: str
    name_ru: str
    price: Decimal
    is_active: bool

    @classmethod
    def from_orm(cls, s: Service) -> ServiceDTO:
        return cls(
            id=s.id,
            name_uz=s.name_uz,
            name_ru=s.name_ru,
            price=Decimal(s.price),
            is_active=s.is_active,
        )

    def display_name(self, lang: str) -> str:
        return self.name_ru if lang == "ru" else self.name_uz


@dataclass
class ReceptionDTO:
    id: int
    patient_id: int
    doctor_id: int
    reception_date: datetime
    complaints_codes: list[str]
    complaints_details: dict[str, str]
    complaints_note: str | None
    anamnesis: str | None
    lor_status: dict | None
    diagnosis: str
    recommendation: str | None
    created_at: datetime

    @classmethod
    def from_orm(cls, r: Reception) -> ReceptionDTO:
        return cls(
            id=r.id,
            patient_id=r.patient_id,
            doctor_id=r.doctor_id,
            reception_date=r.reception_date,
            complaints_codes=list(r.complaints_codes or []),
            complaints_details=dict(r.complaints_details or {}),
            complaints_note=r.complaints_note,
            anamnesis=r.anamnesis,
            lor_status=r.lor_status,
            diagnosis=r.diagnosis,
            recommendation=r.recommendation,
            created_at=r.created_at,
        )


# ============================================================================
# Input DTOs (form -> service)
# ============================================================================


@dataclass
class PatientInput:
    full_name: str
    birth_year: int | str
    address: str | None = None
    phone: str | None = None


@dataclass
class ReceptionInput:
    patient: PatientInput
    patient_id: int | None  # None if the patient is new
    doctor_id: int | None
    reception_date: datetime
    complaints_codes: list[str] = field(default_factory=list)
    complaints_details: dict[str, str] = field(default_factory=dict)
    complaints_note: str | None = None
    anamnesis: str | None = None
    lor_status: dict | None = None
    diagnosis: str = ""
    recommendation: str | None = None


__all__ = [
    "DoctorDTO",
    "PatientDTO",
    "PatientInput",
    "ReceptionDTO",
    "ReceptionInput",
    "ServiceDTO",
]
