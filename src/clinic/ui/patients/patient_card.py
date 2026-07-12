"""Patient card dialog — one-page view of everything about a single patient."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
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

from clinic.domain import patient_service, reception_service
from clinic.domain.dto import PatientDetail
from clinic.i18n.translator import t, translator


def _format_money(value: Decimal | float) -> str:
    v = float(value)
    if v == int(v):
        return f"{int(v):,}".replace(",", " ")
    return f"{v:,.2f}".replace(",", " ")


class PatientCardDialog(QDialog):
    """Dialog showing a patient's full history and payments."""

    data_changed = Signal()

    def __init__(self, patient_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._patient_id = patient_id
        self._detail: PatientDetail | None = None

        self.setWindowTitle(t("patients.card.title"))
        self.setMinimumSize(760, 620)

        self._build_ui()
        translator.language_changed.connect(self._reload)
        self._reload()

    # ============================================================
    # UI construction
    # ============================================================

    def _build_ui(self) -> None:
        # ----- header -----
        self.name_label = QLabel()
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        self.name_label.setFont(font)

        self.age_label = QLabel()
        self.phone_label = QLabel()
        self.address_label = QLabel()
        self.address_label.setWordWrap(True)

        header_grid = QVBoxLayout()
        header_grid.addWidget(self.name_label)
        header_grid.addWidget(self.age_label)
        header_grid.addWidget(self.phone_label)
        header_grid.addWidget(self.address_label)

        # ----- receptions table -----
        self.receptions_group = QGroupBox()
        rlayout = QVBoxLayout(self.receptions_group)
        self.receptions_table = QTableWidget(0, 5)
        self.receptions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.receptions_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.receptions_table.verticalHeader().setVisible(False)
        r_header = self.receptions_table.horizontalHeader()
        r_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # date
        r_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # diagnosis
        r_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # doctor
        r_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # complaints count
        r_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # actions
        self.receptions_empty_label = QLabel()
        self.receptions_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.receptions_empty_label.setStyleSheet("color: #9e9e9e; padding: 8px;")
        rlayout.addWidget(self.receptions_table)
        rlayout.addWidget(self.receptions_empty_label)

        # ----- payments table -----
        self.payments_group = QGroupBox()
        playout = QVBoxLayout(self.payments_group)
        self.payments_table = QTableWidget(0, 5)
        self.payments_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.payments_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.payments_table.verticalHeader().setVisible(False)
        p_header = self.payments_table.horizontalHeader()
        p_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # date
        p_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # service
        p_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # qty
        p_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # price
        p_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # total
        self.payments_empty_label = QLabel()
        self.payments_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.payments_empty_label.setStyleSheet("color: #9e9e9e; padding: 8px;")
        self.total_paid_label = QLabel()
        total_font = QFont()
        total_font.setBold(True)
        self.total_paid_label.setFont(total_font)
        self.total_paid_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        playout.addWidget(self.payments_table)
        playout.addWidget(self.payments_empty_label)
        playout.addWidget(self.total_paid_label)

        # ----- buttons -----
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        self._close_btn = button_box.button(QDialogButtonBox.StandardButton.Close)

        # ----- assemble -----
        outer = QVBoxLayout(self)
        outer.addLayout(header_grid)
        outer.addWidget(self.receptions_group, 3)
        outer.addWidget(self.payments_group, 2)
        outer.addWidget(button_box)

    # ============================================================
    # Data
    # ============================================================

    def _reload(self, *_args: object) -> None:
        try:
            self._detail = patient_service.get_detail(self._patient_id)
        except Exception as exc:
            logger.exception("Patient detail failed")
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            self._detail = None
        self._render()

    def _render(self) -> None:
        d = self._detail
        if d is None:
            self.name_label.setText("—")
            return

        p = d.patient
        self.name_label.setText(p.full_name)
        self.age_label.setText(
            f"{datetime.now().year - p.birth_year} {t('patients.card.age')} · {p.birth_year}"
        )
        self.phone_label.setText("\u260E  " + (p.phone or "—"))
        self.address_label.setText("\U0001F4CD  " + (p.address or "—"))

        self.receptions_group.setTitle(t("patients.card.receptions"))
        self.payments_group.setTitle(t("patients.card.payments"))
        self.receptions_table.setHorizontalHeaderLabels(
            [
                t("reception.date"),
                t("reception.diagnosis"),
                t("reception.doctor"),
                t("reception.complaints"),
                t("patients.column.actions"),
            ]
        )
        self.payments_table.setHorizontalHeaderLabels(
            [
                t("reception.date"),
                t("cashier.column.service"),
                t("cashier.column.quantity"),
                t("cashier.column.price"),
                t("cashier.column.total"),
            ]
        )

        # ----- receptions -----
        self.receptions_table.setRowCount(len(d.receptions))
        for row, rec in enumerate(d.receptions):
            date_item = QTableWidgetItem(rec.reception_date.strftime("%Y-%m-%d %H:%M"))
            date_item.setData(Qt.ItemDataRole.UserRole, rec.id)
            diag_item = QTableWidgetItem(rec.diagnosis)
            doctor_name = d.doctor_names.get(rec.doctor_id, str(rec.doctor_id))
            doctor_item = QTableWidgetItem(doctor_name)
            complaints_count = len(rec.complaints_codes or [])
            complaints_item = QTableWidgetItem(str(complaints_count))
            complaints_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            for c, cell in enumerate((date_item, diag_item, doctor_item, complaints_item)):
                self.receptions_table.setItem(row, c, cell)
            self.receptions_table.setCellWidget(
                row, 4, self._build_reception_actions(rec.id)
            )
        self.receptions_empty_label.setVisible(not d.receptions)
        self.receptions_empty_label.setText(t("patients.card.no_receptions"))

        # ----- payments -----
        self.payments_table.setRowCount(len(d.payments))
        currency = t("cashier.currency")
        for row, pay in enumerate(d.payments):
            date_item = QTableWidgetItem(pay.paid_at.strftime("%Y-%m-%d %H:%M"))
            svc_item = QTableWidgetItem(pay.service_name(translator.language))
            qty_item = QTableWidgetItem(str(pay.quantity))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            price_item = QTableWidgetItem(f"{_format_money(pay.price_at_moment)} {currency}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            total_item = QTableWidgetItem(f"{_format_money(pay.total)} {currency}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            for c, cell in enumerate((date_item, svc_item, qty_item, price_item, total_item)):
                self.payments_table.setItem(row, c, cell)
        self.payments_empty_label.setVisible(not d.payments)
        self.payments_empty_label.setText(t("patients.card.no_payments"))

        self.total_paid_label.setText(
            f"{t('patients.card.total_paid')}: {_format_money(d.total_paid)} {currency}"
        )
        self._close_btn.setText(t("common.close"))

    # ============================================================
    # Reception row actions
    # ============================================================

    def _build_reception_actions(self, reception_id: int) -> QWidget:
        wrapper = QWidget()
        h = QHBoxLayout(wrapper)
        h.setContentsMargins(2, 0, 2, 0)
        h.setSpacing(2)
        edit_btn = QPushButton("\u270F")
        edit_btn.setToolTip(t("patients.card.reception.edit"))
        edit_btn.setFixedWidth(32)
        edit_btn.clicked.connect(lambda: self._edit_reception(reception_id))
        del_btn = QPushButton("\U0001F5D1")
        del_btn.setToolTip(t("patients.card.reception.delete"))
        del_btn.setFixedWidth(32)
        del_btn.clicked.connect(lambda: self._delete_reception(reception_id))
        h.addWidget(edit_btn)
        h.addWidget(del_btn)
        return wrapper

    def _edit_reception(self, reception_id: int) -> None:
        from clinic.ui.reception import ReceptionWindow

        window = ReceptionWindow(self, edit_reception_id=reception_id)
        if window.exec() == QDialog.DialogCode.Accepted:
            self._reload()
            self.data_changed.emit()

    def _delete_reception(self, reception_id: int) -> None:
        reply = QMessageBox.question(
            self,
            t("common.confirm"),
            t("patients.card.confirm_delete_reception"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            reception_service.delete(reception_id)
        except Exception as exc:
            logger.exception("Reception delete failed")
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        self._reload()
        self.data_changed.emit()


__all__ = ["PatientCardDialog"]
