"""Top-level Settings dialog with 4 tabs.

Non-modal so users can keep working with the main window in parallel — but we
still expose ``exec()`` from :class:`QDialog` for callers that want modal.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from clinic.i18n.translator import t, translator
from clinic.ui.settings.catalogs_tab import CatalogsTab
from clinic.ui.settings.clinic_tab import ClinicTab
from clinic.ui.settings.doctors_tab import DoctorsTab
from clinic.ui.settings.services_tab import ServicesTab


class SettingsWindow(QDialog):
    """Settings hub: clinic / doctors / services / catalogs."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("settings.title"))
        self.setMinimumSize(820, 560)

        self.tabs = QTabWidget()
        self.clinic_tab = ClinicTab(self)
        self.doctors_tab = DoctorsTab(self)
        self.services_tab = ServicesTab(self)
        self.catalogs_tab = CatalogsTab(self)

        self.tabs.addTab(self.clinic_tab, t("settings.tab.clinic"))
        self.tabs.addTab(self.doctors_tab, t("settings.tab.doctors"))
        self.tabs.addTab(self.services_tab, t("settings.tab.services"))
        self.tabs.addTab(self.catalogs_tab, t("settings.tab.catalogs"))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        self.close_button.setText(t("common.close"))
        buttons.rejected.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        layout.addWidget(buttons)

        translator.language_changed.connect(self._retranslate)

    def _retranslate(self, *_args: object) -> None:
        self.setWindowTitle(t("settings.title"))
        self.tabs.setTabText(0, t("settings.tab.clinic"))
        self.tabs.setTabText(1, t("settings.tab.doctors"))
        self.tabs.setTabText(2, t("settings.tab.services"))
        self.tabs.setTabText(3, t("settings.tab.catalogs"))
        self.close_button.setText(t("common.close"))


__all__ = ["SettingsWindow"]
