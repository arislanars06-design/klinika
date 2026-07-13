"""Domain service for clinic services (CRUD + pricing).

Named ``service_service`` for regularity with ``doctor_service`` — the
``ServiceDTO`` refers to a billable clinic service (consultation, procedure).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from clinic.db.database import session_scope
from clinic.db.repository import ServiceRepository
from clinic.domain.dto import ServiceDTO
from clinic.infrastructure.validators import ValidationError


def list_all(*, active_only: bool = False) -> list[ServiceDTO]:
    with session_scope() as session:
        repo = ServiceRepository(session)
        rows = repo.list_active() if active_only else repo.list_all()
        return [ServiceDTO.from_orm(s) for s in rows]


def get(service_id: int) -> ServiceDTO | None:
    with session_scope() as session:
        row = ServiceRepository(session).get(service_id)
        return ServiceDTO.from_orm(row) if row else None


def _coerce_price(raw: Decimal | str | int | float) -> Decimal:
    """Return a positive Decimal or raise ``ValidationError`` on ``price``."""
    if isinstance(raw, Decimal):
        value = raw
    else:
        try:
            value = Decimal(str(raw).replace(" ", "").replace(",", "."))
        except (InvalidOperation, ValueError):
            err = ValidationError()
            err.add("price", "validation.price_invalid")
            raise err from None

    if value < 0:
        err = ValidationError()
        err.add("price", "validation.price_negative")
        raise err
    # Quantize to 2 decimals so we don't accidentally store more precision.
    return value.quantize(Decimal("0.01"))


def _validate_names(name_uz: str, name_ru: str) -> tuple[str, str]:
    errors = ValidationError()
    uz = (name_uz or "").strip()
    ru = (name_ru or "").strip()
    if not uz:
        errors.add("name_uz", "validation.required")
    if not ru:
        errors.add("name_ru", "validation.required")
    if errors:
        raise errors
    return uz, ru


def create(
    *,
    name_uz: str,
    name_ru: str,
    price: Decimal | str | int | float,
) -> ServiceDTO:
    uz, ru = _validate_names(name_uz, name_ru)
    price_value = _coerce_price(price)
    with session_scope() as session:
        repo = ServiceRepository(session)
        created = repo.create(name_uz=uz, name_ru=ru, price=price_value)
        return ServiceDTO.from_orm(created)


def update(
    service_id: int,
    *,
    name_uz: str | None = None,
    name_ru: str | None = None,
    price: Decimal | str | int | float | None = None,
    is_active: bool | None = None,
) -> ServiceDTO | None:
    errors = ValidationError()
    normalized_uz: str | None = None
    normalized_ru: str | None = None
    normalized_price: Decimal | None = None

    if name_uz is not None:
        normalized_uz = (name_uz or "").strip()
        if not normalized_uz:
            errors.add("name_uz", "validation.required")
    if name_ru is not None:
        normalized_ru = (name_ru or "").strip()
        if not normalized_ru:
            errors.add("name_ru", "validation.required")
    if price is not None:
        try:
            normalized_price = _coerce_price(price)
        except ValidationError as ve:
            errors.errors.update(ve.errors)

    if errors:
        raise errors

    with session_scope() as session:
        row = ServiceRepository(session).update(
            service_id,
            name_uz=normalized_uz,
            name_ru=normalized_ru,
            price=normalized_price,
            is_active=is_active,
        )
        return ServiceDTO.from_orm(row) if row else None


def set_active(service_id: int, is_active: bool) -> ServiceDTO | None:
    with session_scope() as session:
        row = ServiceRepository(session).update(service_id, is_active=is_active)
        return ServiceDTO.from_orm(row) if row else None


def delete(service_id: int) -> bool:
    """Permanently delete a service by id. Returns True if deleted."""
    from clinic.db.models import Service

    with session_scope() as session:
        svc = session.get(Service, service_id)
        if svc is None:
            return False
        session.delete(svc)
        return True
