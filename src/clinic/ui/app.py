"""Qt application bootstrap.

Orchestrates first-run language selection and hands control to
``MainWindow``. Keeps ``main.py`` tiny so it can double as the PyInstaller
entry point.
"""

from __future__ import annotations

import sys

from loguru import logger
from PySide6.QtWidgets import QApplication

from clinic.db.database import init_db
from clinic.domain import settings_service
from clinic.i18n.translator import translator
from clinic.ui.language_dialog import LanguageDialog
from clinic.ui.main_window import MainWindow


def _ensure_language() -> None:
    """Load persisted language or prompt on first launch."""
    stored = settings_service.get_language()
    if stored:
        translator.set_language(stored)
        logger.info("Loaded persisted language: {}", stored)
        return

    dialog = LanguageDialog()
    if dialog.exec() and dialog.selected:
        translator.set_language(dialog.selected)
        settings_service.set_language(dialog.selected)
        settings_service.mark_first_run_done()
        logger.info("First-run language chosen: {}", dialog.selected)
    else:
        # Fallback: proceed with default if the dialog was dismissed
        translator.set_language("uz")
        settings_service.set_language("uz")
        logger.warning("Language dialog dismissed; defaulting to 'uz'")


def run() -> int:
    """Entry point that returns Qt's exit code."""
    init_db()

    # Best-effort daily backup right after the DB is ready. Failures are
    # already swallowed inside daily_auto_backup so we never block startup.
    from clinic.infrastructure.backup import daily_auto_backup

    daily_auto_backup()

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Clinic LOR")
    app.setOrganizationName("ClinicLOR")

    _ensure_language()

    window = MainWindow()
    window.show()
    return app.exec()
