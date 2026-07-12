"""Placeholder tab for user-added complaint / LOR STATUS catalog items (M4)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from clinic.i18n.translator import t, translator


class CatalogsTab(QWidget):
    """Empty tab that explains this section is coming in a later milestone."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.message = QLabel()
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.addStretch(1)
        layout.addWidget(self.title_label)
        layout.addSpacing(12)
        layout.addWidget(self.message)
        layout.addStretch(2)

        self._retranslate()
        translator.language_changed.connect(self._retranslate)

    def _retranslate(self, *_args: object) -> None:
        self.title_label.setText(t("settings.tab.catalogs"))
        self.message.setText(t("settings.catalogs.placeholder"))
