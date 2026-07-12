"""Landing page: language selection on first run, then main menu."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from clinic.domain import settings_service
from clinic.web.deps import LANGUAGE_COOKIE, get_lang

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """Show the language dialog on first launch, otherwise the main menu."""
    templates = request.app.state.templates

    stored_lang = settings_service.get_language()
    if not stored_lang and not request.cookies.get(LANGUAGE_COOKIE):
        return templates.TemplateResponse(
            request,
            "language_select.html",
            {"lang": "uz"},
        )

    lang = get_lang(request)
    clinic_name = settings_service.get(f"clinic_name_{lang}") or ""
    return templates.TemplateResponse(
        request,
        "home.html",
        {"lang": lang, "clinic_name": clinic_name},
    )
