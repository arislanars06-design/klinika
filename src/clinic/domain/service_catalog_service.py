"""Services catalog (what the clinic charges for).

Kept intentionally separate from ``settings_service`` because these rows
are looked up on every cashier flow, whereas settings are read once.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from clinic.db.models import Service


@dataclass(slots=True)
class ServiceInput:
    name_uz: str
    name_ru: str
    price: Decimal


def get(session: Session, service_id: int) -> Service | None:
    return session.get(Service, service_id)


def list_active(session: Session) -> Sequence[Service]:
    stmt = select(Service).where(Service.is_active.is_(True)).order_by(Service.name_uz)
    return session.execute(stmt).scalars().all()


def list_all(session: Session) -> Sequence[Service]:
    return session.execute(select(Service).order_by(Service.name_uz)).scalars().all()


def create(session: Session, data: ServiceInput) -> Service:
    service = Service(
        name_uz=data.name_uz.strip(),
        name_ru=data.name_ru.strip(),
        price=Decimal(data.price),
    )
    session.add(service)
    session.flush()
    return service


def update(session: Session, service_id: int, data: ServiceInput) -> Service:
    service = session.get(Service, service_id)
    if service is None:
        raise LookupError(f"Service {service_id} not found")
    service.name_uz = data.name_uz.strip()
    service.name_ru = data.name_ru.strip()
    service.price = Decimal(data.price)
    session.flush()
    return service


def set_active(session: Session, service_id: int, active: bool) -> Service:
    service = session.get(Service, service_id)
    if service is None:
        raise LookupError(f"Service {service_id} not found")
    service.is_active = active
    session.flush()
    return service
