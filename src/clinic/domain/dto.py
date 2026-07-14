"""Plain data-transfer objects returned by domain services.

The UI layer works with these instead of live ORM entities so we can freely
close sessions between operations without hitting ``DetachedInstanceError``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from clinic.db.models import CashierRecord, Doctor, Patient, Reception, Service


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
    # Optional — set when editing an existing reception.
    reception_id: int | None = None


# ============================================================================
# Cashier
# ============================================================================


@dataclass
class CashierRecordDTO:
    """One paid line-item (a single service on a single visit)."""

    id: int
    patient_id: int
    reception_id: int | None
    service_id: int
    service_name_uz: str
    service_name_ru: str
    quantity: int
    price_at_moment: Decimal
    total: Decimal
    paid_at: datetime
    note: str | None
    payment_type: str = "cash"  # cash | transfer | terminal

    @classmethod
    def from_orm(cls, r: CashierRecord) -> CashierRecordDTO:
        svc = r.service
        return cls(
            id=r.id,
            patient_id=r.patient_id,
            reception_id=r.reception_id,
            service_id=r.service_id,
            service_name_uz=svc.name_uz if svc else "",
            service_name_ru=svc.name_ru if svc else "",
            quantity=r.quantity,
            price_at_moment=Decimal(r.price_at_moment),
            total=Decimal(r.total),
            paid_at=r.paid_at,
            note=r.note,
            payment_type=getattr(r, "payment_type", None) or "cash",
        )

    def service_name(self, lang: str) -> str:
        return self.service_name_ru if lang == "ru" else self.service_name_uz


@dataclass
class CashierItemInput:
    """One line-item on the cashier form (service + quantity)."""

    service_id: int
    quantity: int = 1


VALID_PAYMENT_TYPES = ("cash", "transfer", "terminal")


@dataclass
class CashierPaymentInput:
    """A complete cashier operation (one or more line-items in a single receipt)."""

    patient_id: int
    reception_id: int | None
    items: list[CashierItemInput] = field(default_factory=list)
    note: str | None = None
    payment_type: str = "cash"
    # Optional user-supplied grand total override; when set, the sum of items
    # is scaled proportionally so the receipt totals exactly this amount.
    override_total: Decimal | None = None


# ============================================================================
# Patient history / search
# ============================================================================


@dataclass
class PatientSummaryDTO:
    """Row in the Patient History table — patient + last reception summary."""

    patient: PatientDTO
    last_reception_date: datetime | None

    @property
    def age(self) -> int:
        return datetime.now().year - self.patient.birth_year


@dataclass
class PatientHistoryPage:
    """One page of paginated patient results."""

    items: list[PatientSummaryDTO]
    total: int
    page: int  # 1-based
    page_size: int

    @property
    def page_count(self) -> int:
        if self.page_size <= 0:
            return 1
        return max(1, (self.total + self.page_size - 1) // self.page_size)


@dataclass
class PatientDetail:
    """Everything the Patient Card dialog needs about one patient."""

    patient: PatientDTO
    receptions: list[ReceptionDTO]
    payments: list[CashierRecordDTO]
    doctor_names: dict[int, str] = field(default_factory=dict)

    @property
    def total_paid(self) -> Decimal:
        return sum((p.total for p in self.payments), Decimal("0"))


# ============================================================================
# Statistics
# ============================================================================


@dataclass
class DiagnosisCount:
    diagnosis: str
    count: int


@dataclass
class DayPoint:
    """One (date, value) sample on a chart timeline."""

    date: str  # ISO YYYY-MM-DD
    value: float  # count of receptions or revenue in currency


@dataclass
class PatientInPeriod:
    """A patient who had ≥ 1 reception in the selected period."""

    id: int
    full_name: str
    birth_year: int
    phone: str | None
    visits: int             # visits inside the period
    last_visit: datetime
    is_new: bool            # first-ever reception fell inside the period
    last_diagnosis: str = ""


@dataclass
class PatientStats:
    total_patients: int
    new_patients: int
    repeat_receptions: int
    top_diagnoses: list[DiagnosisCount]
    by_day: list[DayPoint]  # reception count per day
    # Phase 4: list of patients matching the selected period (for the
    # filtered table shown below the KPI cards).
    patients: list[PatientInPeriod] = field(default_factory=list)


@dataclass
class ServiceRevenue:
    service_id: int
    name_uz: str
    name_ru: str
    units_sold: int
    revenue: Decimal

    def display_name(self, lang: str) -> str:
        return self.name_ru if lang == "ru" else self.name_uz


@dataclass
class PaymentTypeRevenue:
    """Total revenue for one payment channel (cash / transfer / terminal)."""

    payment_type: str  # cash | transfer | terminal
    total: Decimal
    count: int  # number of line-items with this payment type


@dataclass
class CashierStats:
    total_revenue: Decimal
    payment_count: int
    receipts_count: int
    average_receipt: Decimal
    by_service: list[ServiceRevenue]
    by_day: list[DayPoint]  # revenue per day
    # Phase 4: total-by-payment-channel breakdown.
    by_payment_type: dict[str, "PaymentTypeRevenue"] = field(default_factory=dict)


__all__ = [
    "CashierItemInput",
    "CashierPaymentInput",
    "CashierRecordDTO",
    "CashierStats",
    "DayPoint",
    "DiagnosisCount",
    "DoctorDTO",
    "PatientDTO",
    "PatientDetail",
    "PatientHistoryPage",
    "PatientInPeriod",
    "PatientInput",
    "PatientStats",
    "PatientSummaryDTO",
    "PaymentTypeRevenue",
    "ReceptionDTO",
    "ReceptionInput",
    "ServiceDTO",
    "ServiceRevenue",
]
