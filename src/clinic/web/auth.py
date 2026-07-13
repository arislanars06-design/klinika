"""Very small password-based auth.

Phase 1 uses one shared password read from ``CLINIC_WEB_PASSWORD`` so any
clinic staff member can sign in from any device on the network. Sessions
are Starlette-signed cookies; nothing is stored server-side.

Phase 3 will replace this with per-user accounts + role-based access.
"""

from __future__ import annotations

import hmac

from clinic.web.config import web_settings


def check_password(candidate: str) -> bool:
    """Constant-time comparison against the configured password."""
    return hmac.compare_digest(candidate.encode("utf-8"), web_settings.password.encode("utf-8"))
