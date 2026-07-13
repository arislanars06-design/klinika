"""Settings service: key-value persistence in the ``settings`` DB table.

Used for storing runtime configuration such as the interface language,
clinic name/address, logo path, and one-off flags like "first run done".
"""

from __future__ import annotations

from sqlalchemy import select

from clinic.db.database import session_scope
from clinic.db.models import Setting

# Well-known keys
KEY_LANGUAGE = "language"
KEY_CLINIC_NAME_UZ = "clinic_name_uz"
KEY_CLINIC_NAME_RU = "clinic_name_ru"
KEY_CLINIC_ADDRESS_UZ = "clinic_address_uz"
KEY_CLINIC_ADDRESS_RU = "clinic_address_ru"
KEY_CLINIC_PHONE = "clinic_phone"
KEY_CLINIC_LOGO_PATH = "clinic_logo_path"
KEY_FIRST_RUN_DONE = "first_run_done"
KEY_LAST_BACKUP_DATE = "last_backup_date"
# ---- Phase 4 additions -----------------------------------------------------
KEY_THEME = "web_theme"                # light | dark | auto
KEY_SAVE_FOLDER = "web_save_folder"    # download filename prefix / path hint


def get(key: str, default: str | None = None) -> str | None:
    with session_scope() as session:
        row = session.execute(select(Setting).where(Setting.key == key)).scalar_one_or_none()
        return row.value if row else default


def set_value(key: str, value: str) -> None:
    with session_scope() as session:
        row = session.execute(select(Setting).where(Setting.key == key)).scalar_one_or_none()
        if row is None:
            session.add(Setting(key=key, value=value))
        else:
            row.value = value


def is_first_run() -> bool:
    """Return True if the app hasn't gone through initial setup yet."""
    return get(KEY_FIRST_RUN_DONE) != "true"


def mark_first_run_done() -> None:
    set_value(KEY_FIRST_RUN_DONE, "true")


def get_language() -> str | None:
    return get(KEY_LANGUAGE)


def set_language(lang: str) -> None:
    set_value(KEY_LANGUAGE, lang)
