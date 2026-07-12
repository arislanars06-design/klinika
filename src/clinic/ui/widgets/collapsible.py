"""A minimal collapsible ("accordion") panel.

Not exhaustive — covers what the Reception screen needs: a header button that
toggles the visibility of a child container. When expanded, the child widget
fills the available vertical space and shows a smooth arrow indicator.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class CollapsibleSection(QWidget):
    """Container with a clickable header that shows/hides its body widget."""

    toggled = Signal(bool)  # emitted with the new "expanded" state

    def __init__(
        self,
        title: str,
        body: QWidget,
        *,
        expanded: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._title = title
        self._body = body

        self._toggle_btn = QToolButton()
        self._toggle_btn.setStyleSheet("QToolButton { border: none; padding: 6px; text-align: left; }")
        self._toggle_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._toggle_btn.setArrowType(Qt.ArrowType.RightArrow)
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(False)
        self._toggle_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._toggle_btn.setText(title)
        self._toggle_btn.clicked.connect(self._on_toggled)

        self._body_frame = QFrame()
        self._body_frame.setFrameShape(QFrame.Shape.StyledPanel)
        body_layout = QVBoxLayout(self._body_frame)
        body_layout.setContentsMargins(12, 8, 12, 8)
        body_layout.addWidget(body)
        self._body_frame.setVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self._toggle_btn)
        layout.addWidget(self._body_frame)

        if expanded:
            self.set_expanded(True)

    # ----- API -----

    def set_title(self, title: str) -> None:
        self._title = title
        self._toggle_btn.setText(title)

    def is_expanded(self) -> bool:
        return self._toggle_btn.isChecked()

    def set_expanded(self, value: bool) -> None:
        if self._toggle_btn.isChecked() == value:
            return
        self._toggle_btn.setChecked(value)
        self._on_toggled(value)

    def body(self) -> QWidget:
        return self._body

    # ----- internal -----

    def _on_toggled(self, checked: bool) -> None:
        self._toggle_btn.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        )
        self._body_frame.setVisible(checked)
        self.toggled.emit(checked)
