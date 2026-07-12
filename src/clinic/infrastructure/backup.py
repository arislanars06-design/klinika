"""SQLite backup helpers.

Two flavours:

* :func:`daily_auto_backup` — one automatic snapshot per calendar day. Run at
  application startup. Uses the same ``sqlite3.Connection.backup`` API that
  SQLite's ``sqlite3`` CLI uses; safe against WAL because SQLite handles the
  file locking for us.
* :func:`manual_backup` — save to an arbitrary path chosen by the user.

Old snapshots older than ``settings.backup_retention_days`` are cleaned up
automatically after each backup.
"""

from __future__ import annotations

import shutil
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from loguru import logger
from sqlalchemy.orm import sessionmaker

from clinic.config import settings
from clinic.domain import settings_service

DATE_FMT = "%Y%m%d"
BACKUP_PREFIX = "clinic_"


@dataclass(frozen=True)
class BackupEntry:
    """A backup file on disk plus its parsed date and size."""

    path: Path
    created_on: date
    size_bytes: int

    @property
    def filename(self) -> str:
        return self.path.name


# ============================================================================
# Public API
# ============================================================================


def force_daily_backup() -> BackupEntry:
    """Refresh today's backup unconditionally, then run cleanup.

    Unlike :func:`daily_auto_backup`, this always writes (overwriting an
    existing same-day snapshot) and is meant for the ``Create backup now``
    button in Settings.
    """
    settings.ensure_dirs()
    source = settings.db_path
    if not source.exists():
        raise FileNotFoundError(f"Source DB not found: {source}")
    today = date.today()
    dest = settings.backups_dir / _filename_for(today)
    _copy_database(source, dest)
    settings_service.set_value(settings_service.KEY_LAST_BACKUP_DATE, today.isoformat())
    entry = _entry_from(dest)
    cleanup_old_backups()
    logger.info("Manual daily backup refreshed: {}", dest)
    assert entry is not None
    return entry


def daily_auto_backup() -> BackupEntry | None:
    """Ensure today's backup exists. No-op if one has already been made today.

    Returns the created ``BackupEntry`` (or ``None`` if today's backup already
    existed / no source DB yet). Failures are logged and swallowed — the app
    should keep running even if the backup step fails.
    """
    try:
        settings.ensure_dirs()
        today = date.today()
        marker = settings_service.get(settings_service.KEY_LAST_BACKUP_DATE)
        if marker == today.isoformat() and _todays_backup_exists(today):
            return None

        source = settings.db_path
        if not source.exists():
            logger.info("Skip auto-backup — DB file not created yet")
            return None

        dest = settings.backups_dir / _filename_for(today)
        if dest.exists():
            # Backup file is already there; refresh the marker and exit.
            settings_service.set_value(settings_service.KEY_LAST_BACKUP_DATE, today.isoformat())
            return _entry_from(dest)

        _copy_database(source, dest)
        settings_service.set_value(settings_service.KEY_LAST_BACKUP_DATE, today.isoformat())
        entry = _entry_from(dest)
        logger.info("Daily auto-backup created: {}", dest)

        removed = cleanup_old_backups()
        if removed:
            logger.info("Cleaned up {} old backup file(s)", removed)
        return entry
    except Exception:
        logger.exception("Auto-backup failed")
        return None


def manual_backup(destination: Path | str) -> BackupEntry:
    """Copy the current DB to ``destination``. Overwrites if already there."""
    settings.ensure_dirs()
    source = settings.db_path
    if not source.exists():
        raise FileNotFoundError(f"Source DB not found: {source}")

    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    _copy_database(source, dest)
    logger.info("Manual backup written to: {}", dest)
    try:
        size = dest.stat().st_size
    except OSError:
        size = 0
    return BackupEntry(path=dest, created_on=date.today(), size_bytes=size)


def list_backups() -> list[BackupEntry]:
    """Return backups sorted newest-first."""
    settings.ensure_dirs()
    result: list[BackupEntry] = []
    for path in settings.backups_dir.glob(f"{BACKUP_PREFIX}*.db"):
        entry = _entry_from(path)
        if entry is not None:
            result.append(entry)
    return sorted(result, key=lambda e: e.created_on, reverse=True)


def restore_from(source: Path | str) -> Path:
    """Restore the DB from ``source``.

    The current DB is preserved as ``<db>.old-YYYYMMDD-HHMMSS`` so the user
    can roll back if the restore turns out to be the wrong choice. The
    SQLAlchemy engine + session factory are rebuilt so callers see the new
    data immediately.
    """
    settings.ensure_dirs()
    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(f"Backup file not found: {source_path}")

    target = settings.db_path
    _dispose_engine()

    if target.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        rescue = target.with_suffix(target.suffix + f".old-{stamp}")
        target.rename(rescue)
        logger.info("Current DB moved aside to: {}", rescue)
        # Also clean up WAL/SHM files that could confuse the new DB.
        for sfx in ("-wal", "-shm"):
            extra = target.parent / (target.name + sfx)
            if extra.exists():
                extra.unlink(missing_ok=True)

    shutil.copy2(source_path, target)
    _rebuild_engine()
    logger.info("Database restored from: {}", source_path)
    return target


def cleanup_old_backups() -> int:
    """Delete backups older than ``settings.backup_retention_days``.

    Returns the count of files removed.
    """
    settings.ensure_dirs()
    if settings.backup_retention_days <= 0:
        return 0
    cutoff = date.today() - timedelta(days=settings.backup_retention_days)
    removed = 0
    for entry in list_backups():
        if entry.created_on < cutoff:
            try:
                entry.path.unlink()
                removed += 1
            except OSError:
                logger.warning("Could not remove old backup: {}", entry.path)
    return removed


# ============================================================================
# Internals
# ============================================================================


def _filename_for(day: date) -> str:
    return f"{BACKUP_PREFIX}{day.strftime(DATE_FMT)}.db"


def _todays_backup_exists(today: date) -> bool:
    return (settings.backups_dir / _filename_for(today)).exists()


def _entry_from(path: Path) -> BackupEntry | None:
    try:
        raw = path.stem.removeprefix(BACKUP_PREFIX)
        created = datetime.strptime(raw, DATE_FMT).date()
    except ValueError:
        return None
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    return BackupEntry(path=path, created_on=created, size_bytes=size)


def _copy_database(source: Path, dest: Path) -> None:
    """Copy ``source`` SQLite file into ``dest`` using the online backup API."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    src_conn = sqlite3.connect(str(source))
    try:
        # ``dest.unlink(missing_ok=True)`` guarantees a clean file for the
        # backup API to write into.
        dest.unlink(missing_ok=True)
        dst_conn = sqlite3.connect(str(dest))
        try:
            with dst_conn:
                src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
    finally:
        src_conn.close()


def _dispose_engine() -> None:
    """Close all connections so the DB file becomes movable."""
    from clinic.db import database as dbmod

    try:
        dbmod.engine.dispose()
    except Exception:
        logger.exception("Failed to dispose engine before restore")


def _rebuild_engine() -> None:
    """Recreate ``dbmod.engine`` + ``SessionLocal`` after a restore/settings swap."""
    from clinic.db import database as dbmod

    dbmod.engine = dbmod._make_engine()
    dbmod.SessionLocal = sessionmaker(
        bind=dbmod.engine, expire_on_commit=False, future=True
    )


__all__ = [
    "BackupEntry",
    "cleanup_old_backups",
    "daily_auto_backup",
    "force_daily_backup",
    "list_backups",
    "manual_backup",
    "restore_from",
]
