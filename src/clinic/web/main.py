"""Uvicorn entry point.

Run with either of::

    python -m clinic.web.main
    clinic-web

Bind address & port come from ``CLINIC_WEB_HOST`` / ``CLINIC_WEB_PORT``.
"""

from __future__ import annotations

import uvicorn

from clinic.web.app import create_app
from clinic.web.config import web_settings

# Uvicorn re-imports this attribute when using --reload, so keep it top-level.
app = create_app()


def main() -> None:
    uvicorn.run(
        "clinic.web.main:app",
        host=web_settings.host,
        port=web_settings.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
