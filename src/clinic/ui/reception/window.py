"""Top-level Reception ("Qabulni boshlash") window.

Combines the patient, complaints, and LOR STATUS widgets into a single form
with a scrollable body, plus anamnesis / diagnosis / recommendation / doctor
fields. On Save it hands a :class:`ReceptionInput` to
:mod:`clinic.domain.reception_service`.
"""

from __future__ import annotations

from datetime import datetime

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clinic.domain import doctor_service, reception_service
from clinic.domain.dto import DoctorDTO, PatientInput, ReceptionInput
from clinic.i18n.translator import t, translator
from clinic.infrastructure.validators import ValidationError
from clinic.ui.reception.complaints_widget import ComplaintsBlock
from clinic.ui.reception.lor_status_widget import LorStatusBlock
from clinic.ui.reception.patient_widget import PatientBlock


class ReceptionWindow(QDialog):
    """Full reception form as a modal dialog."""

    #: Emitted after a successful save with the created reception id.
    saved = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dirty = False
        self._doctors: list[DoctorDTO] = []
        self._last_reception_id: int | None = None

        self.setWindowTitle(t("reception.title"))
        self.setMinimumSize(960, 720)

        self._build_ui()
        self._load_doctors()
        translator.language_changed.connect(self._retranslate)
        self._retranslate()

    # ============================================================
    # UI construction
    # ============================================================

    def _build_ui(self) -> None:
        # ----- top bar -----
        self.date_edit = QDateTimeEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDateTime(datetime.now())
        self.date_edit.dateTimeChanged.connect(self._on_dirty)

        self.date_label = QLabel()
        top_row = QHBoxLayout()
        top_row.addWidget(self.date_label)
        top_row.addWidget(self.date_edit)
        top_row.addStretch(1)

        # ----- scrollable body -----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 12, 12, 12)
        body_layout.setSpacing(12)

        # Patient
        self.patient_group = QGroupBox()
        pg = QVBoxLayout(self.patient_group)
        self.patient_widget = PatientBlock()
        self.patient_widget.changed.connect(self._on_dirty)
        pg.addWidget(self.patient_widget)
        body_layout.addWidget(self.patient_group)

        # Complaints
        self.complaints_group = QGroupBox()
        cg = QVBoxLayout(self.complaints_group)
        self.complaints_widget = ComplaintsBlock()
        self.complaints_widget.changed.connect(self._on_dirty)
        cg.addWidget(self.complaints_widget)
        body_layout.addWidget(self.complaints_group)

        # Anamnesis
        self.anamnesis_group = QGroupBox()
        ag = QVBoxLayout(self.anamnesis_group)
        self.anamnesis_edit = QTextEdit()
        self.anamnesis_edit.setFixedHeight(72)
        self.anamnesis_edit.textChanged.connect(self._on_dirty)
        ag.addWidget(self.anamnesis_edit)
        body_layout.addWidget(self.anamnesis_group)

        # LOR STATUS
        self.lor_group = QGroupBox()
        lg = QVBoxLayout(self.lor_group)
        self.lor_widget = LorStatusBlock()
        self.lor_widget.changed.connect(self._on_dirty)
        lg.addWidget(self.lor_widget)
        body_layout.addWidget(self.lor_group)

        # Diagnosis
        self.diagnosis_group = QGroupBox()
        dg = QVBoxLayout(self.diagnosis_group)
        self.diagnosis_edit = QLineEdit()
        self.diagnosis_edit.textEdited.connect(self._on_dirty)
        self.diagnosis_error_label = QLabel()
        self.diagnosis_error_label.setStyleSheet("color: #c62828;")
        self.diagnosis_error_label.hide()
        dg.addWidget(self.diagnosis_edit)
        dg.addWidget(self.diagnosis_error_label)
        body_layout.addWidget(self.diagnosis_group)

        # Recommendation
        self.recommendation_group = QGroupBox()
        rg = QVBoxLayout(self.recommendation_group)
        self.recommendation_edit = QTextEdit()
        self.recommendation_edit.setFixedHeight(72)
        self.recommendation_edit.textChanged.connect(self._on_dirty)
        rg.addWidget(self.recommendation_edit)
        body_layout.addWidget(self.recommendation_group)

        # Doctor row
        self.doctor_group = QGroupBox()
        doctor_form = QFormLayout(self.doctor_group)
        self.doctor_combo = QComboBox()
        self.doctor_combo.currentIndexChanged.connect(self._on_doctor_changed)
        self.doctor_phone_label = QLabel("—")
        self.doctor_error_label = QLabel()
        self.doctor_error_label.setStyleSheet("color: #c62828;")
        self.doctor_error_label.hide()
        self.doctor_label_widget = QLabel()
        self.doctor_phone_label_widget = QLabel()
        doctor_form.addRow(self.doctor_label_widget, self.doctor_combo)
        doctor_form.addRow(self.doctor_phone_label_widget, self.doctor_phone_label)
        doctor_form.addRow("", self.doctor_error_label)
        body_layout.addWidget(self.doctor_group)

        body_layout.addStretch(1)
        scroll.setWidget(body)

        # ----- bottom buttons -----
        self.back_btn = QPushButton()
        self.back_btn.clicked.connect(self._on_back)
        self.save_btn = QPushButton()
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setDefault(True)
        self.print_btn = QPushButton()
        self.print_btn.clicked.connect(self._on_print)
        self.cashier_btn = QPushButton()
        self.cashier_btn.clicked.connect(self._on_cashier)

        buttons = QHBoxLayout()
        buttons.addWidget(self.back_btn)
        buttons.addStretch(1)
        buttons.addWidget(self.print_btn)
        buttons.addWidget(self.cashier_btn)
        buttons.addWidget(self.save_btn)

        outer = QVBoxLayout(self)
        outer.addLayout(top_row)
        outer.addWidget(scroll, 1)
        outer.addLayout(buttons)

    # ============================================================
    # Data
    # ============================================================

    def _load_doctors(self) -> None:
        try:
            self._doctors = doctor_service.list_all(active_only=True)
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            self._doctors = []
        self._populate_doctor_combo()

    def _populate_doctor_combo(self) -> None:
        current = self.doctor_combo.currentData()
        self.doctor_combo.blockSignals(True)
        self.doctor_combo.clear()
        self.doctor_combo.addItem(t("reception.doctor.select"), None)
        for doc in self._doctors:
            self.doctor_combo.addItem(doc.full_name, doc.id)
        # Restore previous selection if still present.
        if current is not None:
            idx = self.doctor_combo.findData(current)
            if idx >= 0:
                self.doctor_combo.setCurrentIndex(idx)
        self.doctor_combo.blockSignals(False)
        self._on_doctor_changed()

    def _on_doctor_changed(self, *_args: object) -> None:
        doctor_id = self.doctor_combo.currentData()
        phone = "—"
        for doc in self._doctors:
            if doc.id == doctor_id:
                phone = doc.phone or "—"
                break
        self.doctor_phone_label.setText(phone)
        self._on_dirty()

    # ============================================================
    # Dirty tracking
    # ============================================================

    def _on_dirty(self, *_args: object) -> None:
        self._dirty = True

    # ============================================================
    # Actions
    # ============================================================

    def _collect_input(self) -> ReceptionInput:
        name, year, address, phone = self.patient_widget.get_values()
        codes, details, note = self.complaints_widget.get_values()

        return ReceptionInput(
            patient=PatientInput(
                full_name=name,
                birth_year=year,
                address=address or None,
                phone=phone or None,
            ),
            patient_id=self.patient_widget.selected_patient_id(),
            doctor_id=self.doctor_combo.currentData(),
            reception_date=self.date_edit.dateTime().toPython(),
            complaints_codes=codes,
            complaints_details=details,
            complaints_note=note or None,
            anamnesis=self.anamnesis_edit.toPlainText().strip() or None,
            lor_status=self.lor_widget.get_values() or None,
            diagnosis=self.diagnosis_edit.text().strip(),
            recommendation=self.recommendation_edit.toPlainText().strip() or None,
        )

    def _on_save(self) -> None:
        self._clear_field_errors()
        data = self._collect_input()
        try:
            reception, _patient, _created = reception_service.save(data)
        except ValidationError as ve:
            self._apply_field_errors(ve)
            QMessageBox.warning(self, t("error.title"), t("error.validation"))
            return
        except Exception as exc:
            logger.exception("Reception save failed")
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return

        self._last_reception_id = reception.id
        self._dirty = False
        QMessageBox.information(self, t("reception.title"), t("reception.saved"))
        self.saved.emit(reception.id)
        self.accept()

    def _on_back(self) -> None:
        if not self._confirm_discard():
            return
        self.reject()

    def _on_print(self) -> None:
        QMessageBox.information(self, t("reception.print"), t("info.not_implemented"))

    def _on_cashier(self) -> None:
        QMessageBox.information(self, t("reception.to_cashier"), t("info.not_implemented"))

    def _confirm_discard(self) -> bool:
        if not self._dirty:
            return True
        reply = QMessageBox.question(
            self,
            t("common.confirm"),
            t("reception.discard_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()

    # ============================================================
    # Validation error mapping
    # ============================================================

    def _clear_field_errors(self) -> None:
        self.patient_widget.clear_errors()
        self.complaints_widget.set_error(False)
        self.diagnosis_error_label.hide()
        self.diagnosis_edit.setStyleSheet("")
        self.doctor_error_label.hide()

    def _apply_field_errors(self, ve: ValidationError) -> None:
        for field, err in ve.errors.items():
            message = t(err.message_key, **err.params)
            if field in {"full_name", "birth_year", "address", "phone"}:
                self.patient_widget.set_error(field, True)
            elif field == "complaints":
                self.complaints_widget.set_error(True)
            elif field == "diagnosis":
                self.diagnosis_error_label.setText(message)
                self.diagnosis_error_label.show()
                self.diagnosis_edit.setStyleSheet("border: 1px solid #c62828;")
            elif field == "doctor" or field == "patient":
                self.doctor_error_label.setText(message)
                self.doctor_error_label.show()

    # ============================================================
    # Retranslation
    # ============================================================

    def _retranslate(self, *_args: object) -> None:
        self.setWindowTitle(t("reception.title"))
        self.date_label.setText(t("reception.date"))
        self.patient_group.setTitle(t("reception.section.patient"))
        self.complaints_group.setTitle(t("reception.section.complaints"))
        self.anamnesis_group.setTitle(t("reception.section.anamnesis"))
        self.anamnesis_edit.setPlaceholderText(t("reception.anamnesis.placeholder"))
        self.lor_group.setTitle(t("reception.section.lor_status"))
        self.diagnosis_group.setTitle(t("reception.section.diagnosis"))
        self.diagnosis_edit.setPlaceholderText(t("reception.diagnosis.placeholder"))
        self.recommendation_group.setTitle(t("reception.section.recommendation"))
        self.recommendation_edit.setPlaceholderText(t("reception.recommendation.placeholder"))
        self.doctor_group.setTitle(t("reception.section.doctor"))
        self.doctor_label_widget.setText(t("reception.doctor"))
        self.doctor_phone_label_widget.setText(t("reception.doctor.phone"))
        # Refresh doctor combo placeholder
        if self.doctor_combo.count():
            self.doctor_combo.setItemText(0, t("reception.doctor.select"))
        self.back_btn.setText(t("common.back"))
        self.save_btn.setText(t("reception.save"))
        self.print_btn.setText(t("reception.print"))
        self.cashier_btn.setText(t("reception.to_cashier"))


__all__ = ["ReceptionWindow"]
