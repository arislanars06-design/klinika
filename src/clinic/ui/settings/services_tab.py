"""Settings → Services tab: table + add/edit/archive."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinic.domain import service_service
from clinic.domain.dto import ServiceDTO
from clinic.i18n.translator import t, translator
from clinic.ui.widgets.edit_dialogs import ServiceDialog


def _format_price(price) -> str:  # type: ignore[no-untyped-def]
    """Render a Decimal with thousand separators, dropping trailing zeros."""
    try:
        value = float(price)
    except (TypeError, ValueError):
        return str(price)
    if value == int(value):
        return f"{int(value):,}".replace(",", " ")
    return f"{value:,.2f}".replace(",", " ")


class ServicesTab(QWidget):
    """Table of billable services with CRUD."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._services: list[ServiceDTO] = []
        self._build_ui()
        self._reload()
        translator.language_changed.connect(self._retranslate)

    def _build_ui(self) -> None:
        self.table = QTableWidget(0, 4)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemDoubleClicked.connect(lambda _: self._on_edit())

        self.add_btn = QPushButton()
        self.edit_btn = QPushButton()
        self.archive_btn = QPushButton()
        self.restore_btn = QPushButton()
        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn.clicked.connect(self._on_edit)
        self.archive_btn.clicked.connect(lambda: self._set_active(False))
        self.restore_btn.clicked.connect(lambda: self._set_active(True))

        row = QHBoxLayout()
        row.addWidget(self.add_btn)
        row.addWidget(self.edit_btn)
        row.addWidget(self.archive_btn)
        row.addWidget(self.restore_btn)
        row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addLayout(row)
        layout.addWidget(self.table)

        self._retranslate()

    def _retranslate(self, *_args: object) -> None:
        self.add_btn.setText(t("settings.services.add"))
        self.edit_btn.setText(t("settings.services.edit"))
        self.archive_btn.setText(t("settings.services.archive"))
        self.restore_btn.setText(t("settings.services.restore"))
        self.table.setHorizontalHeaderLabels(
            [
                t("settings.services.column.name_uz"),
                t("settings.services.column.name_ru"),
                t("settings.services.column.price"),
                t("settings.services.column.status"),
            ]
        )
        self._reload()

    def _reload(self) -> None:
        try:
            self._services = service_service.list_all(active_only=False)
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            self._services = []

        currency = " " + t("cashier.currency")
        self.table.setRowCount(len(self._services))
        for row, svc in enumerate(self._services):
            name_uz = QTableWidgetItem(svc.name_uz)
            name_uz.setData(Qt.ItemDataRole.UserRole, svc.id)
            name_ru = QTableWidgetItem(svc.name_ru)
            price = QTableWidgetItem(_format_price(svc.price) + currency)
            price.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            status_key = "settings.status.active" if svc.is_active else "settings.status.archived"
            status = QTableWidgetItem(t(status_key))
            if not svc.is_active:
                for it in (name_uz, name_ru, price, status):
                    it.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 0, name_uz)
            self.table.setItem(row, 1, name_ru)
            self.table.setItem(row, 2, price)
            self.table.setItem(row, 3, status)

    def _selected(self) -> ServiceDTO | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._services):
            return None
        return self._services[row]

    def _on_add(self) -> None:
        dialog = ServiceDialog(parent=self)
        if dialog.exec() and dialog.result_dto():
            self._reload()

    def _on_edit(self) -> None:
        svc = self._selected()
        if svc is None:
            return
        dialog = ServiceDialog(svc, parent=self)
        if dialog.exec() and dialog.result_dto():
            self._reload()

    def _set_active(self, active: bool) -> None:
        svc = self._selected()
        if svc is None:
            return
        confirm_key = "confirm.restore" if active else "confirm.archive"
        reply = QMessageBox.question(
            self,
            t("common.confirm"),
            t(confirm_key),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            service_service.set_active(svc.id, active)
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        self._reload()
