"""Thin matplotlib canvas wrapper for use inside Qt layouts.

Two convenience helpers cover everything M3 needs: :meth:`plot_bar` for
top-diagnosis-style categorical charts and :meth:`plot_time_series` for the
day-by-day trend chart.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget


class ChartCanvas(QWidget):
    """Wrapper around a single Matplotlib figure inside a QWidget."""

    def __init__(self, parent: QWidget | None = None, height: int = 220) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(6, 3), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    # ============================================================
    # Public API
    # ============================================================

    def clear(self) -> None:
        self.figure.clear()
        self.canvas.draw_idle()

    def show_empty_message(self, message: str) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            fontsize=11,
            color="#9e9e9e",
            transform=ax.transAxes,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        self.canvas.draw_idle()

    def plot_bar(
        self,
        labels: list[str],
        values: list[float],
        *,
        title: str = "",
        color: str = "#1976d2",
        y_label: str = "",
    ) -> None:
        if not labels:
            self.show_empty_message(title or "—")
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.bar(labels, values, color=color)
        if title:
            ax.set_title(title, fontsize=11)
        if y_label:
            ax.set_ylabel(y_label)
        ax.tick_params(axis="x", rotation=25, labelsize=8)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        self.canvas.draw_idle()

    def plot_time_series(
        self,
        dates: list[str],
        values: list[float],
        *,
        title: str = "",
        color: str = "#43a047",
        y_label: str = "",
    ) -> None:
        if not dates:
            self.show_empty_message(title or "—")
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(dates, values, marker="o", color=color, linewidth=2)
        ax.fill_between(dates, values, color=color, alpha=0.15)
        if title:
            ax.set_title(title, fontsize=11)
        if y_label:
            ax.set_ylabel(y_label)
        ax.tick_params(axis="x", rotation=30, labelsize=8)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.grid(True, alpha=0.2, axis="y")
        self.canvas.draw_idle()
