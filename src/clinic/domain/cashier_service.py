"""Domain service for cashier payments.

A "payment" is one receipt containing one or more line-items (services), each
of which becomes its own :class:`CashierRecord` row in the database. This
schema makes statistics queries much simpler than nested tables.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from loguru import logger

from clinic.db.database import session_scope
from clinic.db.models import CashierRecord
from clinic.db.repository import (
    CashierRepository,
    PatientRepository,
    ReceptionRepository,
    ServiceRepository,
)
from clinic.domain.dto import CashierPaymentInput, CashierRecordDTO
from clinic.infrastructure.validators import ValidationError

# ============================================================================
# Read
# ============================================================================


def list_for_patient(patient_id: int) -> list[CashierRecordDTO]:
    with session_scope() as session:
        rows = CashierRepository(session).list_for_patient(patient_id)
        return [CashierRecordDTO.from_orm(r) for r in rows]


def list_for_reception(reception_id: int) -> list[CashierRecordDTO]:
    with session_scope() as session:
        rows = CashierRepository(session).list_for_reception(reception_id)
        return [CashierRecordDTO.from_orm(r) for r in rows]


# ============================================================================
# Write
# ============================================================================


def save_payment(data: CashierPaymentInput) -> list[CashierRecordDTO]:
    """Persist a receipt as one row per line-item. All-or-nothing."""
    errors = ValidationError()

    if not data.items:
        errors.add("items", "validation.cashier_items_required")

    normalized_items: list[tuple[int, int]] = []  # (service_id, quantity)
    for i, item in enumerate(data.items):
        if item.quantity <= 0:
            errors.add(f"items[{i}].quantity", "validation.quantity_positive")
            continue
        normalized_items.append((item.service_id, item.quantity))

    if errors:
        raise errors

    note = (data.note or "").strip() or None
    now = datetime.utcnow()

    with session_scope() as session:
        # Verify patient
        patient = PatientRepository(session).get(data.patient_id)
        if patient is None:
            err = ValidationError()
            err.add("patient", "validation.patient_not_found")
            raise err

        # Verify optional reception
        if data.reception_id is not None:
            reception = ReceptionRepository(session).get(data.reception_id)
            if reception is None:
                err = ValidationError()
                err.add("reception", "validation.patient_not_found")
                raise err

        svc_repo = ServiceRepository(session)
        cash_repo = CashierRepository(session)

        records: list[CashierRecord] = []
        for service_id, quantity in normalized_items:
            svc = svc_repo.get(service_id)
            if svc is None:
                err = ValidationError()
                err.add(f"service.{service_id}", "validation.service_not_found")
                raise err
            price = Decimal(svc.price)
            record = CashierRecord(
                patient_id=data.patient_id,
                reception_id=data.reception_id,
                service_id=service_id,
                quantity=quantity,
                price_at_moment=price,
                total=price * quantity,
                paid_at=now,
                note=note,
            )
            records.append(record)

        cash_repo.add_many(records)

        logger.info(
            "Cashier: saved {} record(s) for patient {} reception {} total {}",
            len(records),
            data.patient_id,
            data.reception_id,
            sum(r.total for r in records),
        )
        return [CashierRecordDTO.from_orm(r) for r in records]


def delete(record_id: int) -> bool:
    with session_scope() as session:
        if CashierRepository(session).delete(record_id):
            logger.info("Cashier record {} deleted", record_id)
            return True
        return False


# ============================================================================
# Helpers
# ============================================================================


def total_for_reception(reception_id: int) -> Decimal:
    """Sum of all payments linked to a given reception."""
    records = list_for_reception(reception_id)
    return sum((r.total for r in records), Decimal("0"))


__all__ = [
    "delete",
    "list_for_patient",
    "list_for_reception",
    "save_payment",
    "total_for_reception",
]
