"""Login helpers.

Authentication is now backed by the ``web_users`` table (see
:mod:`clinic.domain.user_service`). The old shared-password path is kept as a
fallback ONLY while the DB has zero users — the first successful login using
``CLINIC_WEB_PASSWORD`` provisions an ``admin`` account named ``admin``.
"""

from __future__ import annotations

import hmac
from dataclasses import dataclass

from clinic.domain import user_service
from clinic.domain.user_service import WebUserDTO
from clinic.web.config import web_settings


@dataclass(frozen=True)
class AuthOutcome:
    """Result of an authentication attempt."""

    user: WebUserDTO | None
    reason: str = ""  # "" on success, otherwise a translation key


def try_login(username: str, password: str) -> AuthOutcome:
    """Authenticate against the ``web_users`` table.

    Special case for first-run bootstrap: if the DB is empty and the shared
    ``CLINIC_WEB_PASSWORD`` env var matches ``password``, provision an
    ``admin`` account and return it.
    """
    if not password:
        return AuthOutcome(None, "auth.wrong_password")

    # Bootstrap path: no users yet, admin creates itself using env password.
    if user_service.user_count() == 0:
        if hmac.compare_digest(
            password.encode("utf-8"),
            web_settings.password.encode("utf-8"),
        ):
            username_to_use = (username or "admin").strip().lower() or "admin"
            user_service.ensure_default_admin(
                username=username_to_use, password=password
            )
            # Now authenticate normally so ``last_login_at`` is set.
            user = user_service.authenticate(username_to_use, password)
            return AuthOutcome(user, "" if user else "auth.wrong_password")
        return AuthOutcome(None, "auth.wrong_password")

    # Regular path.
    user = user_service.authenticate(username, password)
    if user is None:
        return AuthOutcome(None, "auth.wrong_password")
    return AuthOutcome(user, "")


__all__ = ["AuthOutcome", "try_login"]
