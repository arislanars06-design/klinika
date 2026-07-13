"""Read/write the clinic's identity (name, address, phone, logo, language).

Values are stored in the ``settings`` key-value table via
``clinic.domain.settings_service`` so the schema stays flat.
"""

from __future__ import annotations

from dataclasses import dataclass

from clinic.domain import settings_service


@dataclass
class ClinicInfo:
    """Snapshot of the clinic's public-facing details."""

    name_uz: str
    name_ru: str
    address_uz: str
    address_ru: str
    phone: str
    logo_path: str
    language: str
    # Phase 4: UI + workflow preferences shared by all users.
    theme: str = "light"          # light | dark | auto
    save_folder: str = ""         # hint prepended to downloaded filenames

    def localized_name(self, lang: str) -> str:
        return self.name_ru if lang == "ru" else self.name_uz

    def localized_address(self, lang: str) -> str:
        return self.address_ru if lang == "ru" else self.address_uz


VALID_THEMES = ("light", "dark", "auto")


def load() -> ClinicInfo:
    """Load the current clinic info, falling back to empty strings."""
    theme = settings_service.get(settings_service.KEY_THEME) or "light"
    if theme not in VALID_THEMES:
        theme = "light"
    return ClinicInfo(
        name_uz=settings_service.get(settings_service.KEY_CLINIC_NAME_UZ) or "",
        name_ru=settings_service.get(settings_service.KEY_CLINIC_NAME_RU) or "",
        address_uz=settings_service.get(settings_service.KEY_CLINIC_ADDRESS_UZ) or "",
        address_ru=settings_service.get(settings_service.KEY_CLINIC_ADDRESS_RU) or "",
        phone=settings_service.get(settings_service.KEY_CLINIC_PHONE) or "",
        logo_path=settings_service.get(settings_service.KEY_CLINIC_LOGO_PATH) or "",
        language=settings_service.get_language() or "uz",
        theme=theme,
        save_folder=settings_service.get(settings_service.KEY_SAVE_FOLDER) or "",
    )


def save(info: ClinicInfo) -> None:
    """Persist all clinic fields. Empty strings clear the setting."""
    settings_service.set_value(settings_service.KEY_CLINIC_NAME_UZ, info.name_uz.strip())
    settings_service.set_value(settings_service.KEY_CLINIC_NAME_RU, info.name_ru.strip())
    settings_service.set_value(settings_service.KEY_CLINIC_ADDRESS_UZ, info.address_uz.strip())
    settings_service.set_value(settings_service.KEY_CLINIC_ADDRESS_RU, info.address_ru.strip())
    settings_service.set_value(settings_service.KEY_CLINIC_PHONE, info.phone.strip())
    settings_service.set_value(settings_service.KEY_CLINIC_LOGO_PATH, info.logo_path.strip())
    if info.language:
        settings_service.set_language(info.language)
    theme = info.theme if info.theme in VALID_THEMES else "light"
    settings_service.set_value(settings_service.KEY_THEME, theme)
    settings_service.set_value(settings_service.KEY_SAVE_FOLDER, info.save_folder.strip())


def save_logo(path: str) -> None:
    settings_service.set_value(settings_service.KEY_CLINIC_LOGO_PATH, path.strip())


__all__ = ["ClinicInfo", "load", "save", "save_logo"]
