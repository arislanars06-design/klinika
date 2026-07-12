"""Reception → LOR STATUS block.

Renders four otolaryngology examination methods as tabs. Each tab is a
dynamic form generated from :mod:`clinic.catalogs.lor_status`. Supported field
types: ``radio`` (as combo), ``checkbox`` (single), ``checkbox_multi``,
``side``, ``degree``, ``text``.

Otoscopy is rendered per-ear (AD/AS) with two columns of controls sharing the
same section definitions. Fields with ``visible_when`` are dynamically shown or
hidden based on their gating field's current value.

A "Norma" button per tab (and a global one for all tabs) resets every radio,
checkbox-multi and degree control to the option marked ``is_norm: true``. A
live text preview at the bottom uses ``compose_lor_status`` — the same
composer that drives Word export later.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clinic.domain.catalog_loader import lor_status_catalog
from clinic.i18n.translator import t, translator
from clinic.printing.text_composer import compose_lor_status

# ============================================================================
# Field controller — encapsulates one input widget in one section
# ============================================================================


class _FieldController:
    """Runtime handle for a single field within a section."""

    def __init__(
        self,
        code: str,
        widget_row: list[QWidget],  # [label, input] usually
        field: dict,
        get: Callable[[], object],
        set_: Callable[[object], None],
        clear: Callable[[], None],
        norm: Callable[[], None] | None,
        on_change: Callable[[Callable], None],
    ) -> None:
        self.code = code
        self.widget_row = widget_row
        self.field = field
        self.get = get
        self.set_ = set_
        self.clear = clear
        self.norm = norm
        self._register_change = on_change

    def set_visible(self, visible: bool) -> None:
        for w in self.widget_row:
            w.setVisible(visible)


# ============================================================================
# Section — collection of fields inside a scroll area
# ============================================================================


class _SectionForm(QGroupBox):
    """One examination area (e.g. 'Tashqi burun') rendered as a QFormLayout."""

    changed = Signal()

    def __init__(
        self,
        section: dict,
        *,
        catalog: dict,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._section = section
        self._catalog = catalog
        self._fields: dict[str, _FieldController] = {}

        self.setTitle(self._localized(section.get("name", {})))

        form = QFormLayout(self)
        form.setContentsMargins(8, 8, 8, 8)
        form.setSpacing(4)

        for field in section.get("fields", []):
            row = self._build_field(field)
            if row is not None:
                label_widget = row[0]
                input_widget = row[1] if len(row) > 1 else None
                if input_widget is not None:
                    form.addRow(label_widget, input_widget)
                else:
                    form.addRow(label_widget)

        # After all fields are constructed we can wire up visible_when so it
        # references controllers that already exist.
        self._apply_visibility()

    # ---------- helpers ----------

    def _localized(self, entry: dict) -> str:
        if not isinstance(entry, dict):
            return str(entry)
        return entry.get(translator.language) or entry.get("uz") or ""

    def _label_for_field(self, field: dict) -> str:
        # Some fields have a label under either "label" or "name"; if not,
        # fall back to the field's own code (only used for "state"-like codes).
        if "label" in field:
            return self._localized(field["label"])
        # We render "state"/"color"/... as an empty label so the input widget
        # tells the story on its own.
        return ""

    # ---------- field builders ----------

    def _build_field(self, field: dict) -> list[QWidget] | None:
        ftype = field.get("type")
        code = field.get("code")
        if not code:
            return None

        if ftype == "radio":
            return self._build_radio(code, field)
        if ftype == "checkbox_multi":
            return self._build_multi(code, field)
        if ftype == "checkbox":
            return self._build_checkbox(code, field)
        if ftype == "side":
            return self._build_choice_from_catalog(code, field, "sides")
        if ftype == "degree":
            return self._build_choice_from_catalog(code, field, "degrees")
        if ftype == "text":
            return self._build_text(code, field)
        return None

    def _build_radio(self, code: str, field: dict) -> list[QWidget]:
        label_text = self._label_for_field(field) or code.replace("_", " ").capitalize()
        label = QLabel(label_text)
        combo = QComboBox()
        combo.addItem("—", None)
        for option in field.get("options", []):
            combo.addItem(self._localized(option), option["code"])
        combo.currentIndexChanged.connect(self._on_field_changed)

        def _get() -> object:
            return combo.currentData()

        def _set(value: object) -> None:
            idx = combo.findData(value)
            combo.setCurrentIndex(idx if idx >= 0 else 0)

        def _clear() -> None:
            combo.setCurrentIndex(0)

        def _norm() -> None:
            for i in range(combo.count()):
                data = combo.itemData(i)
                if not data:
                    continue
                for opt in field.get("options", []):
                    if opt["code"] == data and opt.get("is_norm"):
                        combo.setCurrentIndex(i)
                        return

        self._register(code, [label, combo], field, _get, _set, _clear, _norm)
        return [label, combo]

    def _build_multi(self, code: str, field: dict) -> list[QWidget]:
        label = QLabel(self._label_for_field(field) or code.replace("_", " ").capitalize())
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(2)

        boxes: list[tuple[str, QCheckBox]] = []
        for i, opt in enumerate(field.get("options", []) or []):
            box = QCheckBox(self._localized(opt))
            box.setProperty("codeData", opt["code"])
            box.stateChanged.connect(self._on_field_changed)
            grid.addWidget(box, i // 2, i % 2)
            boxes.append((opt["code"], box))

        def _get() -> object:
            return [c for c, b in boxes if b.isChecked()]

        def _set(value: object) -> None:
            values = set(value or [])
            for c, b in boxes:
                b.setChecked(c in values)

        def _clear() -> None:
            for _, b in boxes:
                b.setChecked(False)

        def _norm() -> None:
            norm_codes = {opt["code"] for opt in field.get("options", []) if opt.get("is_norm")}
            if not norm_codes:
                _clear()
                return
            for c, b in boxes:
                b.setChecked(c in norm_codes)

        self._register(code, [label, container], field, _get, _set, _clear, _norm)
        return [label, container]

    def _build_checkbox(self, code: str, field: dict) -> list[QWidget]:
        box = QCheckBox(self._localized(field.get("label", {})) or code)
        box.stateChanged.connect(self._on_field_changed)

        def _get() -> object:
            return box.isChecked()

        def _set(value: object) -> None:
            box.setChecked(bool(value))

        def _clear() -> None:
            box.setChecked(False)

        # No is_norm on single checkboxes → norm = unchecked.
        self._register(code, [box], field, _get, _set, _clear, _clear)
        return [box]

    def _build_choice_from_catalog(
        self, code: str, field: dict, key: str
    ) -> list[QWidget]:
        # Determines label from a well-known catalog key ("sides" / "degrees").
        entries = self._catalog.get(key, [])
        default_label = {
            "sides": {"uz": "Tomon", "ru": "Сторона"},
            "degrees": {"uz": "Daraja", "ru": "Степень"},
        }[key]
        label = QLabel(self._localized(default_label))
        combo = QComboBox()
        combo.addItem("—", None)
        for entry in entries:
            combo.addItem(self._localized(entry), entry["code"])
        combo.currentIndexChanged.connect(self._on_field_changed)

        def _get() -> object:
            return combo.currentData()

        def _set(value: object) -> None:
            idx = combo.findData(value)
            combo.setCurrentIndex(idx if idx >= 0 else 0)

        def _clear() -> None:
            combo.setCurrentIndex(0)

        def _norm() -> None:
            for entry in entries:
                if entry.get("is_norm"):
                    idx = combo.findData(entry["code"])
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
                        return

        self._register(code, [label, combo], field, _get, _set, _clear, _norm)
        return [label, combo]

    def _build_text(self, code: str, field: dict) -> list[QWidget]:
        label = QLabel(self._label_for_field(field) or code)
        edit = QLineEdit()
        edit.textEdited.connect(self._on_field_changed)

        def _get() -> object:
            return edit.text().strip() or None

        def _set(value: object) -> None:
            edit.setText(str(value or ""))

        def _clear() -> None:
            edit.clear()

        self._register(code, [label, edit], field, _get, _set, _clear, _clear)
        return [label, edit]

    # ---------- controller registration ----------

    def _register(
        self,
        code: str,
        widget_row: list[QWidget],
        field: dict,
        get,  # type: ignore[no-untyped-def]
        set_,  # type: ignore[no-untyped-def]
        clear,  # type: ignore[no-untyped-def]
        norm,  # type: ignore[no-untyped-def]
    ) -> None:
        controller = _FieldController(
            code=code,
            widget_row=widget_row,
            field=field,
            get=get,
            set_=set_,
            clear=clear,
            norm=norm,
            on_change=lambda cb: None,
        )
        self._fields[code] = controller

    # ---------- visibility ----------

    def _apply_visibility(self) -> None:
        current = {code: ctrl.get() for code, ctrl in self._fields.items()}
        for ctrl in self._fields.values():
            rule = ctrl.field.get("visible_when")
            if not rule:
                continue
            ctrl.set_visible(self._rule_matches(rule, current))

    def _rule_matches(self, rule: dict, current: dict) -> bool:
        for key, expected in rule.items():
            actual = current.get(key)
            if isinstance(expected, list):
                if isinstance(actual, list):
                    if not any(a in expected for a in actual):
                        return False
                elif actual not in expected:
                    return False
            else:
                if isinstance(actual, list):
                    if expected not in actual:
                        return False
                elif actual != expected:
                    return False
        return True

    # ---------- change flow ----------

    def _on_field_changed(self, *_args: object) -> None:
        self._apply_visibility()
        self.changed.emit()

    # ---------- API ----------

    def get_values(self) -> dict:
        result: dict = {}
        current = {code: ctrl.get() for code, ctrl in self._fields.items()}
        for code, ctrl in self._fields.items():
            rule = ctrl.field.get("visible_when")
            if rule and not self._rule_matches(rule, current):
                continue  # Hidden fields are not part of the payload.
            value = ctrl.get()
            if value in (None, "", [], False):
                continue
            result[code] = value
        return result

    def set_values(self, data: dict | None) -> None:
        for code, ctrl in self._fields.items():
            if data and code in data:
                ctrl.set_(data[code])
            else:
                ctrl.clear()
        self._apply_visibility()

    def apply_norm(self) -> None:
        for ctrl in self._fields.values():
            if ctrl.norm is not None:
                ctrl.norm()
        self._apply_visibility()
        self.changed.emit()

    def clear_all(self) -> None:
        for ctrl in self._fields.values():
            ctrl.clear()
        self._apply_visibility()
        self.changed.emit()


# ============================================================================
# Method tab — one otolaryngology exam (rhinoscopy / pharyngoscopy / …)
# ============================================================================


class _MethodTab(QWidget):
    """One method rendered as a scrollable stack of section forms."""

    changed = Signal()

    def __init__(self, method: dict, catalog: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._method = method
        self._catalog = catalog
        self._per_ear = bool(method.get("per_ear"))
        # Section forms — either a flat list or {ear_code: [SectionForm, ...]}.
        self._sections_flat: list[_SectionForm] = []
        self._sections_per_ear: dict[str, list[_SectionForm]] = {}
        # Track which sections are gated on tympanic-membrane perforation.
        self._perf_sections: dict[str, list[_SectionForm]] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # "Norma" button for this method
        norm_row = QHBoxLayout()
        self.norm_btn = QPushButton(t("reception.lor_status.norm"))
        self.norm_btn.clicked.connect(self._apply_norm)
        self.reset_btn = QPushButton(t("reception.lor_status.reset"))
        self.reset_btn.clicked.connect(self._clear_all)
        norm_row.addStretch(1)
        norm_row.addWidget(self.reset_btn)
        norm_row.addWidget(self.norm_btn)
        outer.addLayout(norm_row)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(10)

        if self._per_ear:
            self._build_per_ear(content_layout)
        else:
            self._build_flat(content_layout)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    # ---------- construction ----------

    def _build_flat(self, layout: QVBoxLayout) -> None:
        for section in self._method.get("sections", []):
            form = _SectionForm(section, catalog=self._catalog)
            form.changed.connect(self.changed.emit)
            layout.addWidget(form)
            self._sections_flat.append(form)

    def _build_per_ear(self, layout: QVBoxLayout) -> None:
        ears = self._method.get("ears", [])
        # For each section, build a two-column row: AD | AS
        for section in self._method.get("sections", []):
            row_wrapper = QWidget()
            hbox = QHBoxLayout(row_wrapper)
            hbox.setContentsMargins(0, 0, 0, 0)
            hbox.setSpacing(8)

            for ear in ears:
                form = _SectionForm(
                    self._section_with_ear_title(section, ear),
                    catalog=self._catalog,
                )
                form.changed.connect(self._on_per_ear_changed)
                hbox.addWidget(form, 1)
                self._sections_per_ear.setdefault(ear["code"], []).append(form)
                if section.get("visible_when_perforation"):
                    self._perf_sections.setdefault(ear["code"], []).append(form)

            layout.addWidget(row_wrapper)

        # Initial perforation gating
        self._update_perforation_visibility()

    def _section_with_ear_title(self, section: dict, ear: dict) -> dict:
        # Prepend the ear label to the section name so both columns are clearly
        # attributed. We copy so we don't mutate the shared catalog dict.
        name = dict(section.get("name", {}))
        for lang in ("uz", "ru"):
            label = ear.get(lang) or ear.get("uz") or ear["code"]
            base = name.get(lang, "")
            name[lang] = f"{label}: {base}" if base else label
        return {**section, "name": name}

    # ---------- change flow ----------

    def _apply_norm(self) -> None:
        forms: list[_SectionForm] = list(self._sections_flat)
        for lst in self._sections_per_ear.values():
            forms.extend(lst)
        for form in forms:
            form.apply_norm()
        self._update_perforation_visibility()
        self.changed.emit()

    def _clear_all(self) -> None:
        forms: list[_SectionForm] = list(self._sections_flat)
        for lst in self._sections_per_ear.values():
            forms.extend(lst)
        for form in forms:
            form.clear_all()
        self._update_perforation_visibility()
        self.changed.emit()

    def _on_per_ear_changed(self) -> None:
        self._update_perforation_visibility()
        self.changed.emit()

    def _update_perforation_visibility(self) -> None:
        for ear_code, sections in self._perf_sections.items():
            # Perforation lives in the "tympanic_membrane" section for this ear.
            tm_forms = [
                f for f in self._sections_per_ear.get(ear_code, [])
                if f._section.get("code") == "tympanic_membrane"
            ]
            perforation = None
            if tm_forms:
                perforation = tm_forms[0].get_values().get("perforation")
            visible = perforation not in (None, "none")
            for form in sections:
                form.setVisible(visible)

    # ---------- values ----------

    def get_values(self) -> dict:
        if not self._per_ear:
            result: dict = {}
            for form in self._sections_flat:
                v = form.get_values()
                if v:
                    result[form._section["code"]] = v
            return result

        result_per_ear: dict[str, dict] = {}
        for ear_code, forms in self._sections_per_ear.items():
            ear_data: dict = {}
            for form in forms:
                v = form.get_values()
                if v:
                    ear_data[form._section["code"]] = v
            if ear_data:
                result_per_ear[ear_code] = ear_data
        return result_per_ear

    def set_values(self, data: dict | None) -> None:
        data = data or {}
        if not self._per_ear:
            for form in self._sections_flat:
                form.set_values(data.get(form._section["code"]))
            return
        for ear_code, forms in self._sections_per_ear.items():
            ear_data = data.get(ear_code, {}) or {}
            for form in forms:
                form.set_values(ear_data.get(form._section["code"]))
        self._update_perforation_visibility()


# ============================================================================
# Top-level LOR STATUS block with all four methods
# ============================================================================


class LorStatusBlock(QWidget):
    """Container tab widget with a live preview."""

    changed = Signal()
    PREVIEW_DEBOUNCE_MS = 200

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._catalog = lor_status_catalog()
        self._tabs: dict[str, _MethodTab] = {}

        # ----- top action row -----
        self.norm_all_btn = QPushButton()
        self.norm_all_btn.clicked.connect(self._apply_norm_all)
        top_row = QHBoxLayout()
        top_row.addStretch(1)
        top_row.addWidget(self.norm_all_btn)

        # ----- tabs -----
        self.tab_widget = QTabWidget()
        for method in self._catalog.get("methods", []):
            tab = _MethodTab(method, self._catalog)
            tab.changed.connect(self._on_changed)
            key = f"reception.lor_status.tab.{method['code']}"
            self.tab_widget.addTab(tab, t(key))
            self._tabs[method["code"]] = tab

        # ----- preview -----
        self.preview_label = QLabel()
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setFixedHeight(140)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(top_row)
        outer.addWidget(self.tab_widget, 1)
        outer.addWidget(self.preview_label)
        outer.addWidget(self.preview_edit)

        # Debounced preview update
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(self.PREVIEW_DEBOUNCE_MS)
        self._preview_timer.timeout.connect(self._refresh_preview)

        translator.language_changed.connect(self._retranslate)
        self._retranslate()
        self._refresh_preview()

    # ---------- API ----------

    def get_values(self) -> dict:
        result: dict = {}
        for code, tab in self._tabs.items():
            v = tab.get_values()
            if v:
                result[code] = v
        return result

    def set_values(self, data: dict | None) -> None:
        data = data or {}
        for code, tab in self._tabs.items():
            tab.set_values(data.get(code))
        self._refresh_preview()

    # ---------- actions ----------

    def _apply_norm_all(self) -> None:
        for tab in self._tabs.values():
            tab._apply_norm()

    def _on_changed(self) -> None:
        self._preview_timer.start()
        self.changed.emit()

    def _refresh_preview(self) -> None:
        text = compose_lor_status(self.get_values(), lang=translator.language)
        self.preview_edit.setPlainText(text)

    # ---------- retranslation ----------

    def _retranslate(self, *_args: object) -> None:
        self.norm_all_btn.setText(t("reception.lor_status.norm_all"))
        self.preview_label.setText(t("reception.lor_status.preview"))
        for i, code in enumerate(self._tabs):
            self.tab_widget.setTabText(i, t(f"reception.lor_status.tab.{code}"))
        for tab in self._tabs.values():
            tab.norm_btn.setText(t("reception.lor_status.norm"))
            tab.reset_btn.setText(t("reception.lor_status.reset"))
        self._refresh_preview()
