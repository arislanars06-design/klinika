"""FastAPI dependency helpers.

These small functions live at the seam between the HTTP layer and the domain
services. They give templates and routes typed access to the current language
and a request-scoped DB session.
"""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from clinic.db.database import SessionLocal
from clinic.i18n.translator import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

LANGUAGE_COOKIE = "clinic_lang"


def get_db() -> Iterator[Session]:
    """Yield a request-scoped SQLAlchemy session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_lang(request: Request) -> str:
    """Return the active language.

    Order of precedence: URL query -> cookie -> default. Kept trivial on
    purpose so callers can override for a single request.
    """
    lang = request.query_params.get("lang") or request.cookies.get(LANGUAGE_COOKIE)
    if lang in SUPPORTED_LANGUAGES:
        return lang
    return DEFAULT_LANGUAGE


LangDep = Depends(get_lang)
DbDep = Depends(get_db)
