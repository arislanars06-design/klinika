"""Cashier window: choose a patient and services, save one receipt."""

from __future__ import annotations

from decimal import Decimal

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinic.domain import cashier_service, patient_service, reception_service, service_service
from clinic.domain.dto import (
    CashierItemInput,
    CashierPaymentInput,
    PatientDTO,
    ReceptionDTO,
    ServiceDTO,
)
from clinic.i18n.translator import t, translator
from clinic.infrastructure.validators import ValidationError


def _format_money(value: Decimal | float) -> str:
    v = float(value)
    if v == int(v):
        return f"{int(v):,}".replace(",", " ")
    return f"{v:,.2f}".replace(",", " ")


class CashierWindow(QDialog):
    """Cashier form — one payment per open dialog.

    Callers may pre-seed the patient / reception via constructor kwargs so
    "\U0001F4B0 Kassa" from the Reception window jumps straight into an
    already-selected receipt.
    """

    saved = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        patient_id: int | None = None,
        reception_id: int | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("cashier.title"))
        self.setMinimumSize(880, 620)

        self._patient: PatientDTO | None = None
        self._receptions: list[ReceptionDTO] = []
        self._services: list[ServiceDTO] = []

        self._build_ui()
        self._reload_services()
        translator.language_changed.connect(self._retranslate)
        self._retranslate()

        if patient_id is not None:
            self._set_patient(patient_id)
        if reception_id is not None and self._patient is not None:
            idx = self.reception_combo.findData(reception_id)
            if idx >= 0:
                self.reception_combo.setCurrentIndex(idx)

    # ============================================================
    # UI construction
    # ============================================================

    def _build_ui(self) -> None:
        # ----- top header -----
        self.title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.stats_btn = QPushButton()
        self.stats_btn.clicked.connect(self._on_stats)

        top_row = QHBoxLayout()
        top_row.addWidget(self.title_label)
        top_row.addStretch(1)
        top_row.addWidget(self.stats_btn)

        # ----- patient / reception -----
        self.patient_group = QGroupBox()
        pg = QVBoxLayout(self.patient_group)

        self.patient_label = QLabel()
        self.patient_label.setWordWrap(True)
        self.select_patient_btn = QPushButton()
        self.select_patient_btn.clicked.connect(self._pick_patient)

        row1 = QHBoxLayout()
        row1.addWidget(self.patient_label, 1)
        row1.addWidget(self.select_patient_btn)

        self.reception_label = QLabel()
        self.reception_combo = QComboBox()
        self.reception_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

        row2 = QHBoxLayout()
        row2.addWidget(self.reception_label)
        row2.addWidget(self.reception_combo, 1)
        pg.addLayout(row1)
        pg.addLayout(row2)

        # ----- services / items -----
        self.items_group = QGroupBox()
        ig = QVBoxLayout(self.items_group)

        add_row = QHBoxLayout()
        self.service_combo = QComboBox()
        self.service_combo.setMinimumWidth(280)
        self.add_service_btn = QPushButton()
        self.add_service_btn.clicked.connect(self._add_item)
        add_row.addWidget(self.service_combo, 1)
        add_row.addWidget(self.add_service_btn)

        self.items_table = QTableWidget(0, 6)
        self.items_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.items_table.verticalHeader().setVisible(False)
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # #
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # service
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # qty
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # price
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # total
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # remove
        ig.addLayout(add_row)
        ig.addWidget(self.items_table, 1)

        # Grand total + note
        self.total_label = QLabel()
        total_font = QFont()
        total_font.setPointSize(16)
        total_font.setBold(True)
        self.total_label.setFont(total_font)
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.note_label = QLabel()
        self.note_edit = QLineEdit()

        # Buttons
        self.save_btn = QPushButton()
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._on_save)
        self.receipt_btn = QPushButton()
        self.receipt_btn.clicked.connect(self._on_receipt)
        buttons = QDialogButtonBox()
        buttons.addButton(self.receipt_btn, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.addButton(self.save_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        close_btn = buttons.addButton(QDialogButtonBox.StandardButton.Close)
        close_btn.clicked.connect(self.reject)
        self.close_btn = close_btn

        # Assemble
        outer = QVBoxLayout(self)
        outer.addLayout(top_row)
        outer.addWidget(self.patient_group)
        outer.addWidget(self.items_group, 1)
        outer.addWidget(self.total_label)
        outer.addWidget(self.note_label)
        outer.addWidget(self.note_edit)
        outer.addWidget(buttons)

    # ============================================================
    # Patient / reception
    # ============================================================

    def _pick_patient(self) -> None:
        from clinic.ui.cashier.patient_picker import PatientPickerDialog

        dlg = PatientPickerDialog(self)
        if dlg.exec() and dlg.selected_patient_id is not None:
            self._set_patient(dlg.selected_patient_id)

    def _set_patient(self, patient_id: int) -> None:
        try:
            patient = patient_service.get(patient_id)
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        if patient is None:
            return
        self._patient = patient
        self._receptions = reception_service.list_for_patient(patient_id)
        self.patient_label.setText(f"\U0001F464  {patient.full_name} ({patient.birth_year})")
        self._populate_reception_combo()
        self.select_patient_btn.setText(t("cashier.patient.change"))

    def _populate_reception_combo(self) -> None:
        self.reception_combo.blockSignals(True)
        self.reception_combo.clear()
        self.reception_combo.addItem(t("cashier.reception.none"), None)
        for r in self._receptions:
            label = f"{r.reception_date.strftime('%Y-%m-%d')} — {r.diagnosis}"
            self.reception_combo.addItem(label, r.id)
        # Default to the most recent reception when there is one.
        if self._receptions:
            self.reception_combo.setCurrentIndex(1)
        self.reception_combo.blockSignals(False)

    # ============================================================
    # Services / items
    # ============================================================

    def _reload_services(self) -> None:
        try:
            self._services = service_service.list_all(active_only=True)
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            self._services = []
        self._populate_service_combo()

    def _populate_service_combo(self) -> None:
        self.service_combo.blockSignals(True)
        self.service_combo.clear()
        if not self._services:
            self.service_combo.addItem(t("cashier.no_services_active"), None)
            self.service_combo.setEnabled(False)
            self.add_service_btn.setEnabled(False)
        else:
            self.service_combo.setEnabled(True)
            self.add_service_btn.setEnabled(True)
            currency = t("cashier.currency")
            for svc in self._services:
                label = f"{svc.display_name(translator.language)} — {_format_money(svc.price)} {currency}"
                self.service_combo.addItem(label, svc.id)
        self.service_combo.blockSignals(False)

    def _add_item(self) -> None:
        service_id = self.service_combo.currentData()
        if service_id is None:
            return
        service = next((s for s in self._services if s.id == service_id), None)
        if service is None:
            return
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        self._render_item_row(row, service, quantity=1)
        self._recalc_total()

    def _render_item_row(self, row: int, service: ServiceDTO, quantity: int) -> None:
        num_item = QTableWidgetItem(str(row + 1))
        num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        service_item = QTableWidgetItem(service.display_name(translator.language))
        service_item.setData(Qt.ItemDataRole.UserRole, service.id)

        qty_spin = QSpinBox()
        qty_spin.setRange(1, 999)
        qty_spin.setValue(quantity)
        qty_spin.valueChanged.connect(lambda _v, r=row: self._on_qty_changed(r))

        currency = t("cashier.currency")
        price_item = QTableWidgetItem(f"{_format_money(service.price)} {currency}")
        price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        price_item.setData(Qt.ItemDataRole.UserRole, str(service.price))

        total_item = QTableWidgetItem()
        total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        remove_btn = QPushButton("\U0001F5D1")
        remove_btn.setToolTip(t("cashier.remove_row"))
        remove_btn.setFixedWidth(36)
        remove_btn.clicked.connect(lambda: self._remove_row(service_item))

        self.items_table.setItem(row, 0, num_item)
        self.items_table.setItem(row, 1, service_item)
        self.items_table.setCellWidget(row, 2, qty_spin)
        self.items_table.setItem(row, 3, price_item)
        self.items_table.setItem(row, 4, total_item)
        self.items_table.setCellWidget(row, 5, remove_btn)

        self._update_row_total(row)

    def _on_qty_changed(self, row: int) -> None:
        self._update_row_total(row)
        self._recalc_total()

    def _update_row_total(self, row: int) -> None:
        price_item = self.items_table.item(row, 3)
        qty_widget = self.items_table.cellWidget(row, 2)
        if price_item is None or qty_widget is None:
            return
        price = Decimal(price_item.data(Qt.ItemDataRole.UserRole) or "0")
        qty = int(qty_widget.value())
        total = price * qty
        currency = t("cashier.currency")
        total_item = self.items_table.item(row, 4)
        if total_item is None:
            total_item = QTableWidgetItem()
            self.items_table.setItem(row, 4, total_item)
        total_item.setText(f"{_format_money(total)} {currency}")

    def _remove_row(self, service_item: QTableWidgetItem) -> None:
        row = service_item.row()
        self.items_table.removeRow(row)
        # Renumber remaining rows
        for r in range(self.items_table.rowCount()):
            self.items_table.item(r, 0).setText(str(r + 1))
        self._recalc_total()

    def _recalc_total(self) -> None:
        total = Decimal("0")
        for row in range(self.items_table.rowCount()):
            price_item = self.items_table.item(row, 3)
            qty_widget = self.items_table.cellWidget(row, 2)
            if price_item is None or qty_widget is None:
                continue
            price = Decimal(price_item.data(Qt.ItemDataRole.UserRole) or "0")
            total += price * int(qty_widget.value())
        currency = t("cashier.currency")
        self.total_label.setText(
            f"{t('cashier.grand_total')}: {_format_money(total)} {currency}"
        )

    def _collect_items(self) -> list[CashierItemInput]:
        items: list[CashierItemInput] = []
        for row in range(self.items_table.rowCount()):
            service_item = self.items_table.item(row, 1)
            qty_widget = self.items_table.cellWidget(row, 2)
            if service_item is None or qty_widget is None:
                continue
            service_id = int(service_item.data(Qt.ItemDataRole.UserRole))
            items.append(CashierItemInput(service_id=service_id, quantity=int(qty_widget.value())))
        return items

    # ============================================================
    # Save / receipt
    # ============================================================

    def _on_save(self) -> None:
        if self._patient is None:
            QMessageBox.warning(self, t("error.title"), t("cashier.patient.select"))
            return
        items = self._collect_items()
        payment = CashierPaymentInput(
            patient_id=self._patient.id,
            reception_id=self.reception_combo.currentData(),
            items=items,
            note=self.note_edit.text() or None,
        )
        try:
            cashier_service.save_payment(payment)
        except ValidationError as ve:
            first = next(iter(ve.errors.values()))
            QMessageBox.warning(
                self,
                t("error.title"),
                t(first.message_key, **first.params),
            )
            return
        except Exception as exc:
            logger.exception("Cashier save failed")
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        QMessageBox.information(self, t("cashier.title"), t("cashier.saved"))
        self.saved.emit()
        self.accept()

    def _on_receipt(self) -> None:
        QMessageBox.information(self, t("cashier.receipt"), t("info.not_implemented"))

    def _on_stats(self) -> None:
        from clinic.ui.cashier.stats_widget import CashierStatsDialog

        CashierStatsDialog(self).exec()

    # ============================================================
    # i18n
    # ============================================================

    def _retranslate(self, *_args: object) -> None:
        self.setWindowTitle(t("cashier.title"))
        self.title_label.setText(t("cashier.title"))
        self.stats_btn.setText(f"\U0001F4CA  {t('cashier.stats')}")
        self.patient_group.setTitle(t("cashier.patient"))
        self.reception_label.setText(t("cashier.reception") + ":")
        if self._patient is None:
            self.patient_label.setText("—")
            self.select_patient_btn.setText(t("cashier.patient.select"))
        else:
            self.select_patient_btn.setText(t("cashier.patient.change"))
        self.items_group.setTitle(t("cashier.add_service"))
        self.add_service_btn.setText("+  " + t("cashier.add_service"))
        self.items_table.setHorizontalHeaderLabels(
            [
                t("cashier.column.num"),
                t("cashier.column.service"),
                t("cashier.column.quantity"),
                t("cashier.column.price"),
                t("cashier.column.total"),
                t("cashier.column.remove"),
            ]
        )
        self.note_label.setText(t("cashier.note"))
        self.save_btn.setText("\U0001F4BE  " + t("cashier.save"))
        self.receipt_btn.setText("\U0001F5A8  " + t("cashier.receipt"))
        self.close_btn.setText(t("common.close"))
        self._populate_service_combo()
        self._recalc_total()


__all__ = ["CashierWindow"]
