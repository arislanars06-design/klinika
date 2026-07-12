"""Settings → Clinic tab: name/address (uz+ru), phone, logo picker, language."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from clinic.domain import clinic_info_service
from clinic.i18n.translator import SUPPORTED_LANGUAGES, t, translator
from clinic.ui.settings.backup_widget import BackupSection


class ClinicTab(QWidget):
    """Editable snapshot of the clinic's public-facing identity."""

    LOGO_MAX_PREVIEW = 96

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._load()
        translator.language_changed.connect(self._retranslate)

    # ----- UI construction -----

    def _build_ui(self) -> None:
        self.name_uz_edit = QLineEdit()
        self.name_ru_edit = QLineEdit()
        self.address_uz_edit = QLineEdit()
        self.address_ru_edit = QLineEdit()
        self.phone_edit = QLineEdit()

        self.language_combo = QComboBox()
        for code in SUPPORTED_LANGUAGES:
            self.language_combo.addItem(t(f"language.{code}"), code)

        # Logo row
        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(self.LOGO_MAX_PREVIEW, self.LOGO_MAX_PREVIEW)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setStyleSheet("border: 1px dashed #bdbdbd;")
        self.logo_preview.setText(t("settings.clinic.logo.none"))

        self.logo_path_edit = QLineEdit()
        self.logo_path_edit.setReadOnly(True)

        self.logo_select_btn = QPushButton(t("settings.clinic.logo.select"))
        self.logo_select_btn.clicked.connect(self._on_logo_pick)

        logo_row = QHBoxLayout()
        logo_row.addWidget(self.logo_preview)
        right = QVBoxLayout()
        right.addWidget(self.logo_path_edit)
        right.addWidget(self.logo_select_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        logo_row.addLayout(right, 1)

        self.form = QFormLayout()
        self.form.addRow(t("settings.clinic.name_uz"), self.name_uz_edit)
        self.form.addRow(t("settings.clinic.name_ru"), self.name_ru_edit)
        self.form.addRow(t("settings.clinic.address_uz"), self.address_uz_edit)
        self.form.addRow(t("settings.clinic.address_ru"), self.address_ru_edit)
        self.form.addRow(t("settings.clinic.phone"), self.phone_edit)
        self.form.addRow(t("settings.language"), self.language_combo)
        self.form.addRow(t("settings.clinic.logo"), logo_row)

        self.save_btn = QPushButton(t("settings.clinic.save"))
        self.save_btn.clicked.connect(self._on_save)

        self.backup_section = BackupSection()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addLayout(self.form)
        layout.addWidget(self.save_btn, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addSpacing(12)
        layout.addWidget(self.backup_section, 1)

    # ----- data load/save -----

    def _load(self) -> None:
        info = clinic_info_service.load()
        self.name_uz_edit.setText(info.name_uz)
        self.name_ru_edit.setText(info.name_ru)
        self.address_uz_edit.setText(info.address_uz)
        self.address_ru_edit.setText(info.address_ru)
        self.phone_edit.setText(info.phone)
        self._set_logo(info.logo_path)
        idx = self.language_combo.findData(info.language)
        if idx >= 0:
            self.language_combo.setCurrentIndex(idx)

    def _on_save(self) -> None:
        info = clinic_info_service.ClinicInfo(
            name_uz=self.name_uz_edit.text(),
            name_ru=self.name_ru_edit.text(),
            address_uz=self.address_uz_edit.text(),
            address_ru=self.address_ru_edit.text(),
            phone=self.phone_edit.text(),
            logo_path=self.logo_path_edit.text(),
            language=self.language_combo.currentData(),
        )
        try:
            clinic_info_service.save(info)
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return

        # Apply the new language immediately so all open windows retranslate.
        translator.set_language(info.language)

        QMessageBox.information(self, t("settings.title"), t("settings.clinic.saved"))

    # ----- logo picker -----

    def _on_logo_pick(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("settings.clinic.logo.select"),
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.svg)",
        )
        if path:
            self._set_logo(path)

    def _set_logo(self, path: str) -> None:
        self.logo_path_edit.setText(path)
        if path and Path(path).is_file():
            pix = QPixmap(path)
            if not pix.isNull():
                self.logo_preview.setPixmap(
                    pix.scaled(
                        self.LOGO_MAX_PREVIEW,
                        self.LOGO_MAX_PREVIEW,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                self.logo_preview.setText("")
                return
        self.logo_preview.setPixmap(QPixmap())
        self.logo_preview.setText(t("settings.clinic.logo.none"))

    # ----- retranslation -----

    def _retranslate(self, *_args: object) -> None:
        # Re-label form rows by rebuilding the label texts in place.
        labels = [
            "settings.clinic.name_uz",
            "settings.clinic.name_ru",
            "settings.clinic.address_uz",
            "settings.clinic.address_ru",
            "settings.clinic.phone",
            "settings.language",
            "settings.clinic.logo",
        ]
        for i, key in enumerate(labels):
            item = self.form.itemAt(i, QFormLayout.ItemRole.LabelRole)
            if item and item.widget():
                item.widget().setText(t(key))
        self.logo_select_btn.setText(t("settings.clinic.logo.select"))
        self.save_btn.setText(t("settings.clinic.save"))
        # Language combo labels
        for i in range(self.language_combo.count()):
            code = self.language_combo.itemData(i)
            self.language_combo.setItemText(i, t(f"language.{code}"))
        # Logo placeholder text
        if not self.logo_path_edit.text():
            self.logo_preview.setText(t("settings.clinic.logo.none"))
