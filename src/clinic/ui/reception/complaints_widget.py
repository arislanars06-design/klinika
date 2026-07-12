"""Reception → Complaints block: accordion of 4 sections + freeform note.

Layout:

* Four :class:`CollapsibleSection`s (ear/nose/pharynx/larynx) each containing
  a grid of checkboxes.
* When an item flagged ``has_discharge_type`` is checked, a discharge-type
  dropdown is enabled next to it (yiringli / seroz / …).
* Bottom: header showing the selected count + "Clear" button, and a freeform
  additional-complaints text box.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clinic.domain.catalog_loader import complaints_catalog, discharge_types_catalog
from clinic.i18n.translator import t, translator
from clinic.ui.widgets.collapsible import CollapsibleSection


class ComplaintsBlock(QWidget):
    """Structured complaint selection with discharge-type dropdowns and note."""

    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # code -> QCheckBox
        self._boxes: dict[str, QCheckBox] = {}
        # code -> QComboBox (for items with has_discharge_type)
        self._discharge_boxes: dict[str, QComboBox] = {}
        # code -> item metadata (dict from catalog)
        self._items: dict[str, dict] = {}
        # section headers list to retranslate later
        self._sections: list[tuple[CollapsibleSection, dict]] = []

        # ----- build sections -----
        self.sections_container = QVBoxLayout()
        self.sections_container.setSpacing(6)

        catalog = complaints_catalog()
        for section in catalog.get("sections", []):
            body = self._build_section_body(section)
            title = self._section_title(section)
            group = CollapsibleSection(title, body, expanded=False)
            self.sections_container.addWidget(group)
            self._sections.append((group, section))

        # ----- footer -----
        self.count_label = QLabel()
        self.clear_btn = QPushButton()
        self.clear_btn.clicked.connect(self._on_clear)
        footer = QHBoxLayout()
        footer.addWidget(self.count_label)
        footer.addStretch(1)
        footer.addWidget(self.clear_btn)

        # ----- note -----
        self.note_label = QLabel()
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("")
        self.note_edit.setFixedHeight(72)
        self.note_edit.textChanged.connect(self._on_changed)

        # ----- error label -----
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #c62828;")
        self.error_label.hide()

        # ----- assemble -----
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(self.sections_container)
        outer.addLayout(footer)
        outer.addWidget(self.note_label)
        outer.addWidget(self.note_edit)
        outer.addWidget(self.error_label)

        self._retranslate()
        translator.language_changed.connect(self._retranslate)
        self._update_count()

    # ============================================================
    # Public API
    # ============================================================

    def get_values(self) -> tuple[list[str], dict[str, str], str]:
        """Return ``(codes, discharge_map, note)`` in stable insertion order."""
        codes: list[str] = []
        details: dict[str, str] = {}
        for code, box in self._boxes.items():
            if box.isChecked():
                codes.append(code)
                combo = self._discharge_boxes.get(code)
                if combo is not None:
                    value = combo.currentData()
                    if value:
                        details[code] = str(value)
        note = self.note_edit.toPlainText().strip()
        return codes, details, note

    def clear(self) -> None:
        for box in self._boxes.values():
            box.setChecked(False)
        for combo in self._discharge_boxes.values():
            combo.setCurrentIndex(0)
        self.note_edit.clear()
        self.error_label.hide()
        self._update_count()

    def set_error(self, has_error: bool) -> None:
        if has_error:
            self.error_label.setText(t("validation.complaints_required"))
            self.error_label.show()
        else:
            self.error_label.hide()

    # ============================================================
    # Building the section body
    # ============================================================

    def _section_title(self, section: dict) -> str:
        name = section.get("name", {})
        lang = translator.language
        label = name.get(lang) or name.get("uz") or section.get("code", "")
        return f"{section.get('icon', '')} {label}".strip()

    def _build_section_body(self, section: dict) -> QWidget:
        body = QWidget()
        grid = QGridLayout(body)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(4)

        discharge_labels = self._discharge_options()

        for row, item in enumerate(section.get("items", [])):
            code = item["code"]
            self._items[code] = item

            box = QCheckBox()
            box.setText(self._item_label(item))
            box.stateChanged.connect(lambda _s, c=code: self._on_toggle(c))
            self._boxes[code] = box
            box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            grid.addWidget(box, row, 0)

            if item.get("has_discharge_type"):
                combo = QComboBox()
                combo.addItem(t("reception.complaints.discharge_placeholder"), None)
                for code_, label in discharge_labels:
                    combo.addItem(label, code_)
                combo.setEnabled(False)
                combo.currentIndexChanged.connect(self._on_changed)
                self._discharge_boxes[code] = combo
                grid.addWidget(combo, row, 1)

        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 1)
        return body

    def _item_label(self, item: dict) -> str:
        lang = translator.language
        return item.get(lang) or item.get("uz") or item["code"]

    def _discharge_options(self) -> list[tuple[str, str]]:
        lang = translator.language
        catalog = discharge_types_catalog()
        return [
            (item["code"], item.get(lang) or item.get("uz") or item["code"])
            for item in catalog.get("types", [])
        ]

    # ============================================================
    # Change handlers
    # ============================================================

    def _on_toggle(self, code: str) -> None:
        box = self._boxes.get(code)
        combo = self._discharge_boxes.get(code)
        if combo is not None and box is not None:
            combo.setEnabled(box.isChecked())
            if not box.isChecked():
                combo.setCurrentIndex(0)
        self._update_count()
        self._on_changed()

    def _on_changed(self) -> None:
        self.error_label.hide()
        self.changed.emit()

    def _on_clear(self) -> None:
        self.clear()
        self.changed.emit()

    def _update_count(self) -> None:
        count = sum(1 for b in self._boxes.values() if b.isChecked())
        self.count_label.setText(t("reception.complaints.selected", count=count))

    # ============================================================
    # Retranslation
    # ============================================================

    def _retranslate(self, *_args: object) -> None:
        for group, section in self._sections:
            group.set_title(self._section_title(section))
        for code, box in self._boxes.items():
            box.setText(self._item_label(self._items[code]))
        # Rebuild each discharge combo item labels while keeping selection
        for _, combo in self._discharge_boxes.items():
            current = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(t("reception.complaints.discharge_placeholder"), None)
            for c, label in self._discharge_options():
                combo.addItem(label, c)
            if current:
                idx = combo.findData(current)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.blockSignals(False)
        self.clear_btn.setText(t("reception.complaints.clear"))
        self.note_label.setText(t("reception.complaints.additional"))
        self.note_edit.setPlaceholderText(t("reception.anamnesis.placeholder"))
        self._update_count()
