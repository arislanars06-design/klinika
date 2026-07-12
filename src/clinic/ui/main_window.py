"""Main menu window with the three primary entry points and settings."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from clinic.domain import settings_service
from clinic.i18n.translator import SUPPORTED_LANGUAGES, t, translator


class MainWindow(QMainWindow):
    """Top-level window shown after language selection."""

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(720, 560)
        self._setup_ui()
        self._retranslate()
        translator.language_changed.connect(self._retranslate)

    # ----- UI construction -----

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        # ----- header -----
        self.clinic_label = QLabel()
        clinic_font = QFont()
        clinic_font.setPointSize(14)
        clinic_font.setBold(True)
        self.clinic_label.setFont(clinic_font)

        self.language_combo = QComboBox()
        for code in SUPPORTED_LANGUAGES:
            self.language_combo.addItem(code.upper(), code)
        self.language_combo.setCurrentText(translator.language.upper())
        self.language_combo.currentIndexChanged.connect(self._on_language_selected)

        header = QHBoxLayout()
        header.addWidget(self.clinic_label)
        header.addStretch(1)
        header.addWidget(QLabel("\U0001F30D"))
        header.addWidget(self.language_combo)

        # ----- big menu buttons -----
        self.btn_reception = self._menu_button("\U0001FA7A")
        self.btn_patients = self._menu_button("\U0001F4CB")
        self.btn_cashier = self._menu_button("\U0001F4B0")

        self.btn_reception.clicked.connect(self._open_reception)
        self.btn_patients.clicked.connect(self._open_patients)
        self.btn_cashier.clicked.connect(self._open_cashier)

        buttons = QVBoxLayout()
        buttons.setSpacing(16)
        buttons.addWidget(self.btn_reception)
        buttons.addWidget(self.btn_patients)
        buttons.addWidget(self.btn_cashier)

        # ----- footer -----
        self.btn_settings = QPushButton()
        self.btn_help = QPushButton()
        self.btn_settings.clicked.connect(self._open_settings)
        self.btn_help.clicked.connect(self._open_help)

        footer = QHBoxLayout()
        footer.addWidget(self.btn_settings)
        footer.addStretch(1)
        footer.addWidget(self.btn_help)

        # ----- assemble -----
        layout = QVBoxLayout(central)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.addLayout(header)
        layout.addSpacing(24)
        layout.addLayout(buttons)
        layout.addStretch(1)
        layout.addLayout(footer)

        # ----- menu bar (redundant with buttons but useful for keyboard) -----
        self.action_exit = QAction(self)
        self.action_exit.setShortcut("Ctrl+Q")
        self.action_exit.triggered.connect(self.close)
        self.menuBar().addAction(self.action_exit)

    def _menu_button(self, icon: str) -> QPushButton:
        btn = QPushButton()
        btn.setMinimumHeight(72)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        btn.setFont(font)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("icon_char", icon)
        return btn

    # ----- retranslation -----

    def _retranslate(self, *_args: object) -> None:
        self.setWindowTitle(t("app.title"))
        clinic_name_key = f"clinic_name_{translator.language}"
        clinic_name = settings_service.get(clinic_name_key) or t("app.title")
        self.clinic_label.setText(f"\U0001F3E5  {clinic_name}")

        self.btn_reception.setText(f"{self.btn_reception.property('icon_char')}  {t('menu.start_reception')}")
        self.btn_patients.setText(f"{self.btn_patients.property('icon_char')}  {t('menu.patients_history')}")
        self.btn_cashier.setText(f"{self.btn_cashier.property('icon_char')}  {t('menu.cashier')}")

        self.btn_settings.setText(f"\u2699\ufe0f  {t('menu.settings')}")
        self.btn_help.setText(f"\u2753  {t('menu.help')}")

        self.action_exit.setText(t("menu.exit"))

    # ----- actions -----

    def _on_language_selected(self, _index: int) -> None:
        new_lang = self.language_combo.currentData()
        if new_lang and new_lang != translator.language:
            translator.set_language(new_lang)
            settings_service.set_language(new_lang)

    def _open_reception(self) -> None:
        self._todo_dialog("Qabul oynasi")

    def _open_patients(self) -> None:
        self._todo_dialog("Bemorlar tarixi")

    def _open_cashier(self) -> None:
        self._todo_dialog("Kassa")

    def _open_settings(self) -> None:
        self._todo_dialog("Sozlamalar")

    def _open_help(self) -> None:
        QMessageBox.information(
            self,
            t("menu.help"),
            "Klinika LOR v0.1.0 (skelet).\n"
            "Milestone 1: base structure, DB, i18n, main menu.",
        )

    def _todo_dialog(self, screen_name: str) -> None:
        QMessageBox.information(
            self,
            screen_name,
            f"'{screen_name}' oynasi keyingi bosqichda qo'shiladi.\n"
            "Milestone 1 — hozircha faqat skelet ishlaydi.",
        )

    # ----- exit confirmation -----

    def closeEvent(self, event) -> None:  # type: ignore[override]
        reply = QMessageBox.question(
            self,
            t("menu.exit"),
            t("menu.exit_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
