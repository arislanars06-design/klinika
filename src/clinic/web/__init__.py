"""HTTP / HTML front-end for the clinic system.

The web layer is an optional companion to the PySide6 desktop app: it
reuses every ``clinic.domain`` service, the same SQLite database, the
same i18n catalogs and Word template. Deployment scenarios supported:

- Local (single machine)  — ``python -m clinic.web.main``
- Clinic LAN (multi-seat) — bind ``0.0.0.0`` on one machine; others open
  ``http://<host>:8000`` from their browser
- Cloud                    — run behind a reverse proxy (nginx/Caddy)
  and set ``CLINIC_WEB_SECRET`` + ``CLINIC_WEB_PASSWORD`` env vars
"""

from clinic.web.app import create_app

__all__ = ["create_app"]
