"""Logging configuration using loguru.

Writes to both stderr (for development) and a rotating daily file under
``data/logs/``. Uncaught exceptions are also captured.
"""

from __future__ import annotations

import sys
from datetime import datetime

from loguru import logger

from clinic.config import settings


def configure_logging() -> None:
    """Configure loguru sinks for the application."""
    settings.ensure_dirs()

    logger.remove()

    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}:{function}:{line}</cyan> - "
            "<level>{message}</level>"
        ),
        enqueue=True,
    )

    log_file = settings.logs_dir / f"clinic_{datetime.now():%Y-%m-%d}.log"
    logger.add(
        log_file,
        level="DEBUG",
        rotation="00:00",
        retention=f"{settings.backup_retention_days} days",
        encoding="utf-8",
        backtrace=True,
        diagnose=settings.debug,
        enqueue=True,
    )

    logger.info("Logging configured (level={}, file={})", settings.log_level, log_file)
