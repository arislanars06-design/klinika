"""Small UI helpers that connect print buttons to the docx builders.

Every window that needs to produce a Word document reaches the same steps:
prompt for a save location, write the file, then try to open it with the
system's default handler. Rather than duplicate that flow, we centralise it
here so the docx module stays independent of Qt.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

from loguru import logger
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from clinic.i18n.translator import t
from clinic.printing.common import open_document


def _slugify(value: str) -> str:
    """Squash non-word characters so a filename stays cross-platform friendly."""
    cleaned = re.sub(r"[^A-Za-z0-9А-Яа-яЁёЎўҚқҒғҲҳ]+", "_", value).strip("_")
    return cleaned or "file"


def prompt_and_save(
    parent: QWidget | None,
    *,
    title_key: str,
    default_filename: str,
    builder: Callable[[Path], Path],
) -> Path | None:
    """Show a *Save As* dialog and run ``builder`` on the chosen path.

    Returns the written path on success. Errors are reported via ``QMessageBox``
    and ``None`` is returned in that case (so callers can skip the "opened"
    UI update).
    """
    path, _ = QFileDialog.getSaveFileName(
        parent,
        t(title_key),
        default_filename,
        t("print.filter"),
    )
    if not path:
        return None
    dest = Path(path)
    if dest.suffix.lower() != ".docx":
        dest = dest.with_suffix(".docx")

    try:
        result_path = builder(dest)
    except Exception as exc:
        logger.exception("Document generation failed")
        QMessageBox.critical(parent, t("error.title"), f"{t('error.unknown')}\n\n{exc}")
        return None

    QMessageBox.information(
        parent, t("info.saved"), t("print.saved_to", path=str(result_path))
    )
    if not open_document(result_path):
        # Best-effort — the file is saved regardless.
        logger.info("Document saved but not auto-opened: {}", result_path)
    return result_path


def reception_filename(patient_name: str, when: datetime | date) -> str:
    """Suggested filename for a reception form."""
    stamp = when.strftime("%Y%m%d")
    return t(
        "print.filename.reception", patient=_slugify(patient_name), date=stamp
    )


def receipt_filename(patient_name: str, when: datetime | date) -> str:
    stamp = when.strftime("%Y%m%d") if isinstance(when, (datetime, date)) else str(when)
    return t("print.filename.receipt", patient=_slugify(patient_name), date=stamp)


def patient_stats_filename(start: date, end: date) -> str:
    return t(
        "print.filename.patient_stats",
        start=start.strftime("%Y%m%d"),
        end=end.strftime("%Y%m%d"),
    )


def cashier_stats_filename(start: date, end: date) -> str:
    return t(
        "print.filename.cashier_stats",
        start=start.strftime("%Y%m%d"),
        end=end.strftime("%Y%m%d"),
    )


__all__ = [
    "cashier_stats_filename",
    "patient_stats_filename",
    "prompt_and_save",
    "receipt_filename",
    "reception_filename",
]
