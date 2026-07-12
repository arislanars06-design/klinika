"""Small modal dialog to pick a patient by name search."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinic.domain import patient_service
from clinic.i18n.translator import t


class PatientPickerDialog(QDialog):
    """Dialog with a search field + list of matching patients."""

    SEARCH_DEBOUNCE_MS = 200

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("cashier.patient.select"))
        self.setMinimumSize(520, 400)
        self.selected_patient_id: int | None = None

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(self.SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._reload)

        self.title_label = QLabel(t("cashier.patient"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(t("patients.search.placeholder"))
        self.search_edit.textEdited.connect(lambda _: self._search_timer.start())

        header_row = QHBoxLayout()
        header_row.addWidget(self.title_label)
        header_row.addWidget(self.search_edit, 1)

        self.table = QTableWidget(0, 4)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalHeaderLabels(
            [
                t("reception.patient.full_name"),
                t("reception.patient.birth_year"),
                t("reception.patient.phone"),
                t("reception.patient.address"),
            ]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.itemDoubleClicked.connect(lambda _: self._accept_selected())

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_selected)
        buttons.rejected.connect(self.reject)

        outer = QVBoxLayout(self)
        outer.addLayout(header_row)
        outer.addWidget(self.table, 1)
        outer.addWidget(buttons)

        self._reload()

    def _reload(self) -> None:
        text = self.search_edit.text().strip() or None
        try:
            page = patient_service.paginated_search(
                text=text, page=1, page_size=50
            )
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        self.table.setRowCount(len(page.items))
        for row, item in enumerate(page.items):
            p = item.patient
            name_item = QTableWidgetItem(p.full_name)
            name_item.setData(Qt.ItemDataRole.UserRole, p.id)
            year_item = QTableWidgetItem(str(p.birth_year))
            phone_item = QTableWidgetItem(p.phone or "—")
            addr_item = QTableWidgetItem(p.address or "—")
            for c, cell in enumerate((name_item, year_item, phone_item, addr_item)):
                self.table.setItem(row, c, cell)

    def _accept_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        name_item = self.table.item(row, 0)
        if name_item is None:
            return
        patient_id = name_item.data(Qt.ItemDataRole.UserRole)
        if patient_id is None:
            return
        self.selected_patient_id = int(patient_id)
        self.accept()


__all__ = ["PatientPickerDialog"]
