"""Language selection endpoints.

- ``POST /language/{lang}`` sets the language, persists it, and redirects home.
- ``GET  /language`` shows the picker again if the user wants to change it.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from clinic.domain import settings_service
from clinic.i18n.translator import SUPPORTED_LANGUAGES
from clinic.web.deps import LANGUAGE_COOKIE, get_lang

router = APIRouter(prefix="/language", tags=["language"])

# Cookie lifetime — 10 years is effectively forever for a clinic terminal.
_COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 10


@router.get("", response_class=HTMLResponse)
def show_picker(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "language_select.html",
        {"lang": get_lang(request)},
    )


@router.post("/{lang}")
def set_language(lang: str, request: Request) -> Response:
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}")

    settings_service.set_language(lang)
    settings_service.mark_first_run_done()

    # HTMX callers get a redirect via the HX-Redirect header; plain form posts
    # get a normal 303 redirect. Either way, the cookie is set.
    if request.headers.get("HX-Request") == "true":
        response: Response = Response(status_code=204)
        response.headers["HX-Redirect"] = "/"
    else:
        response = RedirectResponse(url="/", status_code=303)

    response.set_cookie(
        key=LANGUAGE_COOKIE,
        value=lang,
        max_age=_COOKIE_MAX_AGE,
        httponly=False,  # small partials read it via JS if needed
        samesite="lax",
    )
    return response
