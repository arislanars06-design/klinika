"""Skeleton smoke tests: config, DB, catalogs, translator all import & work.

The ``isolated_db`` autouse fixture from ``conftest.py`` gives each test a
fresh SQLite file in a tmp dir.
"""

from __future__ import annotations


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
        reload_all,
    )

    reload_all()

    complaints = complaints_catalog()
    lor = lor_status_catalog()
    discharge = discharge_types_catalog()

    # Built-in sections must all be present (custom DB rows may add extras).
    builtin_codes = {"general", "ear", "nose", "pharynx", "larynx"}
    section_codes = {s["code"] for s in complaints["sections"]}
    assert builtin_codes.issubset(section_codes)
    ear = next(s for s in complaints["sections"] if s["code"] == "ear")
    assert sum(1 for it in ear["items"] if not it.get("_custom_id")) == 8
    general = next(s for s in complaints["sections"] if s["code"] == "general")
    assert sum(1 for it in general["items"] if not it.get("_custom_id")) == 11

    method_codes = {m["code"] for m in lor["methods"]}
    assert method_codes == {"rhinoscopy", "pharyngoscopy", "otoscopy", "laryngoscopy"}

    assert len(discharge["types"]) >= 8


def test_translator_returns_uz_by_default() -> None:
    from clinic.i18n.translator import Translator

    tr = Translator()
    assert tr.language == "uz"
    assert tr.t("menu.start_reception") == "Қабулни бошлаш"

    tr.set_language("ru")
    assert tr.t("menu.start_reception") == "Начать приём"


def test_init_db_creates_tables() -> None:
    from clinic.db.database import init_db, session_scope
    from clinic.db.models import Setting

    init_db()
    with session_scope() as session:
        session.add(Setting(key="probe", value="ok"))

    with session_scope() as session:
        row = session.query(Setting).filter_by(key="probe").one()
        assert row.value == "ok"
