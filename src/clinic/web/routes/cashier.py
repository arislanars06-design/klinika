"""Cashier routes (placeholder until Milestone 3)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from clinic.web.deps import get_lang

router = APIRouter(prefix="/cashier", tags=["cashier"])


@router.get("", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "placeholder.html",
        {
            "lang": get_lang(request),
            "title_key": "menu.cashier",
            "milestone": "M3",
        },
    )
