"""Application entry point.

Kept intentionally slim so PyInstaller can point directly at ``clinic.main:main``.
"""

from __future__ import annotations

import sys

from loguru import logger

from clinic.infrastructure.logging_setup import configure_logging


def main() -> int:
    configure_logging()
    logger.info("Starting Clinic LOR")
    try:
        from clinic.ui.app import run

        return run()
    except Exception:
        logger.exception("Fatal error during application startup")
        return 1


if __name__ == "__main__":
    sys.exit(main())
