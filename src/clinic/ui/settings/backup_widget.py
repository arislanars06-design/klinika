"""Reusable "Zaxira nusxalar" block used inside the Clinic tab.

It shows a list of existing backups, offers the four operations (create now,
export elsewhere, import from file, restore selected), and refreshes itself
after each action.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinic.config import settings
from clinic.i18n.translator import t, translator
from clinic.infrastructure import backup as backup_service


def _format_size(size_bytes: int) -> str:
    kb = size_bytes / 1024
    if kb < 1024:
        return f"{kb:,.1f} {t('settings.backup.size.kb')}".replace(",", " ")
    mb = kb / 1024
    return f"{mb:,.2f} {t('settings.backup.size.mb')}".replace(",", " ")


class BackupSection(QGroupBox):
    """Standalone group box \u2014 drop it into any settings tab layout."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        translator.language_changed.connect(self._retranslate)
        self._retranslate()
        self._reload()

    # ============================================================
    # UI
    # ============================================================

    def _build_ui(self) -> None:
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setStyleSheet("color: #616161;")

        self.table = QTableWidget(0, 3)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.empty_label = QLabel()
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #9e9e9e; padding: 8px;")

        self.create_btn = QPushButton()
        self.export_btn = QPushButton()
        self.import_btn = QPushButton()
        self.restore_btn = QPushButton()
        self.create_btn.clicked.connect(self._on_create)
        self.export_btn.clicked.connect(self._on_export)
        self.import_btn.clicked.connect(self._on_import)
        self.restore_btn.clicked.connect(self._on_restore_selected)

        buttons = QHBoxLayout()
        buttons.addWidget(self.create_btn)
        buttons.addWidget(self.export_btn)
        buttons.addSpacing(16)
        buttons.addWidget(self.restore_btn)
        buttons.addWidget(self.import_btn)
        buttons.addStretch(1)

        outer = QVBoxLayout(self)
        outer.addWidget(self.description)
        outer.addLayout(buttons)
        outer.addWidget(self.table, 1)
        outer.addWidget(self.empty_label)

    # ============================================================
    # Data
    # ============================================================

    def _reload(self) -> None:
        try:
            entries = backup_service.list_backups()
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            entries = []

        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            date_item = QTableWidgetItem(entry.created_on.strftime("%d.%m.%Y"))
            date_item.setData(Qt.ItemDataRole.UserRole, str(entry.path))
            name_item = QTableWidgetItem(entry.filename)
            size_item = QTableWidgetItem(_format_size(entry.size_bytes))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 0, date_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, size_item)

        self.empty_label.setVisible(not entries)

    def _selected_path(self) -> Path | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        raw = item.data(Qt.ItemDataRole.UserRole)
        return Path(raw) if raw else None

    # ============================================================
    # Actions
    # ============================================================

    def _on_create(self) -> None:
        try:
            entry = backup_service.force_daily_backup()
        except Exception as exc:
            logger.exception("Manual backup failed")
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        QMessageBox.information(
            self,
            self.title(),
            t("settings.backup.created_success", path=str(entry.path)),
        )
        self._reload()

    def _on_export(self) -> None:
        default_name = f"clinic_export_{date.today():%Y%m%d}.db"
        path, _ = QFileDialog.getSaveFileName(
            self,
            t("filedialog.save.backup"),
            default_name,
            t("filedialog.sqlite_filter"),
        )
        if not path:
            return
        try:
            entry = backup_service.manual_backup(path)
        except Exception as exc:
            logger.exception("Export backup failed")
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        QMessageBox.information(
            self,
            self.title(),
            t("settings.backup.created_success", path=str(entry.path)),
        )

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("filedialog.open.backup"),
            "",
            t("filedialog.sqlite_filter"),
        )
        if not path:
            return
        self._run_restore(Path(path))

    def _on_restore_selected(self) -> None:
        source = self._selected_path()
        if source is None:
            return
        self._run_restore(source)

    def _run_restore(self, source: Path) -> None:
        reply = QMessageBox.question(
            self,
            t("settings.backup.confirm_restore"),
            t("settings.backup.confirm_restore_details"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            backup_service.restore_from(source)
        except Exception as exc:
            logger.exception("Restore failed")
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        QMessageBox.information(
            self,
            self.title(),
            t("settings.backup.restored_success"),
        )
        self._reload()

    # ============================================================
    # i18n
    # ============================================================

    def _retranslate(self, *_args: object) -> None:
        self.setTitle(t("settings.backup.title"))
        self.description.setText(
            t("settings.backup.description", days=settings.backup_retention_days)
        )
        self.empty_label.setText(t("settings.backup.no_backups"))
        self.create_btn.setText("\u2795  " + t("settings.backup.create_now"))
        self.export_btn.setText(t("settings.backup.export"))
        self.import_btn.setText(t("settings.backup.import"))
        self.restore_btn.setText(t("common.restore") if False else t("settings.backup.confirm_restore"))
        self.table.setHorizontalHeaderLabels(
            [
                t("settings.backup.column.date"),
                t("settings.backup.column.filename"),
                t("settings.backup.column.size"),
            ]
        )
        if self.table.rowCount():
            self._reload()


__all__ = ["BackupSection"]
