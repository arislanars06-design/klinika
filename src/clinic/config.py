"""Application configuration.

Loads settings from environment or defaults. Paths are relative to the
executable/project root so the app is fully portable.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    """Return the writable project root.

    When frozen by PyInstaller, ``sys.executable`` sits next to ``data/``.
    In development, we walk up from this file until we find the ``src`` folder.
    """
    import sys

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "src").is_dir() and (parent / "pyproject.toml").is_file():
            return parent
    return here.parent


ROOT = _project_root()


class Settings(BaseSettings):
    """Runtime settings loaded from ``.env`` or environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        env_prefix="CLINIC_",
        extra="ignore",
    )

    # Data
    data_dir: Path = Field(default=ROOT / "data")
    db_filename: str = Field(default="clinic.db")
    backup_dir_name: str = Field(default="backups")
    logs_dir_name: str = Field(default="logs")
    backup_retention_days: int = Field(default=30)

    # Localization
    default_language: str = Field(default="uz")

    # Debug / logging
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Package resources (bundled with the app)
    package_dir: Path = Field(default=Path(__file__).resolve().parent)

    @property
    def db_path(self) -> Path:
        return self.data_dir / self.db_filename

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    @property
    def backups_dir(self) -> Path:
        return self.data_dir / self.backup_dir_name

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / self.logs_dir_name

    @property
    def catalogs_dir(self) -> Path:
        return self.package_dir / "catalogs"

    @property
    def i18n_dir(self) -> Path:
        return self.package_dir / "i18n"

    @property
    def templates_dir(self) -> Path:
        return ROOT / "templates"

    def ensure_dirs(self) -> None:
        """Create runtime directories if they don't already exist."""
        for directory in (self.data_dir, self.backups_dir, self.logs_dir):
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
