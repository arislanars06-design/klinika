"""Tests for :mod:`clinic.domain.service_service`."""

from __future__ import annotations

from decimal import Decimal

import pytest

from clinic.domain import service_service
from clinic.infrastructure.validators import ValidationError


def test_create_service_with_decimal() -> None:
    svc = service_service.create(
        name_uz="Konsultatsiya",
        name_ru="Консультация",
        price=Decimal("100000.00"),
    )
    assert svc.name_uz == "Konsultatsiya"
    assert svc.price == Decimal("100000.00")
    assert svc.is_active is True


def test_price_from_string_with_comma() -> None:
    svc = service_service.create(name_uz="X", name_ru="Y", price="99,50")
    assert svc.price == Decimal("99.50")


def test_price_from_string_with_spaces() -> None:
    svc = service_service.create(name_uz="X", name_ru="Y", price="150 000")
    assert svc.price == Decimal("150000.00")


def test_negative_price_raises() -> None:
    with pytest.raises(ValidationError):
        service_service.create(name_uz="X", name_ru="Y", price=-1)


def test_missing_name_uz_raises() -> None:
    with pytest.raises(ValidationError) as exc:
        service_service.create(name_uz="", name_ru="Y", price=100)
    assert "name_uz" in exc.value.errors


def test_missing_name_ru_raises() -> None:
    with pytest.raises(ValidationError) as exc:
        service_service.create(name_uz="X", name_ru="", price=100)
    assert "name_ru" in exc.value.errors


def test_update_changes_only_provided_fields() -> None:
    svc = service_service.create(name_uz="A", name_ru="Б", price=100)
    updated = service_service.update(svc.id, price=200)
    assert updated is not None
    assert updated.name_uz == "A"  # unchanged
    assert updated.price == Decimal("200.00")


def test_list_active_filters_archived() -> None:
    a = service_service.create(name_uz="A", name_ru="А", price=100)
    b = service_service.create(name_uz="B", name_ru="Б", price=200)
    service_service.set_active(a.id, False)

    active = service_service.list_all(active_only=True)
    assert len(active) == 1
    assert active[0].id == b.id

    all_ = service_service.list_all(active_only=False)
    assert len(all_) == 2
