"""Settings → Doctors tab: table + add/edit/archive."""

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

from clinic.domain import doctor_service
from clinic.domain.dto import DoctorDTO
from clinic.i18n.translator import t, translator
from clinic.ui.widgets.edit_dialogs import DoctorDialog


class DoctorsTab(QWidget):
    """Table of doctors with add/edit/archive+restore actions."""

    COLUMNS = ("name", "phone", "status")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._doctors: list[DoctorDTO] = []
        self._build_ui()
        self._reload()
        translator.language_changed.connect(self._retranslate)

    # ----- UI -----

    def _build_ui(self) -> None:
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemDoubleClicked.connect(lambda _: self._on_edit())

        # Buttons
        self.add_btn = QPushButton()
        self.edit_btn = QPushButton()
        self.archive_btn = QPushButton()
        self.restore_btn = QPushButton()

        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn.clicked.connect(self._on_edit)
        self.archive_btn.clicked.connect(lambda: self._set_active(False))
        self.restore_btn.clicked.connect(lambda: self._set_active(True))

        button_row = QHBoxLayout()
        button_row.addWidget(self.add_btn)
        button_row.addWidget(self.edit_btn)
        button_row.addWidget(self.archive_btn)
        button_row.addWidget(self.restore_btn)
        button_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addLayout(button_row)
        layout.addWidget(self.table)

        self._retranslate()

    def _retranslate(self, *_args: object) -> None:
        self.add_btn.setText(t("settings.doctors.add"))
        self.edit_btn.setText(t("settings.doctors.edit"))
        self.archive_btn.setText(t("settings.doctors.archive"))
        self.restore_btn.setText(t("settings.doctors.restore"))
        self.table.setHorizontalHeaderLabels(
            [
                t("settings.doctors.column.name"),
                t("settings.doctors.column.phone"),
                t("settings.doctors.column.status"),
            ]
        )
        # Refresh status column labels
        self._reload()

    # ----- data -----

    def _reload(self) -> None:
        try:
            self._doctors = doctor_service.list_all(active_only=False)
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            self._doctors = []

        self.table.setRowCount(len(self._doctors))
        for row, doc in enumerate(self._doctors):
            name_item = QTableWidgetItem(doc.full_name)
            name_item.setData(Qt.ItemDataRole.UserRole, doc.id)
            phone_item = QTableWidgetItem(doc.phone or "—")
            status_key = "settings.status.active" if doc.is_active else "settings.status.archived"
            status_item = QTableWidgetItem(t(status_key))
            if not doc.is_active:
                for it in (name_item, phone_item, status_item):
                    it.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, phone_item)
            self.table.setItem(row, 2, status_item)

    def _selected_doctor(self) -> DoctorDTO | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._doctors):
            return None
        return self._doctors[row]

    # ----- actions -----

    def _on_add(self) -> None:
        dialog = DoctorDialog(parent=self)
        if dialog.exec() and dialog.result_dto():
            self._reload()

    def _on_edit(self) -> None:
        doctor = self._selected_doctor()
        if doctor is None:
            return
        dialog = DoctorDialog(doctor, parent=self)
        if dialog.exec() and dialog.result_dto():
            self._reload()

    def _set_active(self, active: bool) -> None:
        doctor = self._selected_doctor()
        if doctor is None:
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
            doctor_service.set_active(doctor.id, active)
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        self._reload()
