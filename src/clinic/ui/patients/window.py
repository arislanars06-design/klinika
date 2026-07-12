"""Patient history window: paginated table with search + date filter + actions."""

from __future__ import annotations

from datetime import datetime

from loguru import logger
from PySide6.QtCore import QDate, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinic.db.repository import ANY_FIELD_SEARCH, PatientSearchField
from clinic.domain import patient_service, reception_service
from clinic.domain.dto import PatientHistoryPage, PatientSummaryDTO
from clinic.i18n.translator import t, translator

SEARCH_FIELDS: list[tuple[str, PatientSearchField]] = [
    ("patients.search.field.any", ANY_FIELD_SEARCH),
    ("patients.search.field.name", PatientSearchField(full_name=True)),
    ("patients.search.field.phone", PatientSearchField(phone=True)),
    (
        "patients.search.field.diagnosis",
        PatientSearchField(full_name=False, phone=False, diagnosis=True),
    ),
    (
        "patients.search.field.year",
        PatientSearchField(full_name=False, phone=False, birth_year=True),
    ),
]


class PatientsWindow(QDialog):
    """Top-level patients history window (modal for now)."""

    #: Emitted after an action changed data (reception saved/deleted, patient
    #: removed) so callers can refresh their own state if needed.
    data_changed = Signal()

    PAGE_SIZE = 20
    SEARCH_DEBOUNCE_MS = 300

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("patients.title"))
        self.setMinimumSize(960, 640)

        self._page: PatientHistoryPage | None = None
        self._current_page = 1

        # Timer must exist before _build_ui because early callbacks poke it.
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(self.SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._reload)

        self._build_ui()
        translator.language_changed.connect(self._retranslate)
        self._retranslate()

        # Load initial page
        self._reload()

    # ============================================================
    # UI construction
    # ============================================================

    def _build_ui(self) -> None:
        # ----- top bar -----
        self.back_btn = QPushButton()
        self.back_btn.clicked.connect(self.reject)
        self.title_label = QLabel()
        title_font = self.title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.stats_btn = QPushButton()
        self.stats_btn.clicked.connect(self._on_stats)

        top_row = QHBoxLayout()
        top_row.addWidget(self.back_btn)
        top_row.addSpacing(12)
        top_row.addWidget(self.title_label)
        top_row.addStretch(1)
        top_row.addWidget(self.stats_btn)

        # ----- filters row -----
        self.search_edit = QLineEdit()
        self.search_edit.textEdited.connect(lambda _: self._search_timer.start())
        self.search_edit.setMinimumWidth(240)

        self.field_combo = QComboBox()
        for key, _ in SEARCH_FIELDS:
            self.field_combo.addItem(t(key), key)
        self.field_combo.currentIndexChanged.connect(lambda _: self._reload())

        self.date_from = QDateEdit(calendarPopup=True)
        self.date_to = QDateEdit(calendarPopup=True)
        for de in (self.date_from, self.date_to):
            de.setDisplayFormat("yyyy-MM-dd")
            de.setSpecialValueText(" ")
            de.setDate(de.minimumDate())
        self.date_from.dateChanged.connect(lambda _: self._search_timer.start())
        self.date_to.dateChanged.connect(lambda _: self._search_timer.start())

        self.date_from_label = QLabel()
        self.date_to_label = QLabel()
        self.date_enabled = QCheckBox()
        self.date_enabled.stateChanged.connect(self._on_date_toggle)
        self._on_date_toggle()  # sets initial disabled state

        self.filter_btn = QPushButton()
        self.filter_btn.clicked.connect(self._reload)
        self.clear_btn = QPushButton()
        self.clear_btn.clicked.connect(self._on_clear_filters)

        filter_row = QHBoxLayout()
        filter_row.addWidget(self.search_edit, 2)
        filter_row.addWidget(self.field_combo)
        filter_row.addSpacing(12)
        filter_row.addWidget(self.date_enabled)
        filter_row.addWidget(self.date_from_label)
        filter_row.addWidget(self.date_from)
        filter_row.addWidget(self.date_to_label)
        filter_row.addWidget(self.date_to)
        filter_row.addStretch(1)
        filter_row.addWidget(self.filter_btn)
        filter_row.addWidget(self.clear_btn)

        # ----- table -----
        self.table = QTableWidget(0, 6)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.itemDoubleClicked.connect(self._on_row_double_clicked)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # num
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # age
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # phone
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # last
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # actions

        # ----- pagination -----
        self.total_label = QLabel()
        self.prev_btn = QPushButton()
        self.next_btn = QPushButton()
        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prev_btn.clicked.connect(lambda: self._go_page(self._current_page - 1))
        self.next_btn.clicked.connect(lambda: self._go_page(self._current_page + 1))

        pagination = QHBoxLayout()
        pagination.addWidget(self.total_label)
        pagination.addStretch(1)
        pagination.addWidget(self.prev_btn)
        pagination.addWidget(self.page_label)
        pagination.addWidget(self.next_btn)

        # ----- assemble -----
        outer = QVBoxLayout(self)
        outer.addLayout(top_row)
        outer.addLayout(filter_row)
        outer.addWidget(self.table, 1)
        outer.addLayout(pagination)

    def _on_date_toggle(self) -> None:
        enabled = self.date_enabled.isChecked()
        self.date_from.setEnabled(enabled)
        self.date_to.setEnabled(enabled)
        if enabled and self.date_from.date() == self.date_from.minimumDate():
            today = QDate.currentDate()
            self.date_from.setDate(today.addMonths(-1))
            self.date_to.setDate(today)
        self._search_timer.start()

    def _on_clear_filters(self) -> None:
        self.search_edit.clear()
        self.field_combo.setCurrentIndex(0)
        self.date_enabled.setChecked(False)
        self._reload()

    # ============================================================
    # Data loading
    # ============================================================

    def _current_search_field(self) -> PatientSearchField:
        key = self.field_combo.currentData()
        for k, spec in SEARCH_FIELDS:
            if k == key:
                return spec
        return ANY_FIELD_SEARCH

    def _current_date_bounds(self) -> tuple[datetime | None, datetime | None]:
        if not self.date_enabled.isChecked():
            return None, None
        start_date: QDate = self.date_from.date()
        end_date: QDate = self.date_to.date()
        start_dt = datetime(start_date.year(), start_date.month(), start_date.day(), 0, 0, 0)
        end_dt = datetime(end_date.year(), end_date.month(), end_date.day(), 23, 59, 59)
        if end_dt < start_dt:
            start_dt, end_dt = end_dt, start_dt
        return start_dt, end_dt

    def _reload(self) -> None:
        text = self.search_edit.text().strip() or None
        search_in = self._current_search_field()
        date_from, date_to = self._current_date_bounds()

        try:
            self._page = patient_service.paginated_search(
                text=text,
                search_in=search_in,
                date_from=date_from,
                date_to=date_to,
                page=self._current_page,
                page_size=self.PAGE_SIZE,
            )
        except Exception as exc:
            logger.exception("Patient search failed")
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        # If we requested a page past the end (e.g. after deletion), snap back.
        if self._page.total > 0 and self._current_page > self._page.page_count:
            self._current_page = self._page.page_count
            self._reload()
            return
        self._render_table()

    def _render_table(self) -> None:
        page = self._page
        if page is None:
            return
        self.table.setRowCount(len(page.items))
        base = (page.page - 1) * page.page_size
        for row_index, item in enumerate(page.items):
            self._render_row(row_index, base + row_index + 1, item)

        self.total_label.setText(t("patients.total", count=page.total))
        self.page_label.setText(
            t("patients.page_info", page=page.page, total=page.page_count)
        )
        self.prev_btn.setEnabled(page.page > 1)
        self.next_btn.setEnabled(page.page < page.page_count)

    def _render_row(self, row: int, number: int, item: PatientSummaryDTO) -> None:
        num_item = QTableWidgetItem(str(number))
        num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        name_item = QTableWidgetItem(item.patient.full_name)
        name_item.setData(Qt.ItemDataRole.UserRole, item.patient.id)
        age_item = QTableWidgetItem(str(item.age))
        age_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        phone_item = QTableWidgetItem(item.patient.phone or "—")

        last_text = t("patients.no_visits")
        if item.last_reception_date is not None:
            last_text = item.last_reception_date.strftime("%Y-%m-%d")
        last_item = QTableWidgetItem(last_text)

        for c, cell in enumerate((num_item, name_item, age_item, phone_item, last_item)):
            self.table.setItem(row, c, cell)

        # Action buttons — small inline widget
        self.table.setCellWidget(row, 5, self._build_actions_widget(item.patient.id))

    def _build_actions_widget(self, patient_id: int) -> QWidget:
        wrapper = QWidget()
        h = QHBoxLayout(wrapper)
        h.setContentsMargins(2, 0, 2, 0)
        h.setSpacing(2)
        view_btn = QPushButton("\U0001F441")
        view_btn.setToolTip(t("patients.action.view"))
        view_btn.setFixedWidth(32)
        view_btn.clicked.connect(lambda: self._on_view(patient_id))

        edit_btn = QPushButton("\u270F")
        edit_btn.setToolTip(t("patients.action.edit"))
        edit_btn.setFixedWidth(32)
        edit_btn.clicked.connect(lambda: self._on_edit_last(patient_id))

        del_btn = QPushButton("\U0001F5D1")
        del_btn.setToolTip(t("patients.action.delete"))
        del_btn.setFixedWidth(32)
        del_btn.clicked.connect(lambda: self._on_delete(patient_id))

        h.addWidget(view_btn)
        h.addWidget(edit_btn)
        h.addWidget(del_btn)
        return wrapper

    # ============================================================
    # Actions
    # ============================================================

    def _on_view(self, patient_id: int) -> None:
        from clinic.ui.patients.patient_card import PatientCardDialog

        dialog = PatientCardDialog(patient_id, self)
        dialog.data_changed.connect(self._on_child_changed)
        dialog.exec()

    def _on_edit_last(self, patient_id: int) -> None:
        latest = reception_service.list_for_patient(patient_id)
        if not latest:
            QMessageBox.information(
                self,
                t("patients.title"),
                t("patients.no_visits"),
            )
            return
        self._open_reception_editor(latest[0].id)

    def _open_reception_editor(self, reception_id: int) -> None:
        from clinic.ui.reception import ReceptionWindow

        window = ReceptionWindow(self, edit_reception_id=reception_id)
        result = window.exec()
        if result == QDialog.DialogCode.Accepted:
            self._on_child_changed()

    def _on_delete(self, patient_id: int) -> None:
        reply = QMessageBox.question(
            self,
            t("common.confirm"),
            t("patients.confirm_delete"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            patient_service.delete(patient_id)
        except Exception as exc:
            logger.exception("Patient delete failed")
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        self._reload()
        self.data_changed.emit()

    def _on_row_double_clicked(self, item: QTableWidgetItem) -> None:
        # Column 5 hosts a widget so double-clicks arrive from cols 0..4.
        row = item.row()
        name_item = self.table.item(row, 1)
        if name_item is None:
            return
        patient_id = name_item.data(Qt.ItemDataRole.UserRole)
        if patient_id is not None:
            self._on_view(int(patient_id))

    def _on_child_changed(self) -> None:
        self._reload()
        self.data_changed.emit()

    def _on_stats(self) -> None:
        from clinic.ui.patients.stats_widget import PatientStatsDialog

        PatientStatsDialog(self).exec()

    # ============================================================
    # Pagination
    # ============================================================

    def _go_page(self, page: int) -> None:
        if self._page is None:
            return
        target = max(1, min(self._page.page_count, page))
        if target == self._current_page:
            return
        self._current_page = target
        self._reload()

    # ============================================================
    # i18n
    # ============================================================

    def _retranslate(self, *_args: object) -> None:
        self.setWindowTitle(t("patients.title"))
        self.title_label.setText(t("patients.title"))
        self.back_btn.setText(t("common.back"))
        self.stats_btn.setText(f"\U0001F4CA  {t('patients.statistics')}")
        self.search_edit.setPlaceholderText(t("patients.search.placeholder"))
        for i, (key, _) in enumerate(SEARCH_FIELDS):
            self.field_combo.setItemText(i, t(key))
        self.date_enabled.setText(t("patients.filter"))
        self.date_from_label.setText(t("patients.date_from") + ":")
        self.date_to_label.setText(t("patients.date_to") + ":")
        self.filter_btn.setText(t("patients.filter.apply"))
        self.clear_btn.setText(t("patients.filter.clear"))
        self.prev_btn.setText(t("patients.prev_page"))
        self.next_btn.setText(t("patients.next_page"))
        self.table.setHorizontalHeaderLabels(
            [
                t("patients.column.num"),
                t("patients.column.name"),
                t("patients.column.age"),
                t("patients.column.phone"),
                t("patients.column.last_visit"),
                t("patients.column.actions"),
            ]
        )
        # Re-render so column values pick up the new language too.
        if self._page is not None:
            self._render_table()


__all__ = ["PatientsWindow"]
