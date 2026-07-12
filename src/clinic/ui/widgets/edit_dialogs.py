"""Small modal dialogs for adding/editing doctors and services."""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from clinic.domain import doctor_service, service_service
from clinic.domain.dto import DoctorDTO, ServiceDTO
from clinic.i18n.translator import t
from clinic.infrastructure.validators import ValidationError

# ============================================================================
# Doctor dialog
# ============================================================================


class DoctorDialog(QDialog):
    """Add or edit a doctor. Returns the saved DTO via :meth:`result_dto`."""

    def __init__(self, doctor: DoctorDTO | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._doctor = doctor
        self._result: DoctorDTO | None = None

        title_key = "settings.doctors.dialog.title.edit" if doctor else "settings.doctors.dialog.title.add"
        self.setWindowTitle(t(title_key))
        self.setModal(True)
        self.setMinimumWidth(420)

        self.name_edit = QLineEdit(doctor.full_name if doctor else "")
        self.phone_edit = QLineEdit(doctor.phone or "" if doctor else "")
        self.phone_edit.setPlaceholderText("+998 90 123 45 67")

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #c62828;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        form = QFormLayout()
        form.addRow(t("settings.doctors.column.name") + " *", self.name_edit)
        form.addRow(t("settings.doctors.column.phone"), self.phone_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(t("common.save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("common.cancel"))
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)

    def result_dto(self) -> DoctorDTO | None:
        return self._result

    def _on_save(self) -> None:
        self.error_label.hide()
        try:
            if self._doctor is None:
                self._result = doctor_service.create(
                    full_name=self.name_edit.text(),
                    phone=self.phone_edit.text() or None,
                )
            else:
                self._result = doctor_service.update(
                    self._doctor.id,
                    full_name=self.name_edit.text(),
                    phone=self.phone_edit.text() or "",
                )
        except ValidationError as ve:
            messages = [self._format_error(name, err) for name, err in ve.errors.items()]
            self.error_label.setText("\n".join(messages))
            self.error_label.show()
            return
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        self.accept()

    @staticmethod
    def _format_error(field: str, err) -> str:  # type: ignore[no-untyped-def]
        label = t(f"settings.doctors.column.{field.replace('full_name', 'name')}") if field != "phone" else t("settings.doctors.column.phone")
        message = t(err.message_key, **err.params)
        return f"• {label}: {message}"


# ============================================================================
# Service dialog
# ============================================================================


class ServiceDialog(QDialog):
    """Add or edit a billable clinic service (with uz+ru name and price)."""

    def __init__(self, service: ServiceDTO | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self._result: ServiceDTO | None = None

        title_key = (
            "settings.services.dialog.title.edit" if service else "settings.services.dialog.title.add"
        )
        self.setWindowTitle(t(title_key))
        self.setModal(True)
        self.setMinimumWidth(460)

        self.name_uz_edit = QLineEdit(service.name_uz if service else "")
        self.name_ru_edit = QLineEdit(service.name_ru if service else "")

        self.price_edit = QDoubleSpinBox()
        self.price_edit.setDecimals(2)
        self.price_edit.setRange(0.0, 10_000_000_000.0)
        self.price_edit.setSingleStep(1000.0)
        self.price_edit.setSuffix(" " + t("cashier.currency"))
        self.price_edit.setGroupSeparatorShown(True)
        if service:
            self.price_edit.setValue(float(service.price))

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #c62828;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        form = QFormLayout()
        form.addRow(t("settings.services.dialog.name_uz") + " *", self.name_uz_edit)
        form.addRow(t("settings.services.dialog.name_ru") + " *", self.name_ru_edit)
        form.addRow(t("settings.services.dialog.price") + " *", self.price_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(t("common.save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("common.cancel"))
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)

    def result_dto(self) -> ServiceDTO | None:
        return self._result

    def _on_save(self) -> None:
        self.error_label.hide()
        try:
            price = Decimal(str(self.price_edit.value()))
            if self._service is None:
                self._result = service_service.create(
                    name_uz=self.name_uz_edit.text(),
                    name_ru=self.name_ru_edit.text(),
                    price=price,
                )
            else:
                self._result = service_service.update(
                    self._service.id,
                    name_uz=self.name_uz_edit.text(),
                    name_ru=self.name_ru_edit.text(),
                    price=price,
                )
        except ValidationError as ve:
            messages: list[str] = []
            for field, err in ve.errors.items():
                messages.append(f"• {field}: {t(err.message_key, **err.params)}")
            self.error_label.setText("\n".join(messages))
            self.error_label.show()
            return
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), f"{t('error.db')}\n\n{exc}")
            return
        self.accept()


__all__ = ["DoctorDialog", "ServiceDialog"]
