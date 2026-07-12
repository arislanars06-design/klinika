"""Daily backup script.

Copies ``clinic.db`` into ``data/backups/clinic_YYYYMMDD.db`` and prunes files
older than ``settings.backup_retention_days``. Intended to be triggered by
cron or Task Scheduler; safe to run as often as you like.
"""

from __future__ import annotations

import shutil
from datetime import date, datetime, timedelta

from loguru import logger

from clinic.config import settings
from clinic.infrastructure.logging_setup import configure_logging


def run() -> None:
    configure_logging()
    settings.ensure_dirs()

    src = settings.db_path
    if not src.is_file():
        logger.warning("No database found at {} — nothing to back up", src)
        return

    dst = settings.backups_dir / f"clinic_{date.today():%Y%m%d}.db"
    shutil.copy2(src, dst)
    logger.info("Backup written: {}", dst)

    # Prune old backups
    cutoff = datetime.now() - timedelta(days=settings.backup_retention_days)
    removed = 0
    for path in settings.backups_dir.glob("clinic_*.db"):
        if datetime.fromtimestamp(path.stat().st_mtime) < cutoff:
            path.unlink()
            removed += 1
    if removed:
        logger.info("Pruned {} old backup(s)", removed)


if __name__ == "__main__":
    run()
