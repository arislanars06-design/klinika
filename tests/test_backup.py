"""Tests for :mod:`clinic.infrastructure.backup`.

The ``isolated_db`` autouse fixture rebinds ``clinic.config.settings`` per
test, so we always dereference it lazily via ``clinic.config.settings`` rather
than importing the object at module load time.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from clinic import config
from clinic.domain import doctor_service, settings_service
from clinic.infrastructure import backup as backup_service


def _s():  # type: ignore[no-untyped-def]
    """Shortcut for the current settings snapshot (see fixture note above)."""
    return config.settings


def _seed_doctor() -> int:
    doc = doctor_service.create(full_name="Karimov Ali")
    return doc.id


# ============================================================
# daily_auto_backup
# ============================================================


def test_daily_auto_backup_creates_file() -> None:
    _seed_doctor()
    entry = backup_service.daily_auto_backup()
    assert entry is not None
    assert entry.path.exists()
    assert entry.created_on == date.today()
    assert entry.size_bytes > 0


def test_daily_auto_backup_is_idempotent() -> None:
    _seed_doctor()
    first = backup_service.daily_auto_backup()
    second = backup_service.daily_auto_backup()
    assert first is not None
    assert second is None


def test_daily_auto_backup_no_db_returns_none() -> None:
    _s().db_path.unlink(missing_ok=True)
    assert backup_service.daily_auto_backup() is None


def test_daily_auto_backup_updates_last_backup_marker() -> None:
    _seed_doctor()
    backup_service.daily_auto_backup()
    marker = settings_service.get(settings_service.KEY_LAST_BACKUP_DATE)
    assert marker == date.today().isoformat()


# ============================================================
# force_daily_backup
# ============================================================


def test_force_daily_backup_overwrites() -> None:
    _seed_doctor()
    first = backup_service.daily_auto_backup()
    assert first is not None
    doctor_service.create(full_name="Aliyev Bekzod")
    second = backup_service.force_daily_backup()
    assert second.path == first.path
    assert second.size_bytes >= first.size_bytes


def test_force_daily_backup_requires_db_file() -> None:
    _s().db_path.unlink(missing_ok=True)
    with pytest.raises(FileNotFoundError):
        backup_service.force_daily_backup()


# ============================================================
# manual_backup
# ============================================================


def test_manual_backup_writes_to_chosen_path(tmp_path: Path) -> None:
    _seed_doctor()
    dest = tmp_path / "exported.db"
    entry = backup_service.manual_backup(dest)
    assert entry.path == dest
    assert dest.exists()
    assert entry.size_bytes > 0


def test_manual_backup_missing_source_raises(tmp_path: Path) -> None:
    _s().db_path.unlink(missing_ok=True)
    with pytest.raises(FileNotFoundError):
        backup_service.manual_backup(tmp_path / "x.db")


# ============================================================
# list_backups
# ============================================================


def test_list_backups_returns_newest_first() -> None:
    _s().ensure_dirs()
    (_s().backups_dir / "clinic_20260610.db").write_bytes(b"a")
    (_s().backups_dir / "clinic_20260701.db").write_bytes(b"b")

    entries = backup_service.list_backups()
    filenames = [e.filename for e in entries]
    # The two seeded files must appear in "newest first" order relative to
    # each other. Any additional entries created by other means are ignored
    # for the ordering check.
    idx_new = filenames.index("clinic_20260701.db")
    idx_old = filenames.index("clinic_20260610.db")
    assert idx_new < idx_old


def test_list_backups_ignores_unparseable_filenames() -> None:
    _s().ensure_dirs()
    (_s().backups_dir / "random.db").write_bytes(b"garbage")
    (_s().backups_dir / "clinic_20260101.db").write_bytes(b"ok")
    entries = backup_service.list_backups()
    filenames = {e.filename for e in entries}
    assert "clinic_20260101.db" in filenames
    assert "random.db" not in filenames


# ============================================================
# restore_from
# ============================================================


def test_restore_from_backup_reverts_state() -> None:
    empty_snapshot = backup_service.daily_auto_backup()
    assert empty_snapshot is not None
    assert doctor_service.list_all() == []

    doc_id = _seed_doctor()
    assert len(doctor_service.list_all()) == 1

    backup_service.restore_from(empty_snapshot.path)
    assert doctor_service.list_all() == []
    assert doctor_service.get(doc_id) is None


def test_restore_from_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        backup_service.restore_from(tmp_path / "does_not_exist.db")


def test_restore_keeps_old_db_alongside() -> None:
    _seed_doctor()
    snapshot = backup_service.daily_auto_backup()
    assert snapshot is not None
    backup_service.restore_from(snapshot.path)
    olds = list(_s().db_path.parent.glob(_s().db_path.name + ".old-*"))
    assert len(olds) >= 1


# ============================================================
# cleanup
# ============================================================


def test_cleanup_removes_files_older_than_retention() -> None:
    _s().backup_retention_days = 30
    _s().ensure_dirs()

    old_file = _s().backups_dir / "clinic_20200101.db"
    fresh_file = _s().backups_dir / f"clinic_{date.today():%Y%m%d}.db"
    old_file.write_bytes(b"x")
    fresh_file.write_bytes(b"x")

    removed = backup_service.cleanup_old_backups()
    assert removed >= 1
    assert not old_file.exists()
    assert fresh_file.exists()


def test_cleanup_zero_retention_is_noop() -> None:
    _s().backup_retention_days = 0
    _s().ensure_dirs()
    (_s().backups_dir / "clinic_20200101.db").write_bytes(b"x")
    assert backup_service.cleanup_old_backups() == 0
