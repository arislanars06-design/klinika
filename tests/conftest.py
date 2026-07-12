"""Shared fixtures for the test suite.

The autouse fixture below points every test at a fresh SQLite database in
``tmp_path``, so tests never see (or touch) the developer's real data.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Point ``clinic.config.settings`` and the DB engine at a tmp directory.

    * Rebuilds :data:`clinic.db.database.engine` and ``SessionLocal`` so
      previously loaded modules pick up the new SQLite file.
    * Calls :func:`init_db` so the schema is ready before the test runs.
    """
    monkeypatch.setenv("CLINIC_DATA_DIR", str(tmp_path / "data"))

    # Reload settings so its paths reflect the tmp env var
    from clinic import config as cfg

    cfg.settings = cfg.Settings()  # type: ignore[assignment]

    # Modules that did ``from clinic.config import settings`` at import time
    # kept their own local reference to the original object — rebind them so
    # ``settings.db_url`` points at the new tmp path.
    from clinic.db import database as dbmod
    from clinic.domain import catalog_loader as catmod
    from clinic.i18n import translator as i18nmod
    from clinic.infrastructure import backup as backupmod
    from clinic.infrastructure import logging_setup as logmod
    from clinic.printing import docx_builder as docxmod
    from clinic.printing import receipt_builder as receiptmod
    from clinic.printing import stats_export as statsmod

    dbmod.settings = cfg.settings
    backupmod.settings = cfg.settings
    catmod.settings = cfg.settings
    i18nmod.settings = cfg.settings
    logmod.settings = cfg.settings
    docxmod.settings = cfg.settings
    receiptmod.settings = cfg.settings
    statsmod.settings = cfg.settings

    # Rebuild engine + SessionLocal against the new URL. Any function that
    # imported ``session_scope`` earlier still resolves ``SessionLocal`` from
    # the module globals at call time, so reassignment is enough.
    dbmod.engine = dbmod._make_engine()
    dbmod.SessionLocal = sessionmaker(
        bind=dbmod.engine, expire_on_commit=False, future=True
    )
    dbmod.init_db()

    # Drop any cached catalog data so tests always see the shipped files.
    from clinic.domain import catalog_loader

    catalog_loader.reload_all()

    yield tmp_path
