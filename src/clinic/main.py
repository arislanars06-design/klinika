"""Application entry point.

Runs the FastAPI app under uvicorn. Kept intentionally slim so PyInstaller /
systemd can point directly at ``clinic.main:main`` or ``clinic.web.app:create_app``.
"""

from __future__ import annotations

import argparse
import sys

from loguru import logger

from clinic.config import settings
from clinic.infrastructure.logging_setup import configure_logging

# Exposed at module level so ``uvicorn clinic.main:app`` works too.
app = None  # populated lazily by ``_get_app`` to keep import time low


def _get_app():
    global app
    if app is None:
        from clinic.web.app import create_app

        app = create_app()
    return app


def main() -> int:
    configure_logging()
    logger.info("Starting Clinic LOR web (v0.1.0)")

    parser = argparse.ArgumentParser(prog="clinic-lor", description="Klinika LOR web server")
    parser.add_argument("--host", default="127.0.0.1", help="bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="bind port (default: 8000)")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="reload on code changes (development only)",
    )
    args = parser.parse_args()

    try:
        import uvicorn

        _get_app()  # touch the factory once so import errors surface early
        uvicorn.run(
            "clinic.web.app:create_app",
            host=args.host,
            port=args.port,
            reload=args.reload or settings.debug,
            factory=True,
            log_config=None,  # let loguru handle it
        )
        return 0
    except Exception:  # noqa: BLE001
        logger.exception("Fatal error during startup")
        return 1


if __name__ == "__main__":
    sys.exit(main())
