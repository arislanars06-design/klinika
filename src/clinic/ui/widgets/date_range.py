"""Period picker widget: Today / Week / Month / Year / Custom.

Emits :attr:`period_changed` whenever the effective window shifts. Callers
should also invoke :meth:`current_period` to seed initial data.
"""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from clinic.domain.stats_service import Period, PeriodPreset, build_custom, build_period
from clinic.i18n.translator import t, translator


class DateRangeWidget(QWidget):
    """Radio-button period picker with an optional custom date range."""

    period_changed = Signal(object)  # emits Period

    def __init__(
        self,
        *,
        default: PeriodPreset = PeriodPreset.MONTH,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._preset = default

        # Radio buttons
        self._radio_today = QRadioButton()
        self._radio_week = QRadioButton()
        self._radio_month = QRadioButton()
        self._radio_year = QRadioButton()
        self._radio_custom = QRadioButton()

        self._group = QButtonGroup(self)
        for i, radio in enumerate(
            (
                self._radio_today,
                self._radio_week,
                self._radio_month,
                self._radio_year,
                self._radio_custom,
            )
        ):
            self._group.addButton(radio, i)
        self._presets_by_id = {
            0: PeriodPreset.TODAY,
            1: PeriodPreset.WEEK,
            2: PeriodPreset.MONTH,
            3: PeriodPreset.YEAR,
            4: PeriodPreset.CUSTOM,
        }

        # Custom date edits
        self.date_from = QDateEdit(calendarPopup=True)
        self.date_to = QDateEdit(calendarPopup=True)
        today = QDate.currentDate()
        self.date_from.setDate(today.addDays(-30))
        self.date_to.setDate(today)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setEnabled(False)
        self.date_to.setEnabled(False)

        self.label_dash = QLabel(" — ")
        self.label_period = QLabel()
        self.label_period.setStyleSheet("color: #616161;")

        radio_row = QHBoxLayout()
        for r in (
            self._radio_today,
            self._radio_week,
            self._radio_month,
            self._radio_year,
            self._radio_custom,
        ):
            radio_row.addWidget(r)
        radio_row.addStretch(1)

        custom_row = QHBoxLayout()
        custom_row.addWidget(self.date_from)
        custom_row.addWidget(self.label_dash)
        custom_row.addWidget(self.date_to)
        custom_row.addStretch(1)
        custom_row.addWidget(self.label_period)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)
        outer.addLayout(radio_row)
        outer.addLayout(custom_row)

        # Signals
        self._group.idClicked.connect(self._on_preset_clicked)
        self.date_from.dateChanged.connect(self._on_custom_changed)
        self.date_to.dateChanged.connect(self._on_custom_changed)

        # Initial state
        self._select_preset(default)
        translator.language_changed.connect(self._retranslate)
        self._retranslate()

    # ============================================================
    # Public API
    # ============================================================

    def current_period(self) -> Period:
        if self._preset == PeriodPreset.CUSTOM:
            return build_custom(
                self._qdate_to_py(self.date_from.date()),
                self._qdate_to_py(self.date_to.date()),
            )
        return build_period(self._preset)

    def set_preset(self, preset: PeriodPreset) -> None:
        self._select_preset(preset)

    # ============================================================
    # Internal
    # ============================================================

    @staticmethod
    def _qdate_to_py(q: QDate) -> date:
        return date(q.year(), q.month(), q.day())

    def _select_preset(self, preset: PeriodPreset) -> None:
        self._preset = preset
        # Sync the radio-button state without re-emitting signals.
        radio = {
            PeriodPreset.TODAY: self._radio_today,
            PeriodPreset.WEEK: self._radio_week,
            PeriodPreset.MONTH: self._radio_month,
            PeriodPreset.YEAR: self._radio_year,
            PeriodPreset.CUSTOM: self._radio_custom,
        }[preset]
        radio.blockSignals(True)
        radio.setChecked(True)
        radio.blockSignals(False)

        custom_enabled = preset == PeriodPreset.CUSTOM
        self.date_from.setEnabled(custom_enabled)
        self.date_to.setEnabled(custom_enabled)

        self._emit_period()

    def _on_preset_clicked(self, radio_id: int) -> None:
        preset = self._presets_by_id.get(radio_id, PeriodPreset.MONTH)
        self._select_preset(preset)

    def _on_custom_changed(self, *_args: object) -> None:
        if self._preset == PeriodPreset.CUSTOM:
            self._emit_period()

    def _emit_period(self) -> None:
        period = self.current_period()
        # Show the effective window as a helper label (great for MONTH etc).
        self.label_period.setText(
            f"({period.start.date().isoformat()} → {period.end.date().isoformat()})"
        )
        self.period_changed.emit(period)

    # ============================================================
    # i18n
    # ============================================================

    def _retranslate(self, *_args: object) -> None:
        self._radio_today.setText(t("stats.today"))
        self._radio_week.setText(t("stats.week"))
        self._radio_month.setText(t("stats.month"))
        self._radio_year.setText(t("stats.year"))
        self._radio_custom.setText(t("stats.custom"))
