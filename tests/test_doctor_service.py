"""Tests for :mod:`clinic.domain.doctor_service`."""

from __future__ import annotations

import pytest

from clinic.domain import doctor_service
from clinic.infrastructure.validators import ValidationError


def test_create_and_list() -> None:
    created = doctor_service.create(full_name="Karimov Ali", phone="+998901234567")
    assert created.id > 0
    assert created.full_name == "Karimov Ali"
    assert created.is_active is True

    listed = doctor_service.list_all()
    assert len(listed) == 1
    assert listed[0].full_name == "Karimov Ali"


def test_create_invalid_name_raises() -> None:
    with pytest.raises(ValidationError) as exc:
        doctor_service.create(full_name="A")
    assert "full_name" in exc.value.errors


def test_create_invalid_phone_raises() -> None:
    with pytest.raises(ValidationError) as exc:
        doctor_service.create(full_name="Karimov Ali", phone="not-a-phone")
    assert "phone" in exc.value.errors


def test_update_name_and_phone() -> None:
    d = doctor_service.create(full_name="Karimov Ali", phone="+998901234567")
    updated = doctor_service.update(d.id, full_name="Aliyev Karim", phone="+998901112233")
    assert updated is not None
    assert updated.full_name == "Aliyev Karim"
    assert updated.phone == "+998901112233"


def test_set_active_toggles() -> None:
    d = doctor_service.create(full_name="Karimov Ali")
    doctor_service.set_active(d.id, False)
    assert doctor_service.list_all(active_only=True) == []
    assert len(doctor_service.list_all(active_only=False)) == 1

    doctor_service.set_active(d.id, True)
    assert len(doctor_service.list_all(active_only=True)) == 1


def test_get_nonexistent_returns_none() -> None:
    assert doctor_service.get(999) is None
