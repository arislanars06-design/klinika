"""Shared pytest fixtures.

Reassigning the ``settings`` singleton across submodules is fiddly because
``from clinic.config import settings`` captures a name in each importer's
namespace. This conftest rebinds the singleton in every affected module so
each test genuinely runs against its own SQLite file.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_clinic_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the app at a per-test data directory and reset caches."""
    monkeypatch.setenv("CLINIC_DATA_DIR", str(tmp_path / "data"))

    # Build a fresh Settings instance and propagate it to every module that
    # imported the previous one by name.
    from clinic import config as cfg
    new_settings = cfg.Settings()
    cfg.settings = new_settings

    for module_name in (
        "clinic.db.database",
        "clinic.i18n.translator",
        "clinic.infrastructure.logging_setup",
        "clinic.domain.catalog_loader",
        "clinic.printing.docx_builder",
        "clinic.web.app",
        "clinic.web.routes.reception",
        "clinic.web.routes.patients",
        "clinic.web.routes.cashier",
        "clinic.web.routes.settings",
    ):
        module = __import__(module_name, fromlist=["*"])
        if hasattr(module, "settings"):
            module.settings = new_settings

    # Rebuild the SQLAlchemy engine so it targets the new DB path.
    from clinic.db import database as db_module

    db_module.engine = db_module._make_engine()
    db_module.SessionLocal.configure(bind=db_module.engine)
