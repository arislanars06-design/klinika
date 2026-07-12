"""Cashier statistics dialog — revenue KPIs, per-service breakdown, chart."""

from __future__ import annotations

from decimal import Decimal

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
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinic.domain import stats_service
from clinic.domain.dto import CashierStats
from clinic.domain.stats_service import Period, PeriodPreset
from clinic.i18n.translator import t, translator
from clinic.ui.widgets.chart_canvas import ChartCanvas
from clinic.ui.widgets.date_range import DateRangeWidget


def _format_money(value: Decimal | float) -> str:
    v = float(value)
    if v == int(v):
        return f"{int(v):,}".replace(",", " ")
    return f"{v:,.2f}".replace(",", " ")


class CashierStatsDialog(QDialog):
    """Read-only cashier dashboard."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("cashier.stats.title"))
        self.setMinimumSize(820, 620)

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

        self.date_range = DateRangeWidget(default=PeriodPreset.MONTH)

        # KPI cards
        self.kpi_revenue = _KpiCard()
        self.kpi_receipts = _KpiCard()
        self.kpi_avg = _KpiCard()
        kpi_row = QHBoxLayout()
        for card in (self.kpi_revenue, self.kpi_receipts, self.kpi_avg):
            kpi_row.addWidget(card)

        # By-service breakdown
        self.service_group = QGroupBox()
        sg_layout = QVBoxLayout(self.service_group)
        self.service_table = QTableWidget(0, 3)
        self.service_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.service_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.service_table.verticalHeader().setVisible(False)
        header = self.service_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        sg_layout.addWidget(self.service_table)

        # Chart
        self.chart_group = QGroupBox()
        chart_layout = QVBoxLayout(self.chart_group)
        self.chart = ChartCanvas()
        chart_layout.addWidget(self.chart)

        # Buttons: Export + Close
        self.export_btn = QPushButton()
        self.export_btn.clicked.connect(self._on_export)
        button_box = QDialogButtonBox()
        button_box.addButton(self.export_btn, QDialogButtonBox.ButtonRole.ActionRole)
        close_btn = button_box.addButton(QDialogButtonBox.StandardButton.Close)
        close_btn.clicked.connect(self.reject)
        self._close_btn = close_btn

        # Assemble
        outer = QVBoxLayout(self)
        outer.addWidget(self.title_label)
        outer.addWidget(self.date_range)
        outer.addLayout(kpi_row)
        outer.addWidget(self.service_group, 1)
        outer.addWidget(self.chart_group, 1)
        outer.addWidget(button_box)

        self._stats: CashierStats | None = None
        self._period: Period | None = None

    # ============================================================
    # Data
    # ============================================================

    def _on_period_changed(self, _period: Period) -> None:
        self._refresh()

    def _refresh(self, *_args: object) -> None:
        self._retranslate_static()
        period = self.date_range.current_period()
        try:
            stats = stats_service.cashier_stats(period)
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        self._stats = stats
        self._period = period
        self._render_kpis(stats)
        self._render_services(stats)
        self._render_chart(stats)

    def _on_export(self) -> None:
        from clinic.domain import clinic_info_service
        from clinic.printing.stats_export import save_cashier_stats
        from clinic.ui.printing_helpers import cashier_stats_filename, prompt_and_save

        if self._stats is None or self._period is None:
            return
        info = clinic_info_service.load()
        clinic_dict = {
            "name_uz": info.name_uz,
            "name_ru": info.name_ru,
            "address_uz": info.address_uz,
            "address_ru": info.address_ru,
            "phone": info.phone,
            "logo_path": info.logo_path,
        }

        def _builder(dest):  # type: ignore[no-untyped-def]
            return save_cashier_stats(
                output_path=dest,
                stats=self._stats,
                period=self._period,
                clinic=clinic_dict,
                lang=translator.language,
            )

        prompt_and_save(
            self,
            title_key="print.cashier_stats.title",
            default_filename=cashier_stats_filename(
                self._period.start.date(), self._period.end.date()
            ),
            builder=_builder,
        )

    def _render_kpis(self, stats: CashierStats) -> None:
        currency = t("cashier.currency")
        self.kpi_revenue.set(
            t("cashier.stats.total_revenue"),
            f"{_format_money(stats.total_revenue)} {currency}",
        )
        self.kpi_receipts.set(
            t("cashier.stats.receipts_count"), str(stats.receipts_count)
        )
        self.kpi_avg.set(
            t("cashier.stats.average_receipt"),
            f"{_format_money(stats.average_receipt)} {currency}",
        )

    def _render_services(self, stats: CashierStats) -> None:
        self.service_group.setTitle(t("cashier.stats.by_service"))
        self.service_table.setHorizontalHeaderLabels(
            [
                t("cashier.stats.column.service"),
                t("cashier.stats.column.units"),
                t("cashier.stats.column.revenue"),
            ]
        )
        self.service_table.setRowCount(len(stats.by_service))
        currency = t("cashier.currency")
        for row, entry in enumerate(stats.by_service):
            name_item = QTableWidgetItem(entry.display_name(translator.language))
            units_item = QTableWidgetItem(str(entry.units_sold))
            units_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            revenue_item = QTableWidgetItem(f"{_format_money(entry.revenue)} {currency}")
            revenue_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.service_table.setItem(row, 0, name_item)
            self.service_table.setItem(row, 1, units_item)
            self.service_table.setItem(row, 2, revenue_item)

    def _render_chart(self, stats: CashierStats) -> None:
        self.chart_group.setTitle(t("cashier.stats.by_day"))
        if not stats.by_day:
            self.chart.show_empty_message(t("patients.stats.no_data"))
            return
        dates = [pt.date for pt in stats.by_day]
        values = [pt.value for pt in stats.by_day]
        self.chart.plot_time_series(
            dates,
            values,
            title=t("cashier.stats.chart.revenue"),
        )

    # ============================================================
    # i18n
    # ============================================================

    def _retranslate_static(self) -> None:
        self.setWindowTitle(t("cashier.stats.title"))
        self.title_label.setText(t("cashier.stats.title"))
        self._close_btn.setText(t("common.close"))
        self.export_btn.setText("\U0001F4C4  " + t("stats.export_word"))


class _KpiCard(QGroupBox):
    def __init__(self) -> None:
        super().__init__()
        self._title_label = QLabel()
        self._value_label = QLabel()
        value_font = QFont()
        value_font.setPointSize(16)
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


__all__ = ["CashierStatsDialog"]
