"""Shared FastAPI dependencies: current language, template engine, auth guard."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.templating import Jinja2Templates

from clinic.i18n.translator import SUPPORTED_LANGUAGES, translator

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ---------------------------------------------------------------------------
# Language handling
# ---------------------------------------------------------------------------


def resolve_language(request: Request) -> str:
    """Return the active language, preferring session value then default."""
    session = getattr(request, "session", None)
    if session is not None:
        lang = session.get("lang")
        if lang in SUPPORTED_LANGUAGES:
            translator.set_language(lang)
            return lang
    return translator.language


def current_user(request: Request) -> dict | None:
    """Return the logged-in user info (or ``None``) stored in the session."""
    session = getattr(request, "session", None)
    if session is None:
        return None
    user = session.get("user")
    role = session.get("role")
    if not user:
        return None
    return {"username": user, "role": role or "staff", "full_name": session.get("full_name", "")}


# ---------------------------------------------------------------------------
# Template rendering helper
# ---------------------------------------------------------------------------


def render(
    request: Request,
    template_name: str,
    context: dict[str, Any] | None = None,
    *,
    status_code: int = 200,
):
    """Render a Jinja template with the standard clinic context injected."""
    from clinic.domain import clinic_info_service

    ctx: dict[str, Any] = {"request": request}
    if context:
        ctx.update(context)

    lang = resolve_language(request)
    clinic = clinic_info_service.load()
    ctx.setdefault("lang", lang)
    ctx.setdefault("supported_langs", SUPPORTED_LANGUAGES)
    ctx.setdefault("clinic_info", clinic)
    ctx.setdefault("t", translator.t)  # inline usage: {{ t("menu.home") }}
    ctx.setdefault("user", current_user(request))
    return templates.TemplateResponse(request, template_name, ctx, status_code=status_code)


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------


def require_login(request: Request) -> str:
    """Raise 401 (redirects handled by exception handler) if not signed in."""
    user = request.session.get("user") if hasattr(request, "session") else None
    if not user:
        # 401 turned into a redirect by an exception handler in ``app.py``.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="login_required")
    return user


def require_admin(request: Request) -> str:
    """Gate a route to admin-role users only."""
    user = require_login(request)
    role = request.session.get("role") if hasattr(request, "session") else None
    if role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_only")
    return user
