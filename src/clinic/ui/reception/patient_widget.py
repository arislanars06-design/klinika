"""Reception → Patient block: F.I.O with autocomplete, year, address, phone.

Emits :attr:`patient_selected` when the user picks an existing patient from
the search dropdown, and :attr:`changed` on any typing so the outer form can
mark itself dirty.
"""

from __future__ import annotations

from PySide6.QtCore import QStringListModel, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCompleter,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from clinic.domain import patient_service
from clinic.domain.dto import PatientDTO
from clinic.i18n.translator import t, translator
from clinic.infrastructure.validators import MIN_BIRTH_YEAR


class PatientBlock(QWidget):
    """Patient info form with real-time search over existing records."""

    #: Emitted when the user picks a suggestion. ``None`` means "new patient".
    patient_selected = Signal(object)
    #: Any field edit triggers this so the outer form can flip the dirty flag.
    changed = Signal()

    SEARCH_DEBOUNCE_MS = 250
    MIN_SEARCH_LENGTH = 2

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._patient_id: int | None = None
        self._suggestions: list[PatientDTO] = []

        # ----- widgets -----
        self.name_edit = QLineEdit()
        self.year_edit = QSpinBox()
        self.year_edit.setRange(MIN_BIRTH_YEAR, 2100)
        self.year_edit.setValue(1990)
        self.address_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #616161; font-style: italic;")

        # Completer for the name field
        self._completer_model = QStringListModel(self)
        self._completer = QCompleter(self._completer_model, self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._completer.activated.connect(self._on_completer_activated)
        self.name_edit.setCompleter(self._completer)

        # Debounced search
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(self.SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._perform_search)

        # ----- layout -----
        self.form = QFormLayout()
        self.form.addRow(t("reception.patient.full_name") + " *", self.name_edit)
        self.form.addRow(t("reception.patient.birth_year") + " *", self.year_edit)
        self.form.addRow(t("reception.patient.address"), self.address_edit)
        self.form.addRow(t("reception.patient.phone"), self.phone_edit)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(self.form)
        outer.addWidget(self.status_label)

        # ----- signals -----
        self.name_edit.textEdited.connect(self._on_name_edited)
        for w in (self.year_edit, self.address_edit, self.phone_edit):
            if hasattr(w, "textEdited"):
                w.textEdited.connect(lambda *_: self._mark_manual_edit())
            else:
                w.valueChanged.connect(lambda *_: self._mark_manual_edit())

        translator.language_changed.connect(self._retranslate)
        self._retranslate()

    # ============================================================
    # Public API
    # ============================================================

    def get_values(self) -> tuple[str, int, str, str]:
        return (
            self.name_edit.text().strip(),
            int(self.year_edit.value()),
            self.address_edit.text().strip(),
            self.phone_edit.text().strip(),
        )

    def selected_patient_id(self) -> int | None:
        """``None`` when the user is entering a brand-new patient."""
        return self._patient_id

    def clear(self) -> None:
        self.name_edit.clear()
        self.year_edit.setValue(1990)
        self.address_edit.clear()
        self.phone_edit.clear()
        self._patient_id = None
        self._suggestions = []
        self._completer_model.setStringList([])
        self._update_status_label()

    def set_patient(self, dto: PatientDTO) -> None:
        """Load an existing patient into the form silently (no ``changed`` emit)."""
        self._patient_id = dto.id
        self.name_edit.blockSignals(True)
        self.year_edit.blockSignals(True)
        self.address_edit.blockSignals(True)
        self.phone_edit.blockSignals(True)
        try:
            self.name_edit.setText(dto.full_name)
            self.year_edit.setValue(dto.birth_year)
            self.address_edit.setText(dto.address or "")
            self.phone_edit.setText(dto.phone or "")
        finally:
            self.name_edit.blockSignals(False)
            self.year_edit.blockSignals(False)
            self.address_edit.blockSignals(False)
            self.phone_edit.blockSignals(False)
        self._update_status_label()

    def set_error(self, field: str, has_error: bool) -> None:
        """Highlight a field when validation fails."""
        widget = {
            "full_name": self.name_edit,
            "birth_year": self.year_edit,
            "address": self.address_edit,
            "phone": self.phone_edit,
        }.get(field)
        if widget is None:
            return
        widget.setProperty("hasError", has_error)
        style = "border: 1px solid #c62828;" if has_error else ""
        widget.setStyleSheet(style)

    def clear_errors(self) -> None:
        for name in ("full_name", "birth_year", "address", "phone"):
            self.set_error(name, False)

    # ============================================================
    # Search & selection
    # ============================================================

    def _on_name_edited(self, _text: str) -> None:
        # Any manual typing invalidates a previously chosen existing patient.
        self._patient_id = None
        self._update_status_label()
        self.changed.emit()
        self._search_timer.start()

    def _mark_manual_edit(self) -> None:
        self.changed.emit()

    def _perform_search(self) -> None:
        query = self.name_edit.text().strip()
        if len(query) < self.MIN_SEARCH_LENGTH:
            self._suggestions = []
            self._completer_model.setStringList([])
            return
        try:
            self._suggestions = patient_service.search(query)
        except Exception:
            self._suggestions = []
        # Feed the completer with "F.I.O (year) — address" strings.
        self._completer_model.setStringList(
            [self._render_suggestion(s) for s in self._suggestions]
        )

    def _render_suggestion(self, dto: PatientDTO) -> str:
        line = f"{dto.full_name} ({dto.birth_year})"
        if dto.address:
            line += f" — {dto.address}"
        return line

    def _on_completer_activated(self, chosen_text: str) -> None:
        for dto in self._suggestions:
            if self._render_suggestion(dto) == chosen_text:
                self._apply_patient(dto)
                return

    def _apply_patient(self, dto: PatientDTO) -> None:
        self._patient_id = dto.id
        # Populate fields without re-triggering the search.
        self.name_edit.blockSignals(True)
        self.name_edit.setText(dto.full_name)
        self.name_edit.blockSignals(False)
        self.year_edit.blockSignals(True)
        self.year_edit.setValue(dto.birth_year)
        self.year_edit.blockSignals(False)
        self.address_edit.setText(dto.address or "")
        self.phone_edit.setText(dto.phone or "")
        self._update_status_label()
        self.patient_selected.emit(dto.id)
        self.changed.emit()

    def _update_status_label(self) -> None:
        if self._patient_id is not None:
            self.status_label.setText("\u2714  " + t("reception.patient.existing"))
        elif self.name_edit.text().strip():
            self.status_label.setText("\u2795  " + t("reception.patient.new"))
        else:
            self.status_label.setText("")

    # ============================================================
    # Retranslation
    # ============================================================

    def _retranslate(self, *_args: object) -> None:
        # Rewrite form labels in place
        rows = [
            "reception.patient.full_name",
            "reception.patient.birth_year",
            "reception.patient.address",
            "reception.patient.phone",
        ]
        for i, key in enumerate(rows):
            item = self.form.itemAt(i, QFormLayout.ItemRole.LabelRole)
            if item and item.widget():
                suffix = " *" if key in {"reception.patient.full_name", "reception.patient.birth_year"} else ""
                item.widget().setText(t(key) + suffix)
        self.name_edit.setPlaceholderText(t("reception.patient.search_placeholder"))
        self._update_status_label()
