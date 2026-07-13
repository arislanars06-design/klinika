"""Sign-in / sign-out / language switch."""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from clinic.i18n.translator import SUPPORTED_LANGUAGES, translator
from clinic.web.auth import try_login
from clinic.web.dependencies import render

router = APIRouter()


def _safe_next(next_url: str | None) -> str:
    """Constrain ``next`` to same-origin absolute paths."""
    if not next_url or not next_url.startswith("/") or next_url.startswith("//"):
        return "/"
    return next_url


@router.get("/login")
def login_page(request: Request, next: str | None = None, error: str | None = None):
    if request.session.get("user"):
        return RedirectResponse(url=_safe_next(next), status_code=303)
    return render(
        request,
        "login.html",
        {"next_url": _safe_next(next), "error": error},
    )


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(""),
    password: str = Form(...),
    next: str = Form("/"),
):
    outcome = try_login(username, password)
    if outcome.user is None:
        return render(
            request,
            "login.html",
            {
                "next_url": _safe_next(next),
                "error": translator.t(outcome.reason or "auth.wrong_password"),
                "prefilled_username": username,
            },
            status_code=401,
        )
    request.session["user"] = outcome.user.username
    request.session["role"] = outcome.user.role
    request.session["full_name"] = outcome.user.full_name
    return RedirectResponse(url=_safe_next(next), status_code=303)


@router.get("/logout")
def logout(request: Request):
    for key in ("user", "role", "full_name"):
        request.session.pop(key, None)
    return RedirectResponse(url="/login", status_code=303)


@router.get("/lang/{code}")
def switch_language(request: Request, code: str, next: str | None = None):
    if code in SUPPORTED_LANGUAGES:
        request.session["lang"] = code
        translator.set_language(code)
    return RedirectResponse(url=_safe_next(next), status_code=303)
