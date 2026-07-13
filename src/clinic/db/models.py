"""SQLAlchemy 2.0 ORM models for the clinic desktop application.

Schema mirrors ``docs/database_schema.md``. All timestamps are stored as UTC
naive datetimes; the presentation layer converts to local time when displaying.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


# ----- helpers ---------------------------------------------------------------


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())


def _updated_at() -> Mapped[datetime]:
    return mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


# ----- patients --------------------------------------------------------------


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_year: Mapped[int] = mapped_column(Integer, nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()

    receptions: Mapped[list[Reception]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    cashier_records: Mapped[list[CashierRecord]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint("birth_year BETWEEN 1900 AND 2100", name="ck_patients_birth_year"),
        Index("idx_patients_full_name", "full_name"),
        Index("idx_patients_phone", "phone"),
        Index("idx_patients_created", "created_at"),
    )


# ----- doctors ---------------------------------------------------------------


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = _created_at()

    receptions: Mapped[list[Reception]] = relationship(back_populates="doctor")


# ----- receptions ------------------------------------------------------------


class Reception(Base):
    __tablename__ = "receptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    reception_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Complaints (structured selection + optional freeform note)
    complaints_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    complaints_details: Mapped[dict[str, str] | None] = mapped_column(JSON)
    complaints_note: Mapped[str | None] = mapped_column(Text)

    # Free-form fields
    anamnesis: Mapped[str | None] = mapped_column(Text)
    lor_status: Mapped[dict | None] = mapped_column(JSON)
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()

    patient: Mapped[Patient] = relationship(back_populates="receptions")
    doctor: Mapped[Doctor] = relationship(back_populates="receptions")
    cashier_records: Mapped[list[CashierRecord]] = relationship(back_populates="reception")

    __table_args__ = (
        Index("idx_receptions_date", "reception_date"),
        Index("idx_receptions_patient", "patient_id"),
        Index("idx_receptions_diagnosis", "diagnosis"),
    )


# ----- services --------------------------------------------------------------


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_uz: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()

    cashier_records: Mapped[list[CashierRecord]] = relationship(back_populates="service")


# ----- cashier_records -------------------------------------------------------


class CashierRecord(Base):
    __tablename__ = "cashier_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    reception_id: Mapped[int | None] = mapped_column(
        ForeignKey("receptions.id", ondelete="SET NULL")
    )
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price_at_moment: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    note: Mapped[str | None] = mapped_column(Text)

    patient: Mapped[Patient] = relationship(back_populates="cashier_records")
    reception: Mapped[Reception | None] = relationship(back_populates="cashier_records")
    service: Mapped[Service] = relationship(back_populates="cashier_records")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_cashier_quantity_positive"),
        Index("idx_cashier_paid", "paid_at"),
        Index("idx_cashier_patient", "patient_id"),
    )


# ----- settings (key-value) --------------------------------------------------


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


# ----- custom catalog extensions ---------------------------------------------


class ComplaintCatalogCustom(Base):
    """User-added complaints. Built-in ones live in ``catalogs/complaints.json``."""

    __tablename__ = "complaint_catalog_custom"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    section: Mapped[str] = mapped_column(String(32), nullable=False)  # ear|nose|pharynx|larynx
    name_uz: Mapped[str] = mapped_column(String(500), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(500), nullable=False)
    has_discharge_type: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = _created_at()


class LorCatalogCustom(Base):
    """User-added LOR STATUS items."""

    __tablename__ = "lor_catalog_custom"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    section: Mapped[str] = mapped_column(String(64), nullable=False)
    field_type: Mapped[str] = mapped_column(String(16), nullable=False)  # radio|checkbox|text
    label_uz: Mapped[str] = mapped_column(String(500), nullable=False)
    label_ru: Mapped[str] = mapped_column(String(500), nullable=False)
    options_json: Mapped[list | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


# ----- web users (Phase 3) ---------------------------------------------------


class WebUser(Base):
    """Clinic staff account for the web app.

    Roles (string enum, kept simple to sidestep migrations):

    - ``admin``   → full access (settings, users, backup, delete anything)
    - ``staff``   → reception, patients, cashier, stats. Cannot touch users
      or backup, cannot delete records.
    """

    __tablename__ = "web_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="staff")
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = _created_at()
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)

    __table_args__ = (
        CheckConstraint("role IN ('admin','staff')", name="ck_web_users_role"),
        Index("idx_web_users_active", "is_active"),
    )


__all__ = [
    "Base",
    "CashierRecord",
    "ComplaintCatalogCustom",
    "Doctor",
    "LorCatalogCustom",
    "Patient",
    "Reception",
    "Service",
    "Setting",
    "WebUser",
]
