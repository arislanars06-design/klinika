"""Skeleton smoke tests for config, DB, catalogs, translator, and web routes."""

from __future__ import annotations

from pathlib import Path

import pytest


# Data-dir isolation is handled by tests/conftest.py::_isolate_clinic_state.


def test_config_paths_are_writable() -> None:
    from clinic.config import settings

    settings.ensure_dirs()
    assert settings.data_dir.is_dir()
    assert settings.logs_dir.is_dir()
    assert settings.backups_dir.is_dir()


def test_catalogs_load() -> None:
    from clinic.domain.catalog_loader import (
        complaints_catalog,
        discharge_types_catalog,
        lor_status_catalog,
    )

    complaints_catalog.cache_clear()
    lor_status_catalog.cache_clear()
    discharge_types_catalog.cache_clear()

    complaints = complaints_catalog()
    lor = lor_status_catalog()
    discharge = discharge_types_catalog()

    assert len(complaints["sections"]) == 4
    ear = next(s for s in complaints["sections"] if s["code"] == "ear")
    assert len(ear["items"]) == 8

    method_codes = {m["code"] for m in lor["methods"]}
    assert method_codes == {"rhinoscopy", "pharyngoscopy", "otoscopy", "laryngoscopy"}

    assert len(discharge["types"]) >= 8


def test_translator_returns_uz_by_default() -> None:
    from clinic.i18n.translator import t

    assert t("menu.start_reception", "uz") == "Qabulni boshlash"
    assert t("menu.start_reception", "ru") == "Начать приём"
    # Fallback to Uzbek then to raw key
    assert t("nope.does.not.exist", "ru") == "nope.does.not.exist"


def test_init_db_creates_tables() -> None:
    from clinic.db.database import init_db, session_scope
    from clinic.db.models import Setting

    init_db()
    with session_scope() as session:
        session.add(Setting(key="probe", value="ok"))

    with session_scope() as session:
        row = session.query(Setting).filter_by(key="probe").one()
        assert row.value == "ok"
