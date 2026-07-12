"""Patient statistics dialog — KPIs, TOP diagnoses, day-by-day chart."""

from __future__ import annotations

from PySide6.QtCore import Qt
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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinic.domain import stats_service
from clinic.domain.dto import PatientStats
from clinic.domain.stats_service import Period, PeriodPreset
from clinic.i18n.translator import t, translator
from clinic.ui.widgets.chart_canvas import ChartCanvas
from clinic.ui.widgets.date_range import DateRangeWidget


class PatientStatsDialog(QDialog):
    """Read-only dashboard for patient / reception activity in a chosen window."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("patients.stats.title"))
        self.setMinimumSize(760, 620)

        self._build_ui()
        translator.language_changed.connect(self._refresh)
        self.date_range.period_changed.connect(self._on_period_changed)
        self._refresh()

    # ============================================================
    # UI
    # ============================================================

    def _build_ui(self) -> None:
        self.title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        # Period picker
        self.date_range = DateRangeWidget(default=PeriodPreset.MONTH)

        # KPI cards
        self.kpi_total = _KpiCard()
        self.kpi_new = _KpiCard()
        self.kpi_repeat = _KpiCard()
        kpi_row = QHBoxLayout()
        for card in (self.kpi_total, self.kpi_new, self.kpi_repeat):
            kpi_row.addWidget(card)

        # TOP diagnoses table
        self.top_group = QGroupBox()
        tg_layout = QVBoxLayout(self.top_group)
        self.top_table = QTableWidget(0, 2)
        self.top_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.top_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.top_table.verticalHeader().setVisible(False)
        header = self.top_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tg_layout.addWidget(self.top_table)

        # Chart
        self.chart_group = QGroupBox()
        chart_layout = QVBoxLayout(self.chart_group)
        self.chart = ChartCanvas()
        chart_layout.addWidget(self.chart)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        self._close_btn = button_box.button(QDialogButtonBox.StandardButton.Close)

        # Assemble
        outer = QVBoxLayout(self)
        outer.addWidget(self.title_label)
        outer.addWidget(self.date_range)
        outer.addLayout(kpi_row)
        outer.addWidget(self.top_group, 1)
        outer.addWidget(self.chart_group, 1)
        outer.addWidget(button_box)

    # ============================================================
    # Data
    # ============================================================

    def _on_period_changed(self, _period: Period) -> None:
        self._refresh()

    def _refresh(self, *_args: object) -> None:
        self._retranslate_static()
        period = self.date_range.current_period()
        try:
            stats = stats_service.patient_stats(period)
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        self._render_kpis(stats)
        self._render_top(stats)
        self._render_chart(stats)

    def _render_kpis(self, stats: PatientStats) -> None:
        self.kpi_total.set(t("patients.stats.total_patients"), str(stats.total_patients))
        self.kpi_new.set(t("patients.stats.new_patients"), str(stats.new_patients))
        self.kpi_repeat.set(
            t("patients.stats.repeat_receptions"), str(stats.repeat_receptions)
        )

    def _render_top(self, stats: PatientStats) -> None:
        self.top_group.setTitle(t("patients.stats.top_diagnoses"))
        self.top_table.setHorizontalHeaderLabels(
            [t("reception.diagnosis"), t("cashier.stats.column.units")]
        )
        self.top_table.setRowCount(len(stats.top_diagnoses))
        for row, entry in enumerate(stats.top_diagnoses):
            diag_item = QTableWidgetItem(entry.diagnosis)
            cnt_item = QTableWidgetItem(str(entry.count))
            cnt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.top_table.setItem(row, 0, diag_item)
            self.top_table.setItem(row, 1, cnt_item)

    def _render_chart(self, stats: PatientStats) -> None:
        self.chart_group.setTitle(t("patients.stats.by_day"))
        if not stats.by_day:
            self.chart.show_empty_message(t("patients.stats.no_data"))
            return
        dates = [pt.date for pt in stats.by_day]
        values = [pt.value for pt in stats.by_day]
        self.chart.plot_time_series(
            dates,
            values,
            title=t("patients.stats.chart.receptions"),
        )

    # ============================================================
    # i18n
    # ============================================================

    def _retranslate_static(self) -> None:
        self.setWindowTitle(t("patients.stats.title"))
        self.title_label.setText(t("patients.stats.title"))
        self._close_btn.setText(t("common.close"))


class _KpiCard(QGroupBox):
    """Simple single-value KPI card."""

    def __init__(self) -> None:
        super().__init__()
        self._title_label = QLabel()
        self._value_label = QLabel()
        value_font = QFont()
        value_font.setPointSize(20)
        value_font.setBold(True)
        self._value_label.setFont(value_font)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet("color: #616161;")
        layout = QVBoxLayout(self)
        layout.addWidget(self._value_label)
        layout.addWidget(self._title_label)

    def set(self, title: str, value: str) -> None:
        self._title_label.setText(title)
        self._value_label.setText(value)


__all__ = ["PatientStatsDialog"]
