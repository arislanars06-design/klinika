"""First-run language chooser.

Two large buttons for Uzbek / Russian. The result drives both the runtime
translator and the persisted ``settings.language`` row.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class LanguageDialog(QDialog):
    """Modal dialog asking the user to choose an interface language."""

    def __init__(self) -> None:
        super().__init__()
        self.selected: str | None = None

        # Title/window setup
        self.setWindowTitle("Klinika LOR / Клиника ЛОР")
        self.setModal(True)
        self.setFixedSize(520, 280)

        # Prompt shown in both languages so a first-time user always understands
        header = QLabel("Tilni tanlang\nВыберите язык")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        header.setFont(font)

        # Buttons
        self.btn_uz = self._build_button("O'ZBEKCHA", "\U0001F1FA\U0001F1FF")
        self.btn_ru = self._build_button("РУССКИЙ", "\U0001F1F7\U0001F1FA")

        self.btn_uz.clicked.connect(lambda: self._choose("uz"))
        self.btn_ru.clicked.connect(lambda: self._choose("ru"))

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.btn_uz)
        buttons.addSpacing(24)
        buttons.addWidget(self.btn_ru)
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.addWidget(header)
        layout.addStretch(1)
        layout.addLayout(buttons)
        layout.addStretch(1)

    def _build_button(self, text: str, flag: str) -> QPushButton:
        btn = QPushButton(f"{flag}\n{text}")
        btn.setMinimumSize(180, 120)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        btn.setFont(font)
        return btn

    def _choose(self, code: str) -> None:
        self.selected = code
        self.accept()
