"""Cashier service.

Cashier records are append-only from the user's point of view. Each row
snapshots the service price at time of sale so historical totals are stable
even if catalog prices change later.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from sqlalchemy import Select, and_, func, select
from sqlalchemy.orm import Session, selectinload

from clinic.db.models import CashierRecord, Service


class CashierValidationError(ValueError):
    """Raised when the cashier form is not valid."""


@dataclass(slots=True)
class CashierLine:
    service_id: int
    quantity: int


@dataclass(slots=True)
class CashierBatch:
    patient_id: int
    reception_id: int | None
    lines: list[CashierLine]
    note: str | None = None


def _validate(batch: CashierBatch) -> list[str]:
    errors: list[str] = []
    if not batch.patient_id:
        errors.append("validation.patient_required")
    if not batch.lines:
        errors.append("validation.services_required")
    for line in batch.lines:
        if line.quantity <= 0:
            errors.append("validation.quantity_positive")
            break
    return errors


def create_batch(session: Session, batch: CashierBatch) -> list[CashierRecord]:
    """Persist every line in a single flush, snapshotting current prices."""
    errors = _validate(batch)
    if errors:
        raise CashierValidationError(errors)

    now = datetime.utcnow()
    records: list[CashierRecord] = []
    for line in batch.lines:
        service = session.get(Service, line.service_id)
        if service is None:
            raise LookupError(f"Service {line.service_id} not found")
        price = Decimal(service.price)
        record = CashierRecord(
            patient_id=batch.patient_id,
            reception_id=batch.reception_id,
            service_id=service.id,
            quantity=line.quantity,
            price_at_moment=price,
            total=price * line.quantity,
            paid_at=now,
            note=batch.note,
        )
        session.add(record)
        records.append(record)
    session.flush()
    return records


def list_by_patient(session: Session, patient_id: int) -> Sequence[CashierRecord]:
    stmt = (
        select(CashierRecord)
        .options(selectinload(CashierRecord.service))
        .where(CashierRecord.patient_id == patient_id)
        .order_by(CashierRecord.paid_at.desc())
    )
    return session.execute(stmt).scalars().all()


def list_page(
    session: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    start: datetime | None = None,
    end: datetime | None = None,
) -> tuple[Sequence[CashierRecord], int]:
    base: Select = select(CashierRecord).options(
        selectinload(CashierRecord.service),
        selectinload(CashierRecord.patient),
    )
    conditions = []
    if start:
        conditions.append(CashierRecord.paid_at >= start)
    if end:
        conditions.append(CashierRecord.paid_at <= end)
    if conditions:
        base = base.where(and_(*conditions))

    total = session.execute(
        select(func.count()).select_from(base.subquery())
    ).scalar_one()
    rows = session.execute(
        base.order_by(CashierRecord.paid_at.desc()).offset(offset).limit(limit)
    ).scalars().all()
    return rows, int(total)


def delete(session: Session, record_id: int) -> None:
    row = session.get(CashierRecord, record_id)
    if row is not None:
        session.delete(row)
        session.flush()
