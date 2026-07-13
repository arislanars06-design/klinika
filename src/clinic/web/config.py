"""Web-layer configuration (session secret, shared password, bind host).

Values are read from environment variables (prefix ``CLINIC_WEB_``) with
safe defaults for local development. Production deployments must set
``CLINIC_WEB_SECRET`` and ``CLINIC_WEB_PASSWORD`` explicitly.
"""

from __future__ import annotations

import secrets

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WebSettings(BaseSettings):
    """Runtime settings for the FastAPI layer."""

    model_config = SettingsConfigDict(
        env_prefix="CLINIC_WEB_",
        extra="ignore",
    )

    # Session cookie signing key. A random default is generated per process
    # so unset production installs still work — but sessions won't survive
    # restarts unless the operator sets an explicit value.
    secret: str = Field(default_factory=lambda: secrets.token_urlsafe(48))

    # Shared password for the whole clinic staff (Phase 1 keeps auth
    # deliberately simple). Phase 3 will add per-user accounts.
    password: str = Field(default="clinic")

    # Cookie name (avoid conflicts with other apps on the same host).
    session_cookie_name: str = Field(default="clinic_session")

    # Session max age in seconds (default 12 hours — one working shift).
    session_max_age: int = Field(default=12 * 60 * 60)

    # Bind address / port for ``uvicorn``.
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)


web_settings = WebSettings()
