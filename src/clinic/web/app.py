"""FastAPI application factory.

Wires up templates, static files, middleware, and the route modules.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from clinic.db.database import init_db
from clinic.i18n.translator import SUPPORTED_LANGUAGES, translator
from clinic.web.deps import LANGUAGE_COOKIE, get_lang
from clinic.web.routes import cashier, home, language, patients, reception, settings as settings_route

WEB_DIR: Path = Path(__file__).resolve().parent
TEMPLATES_DIR: Path = WEB_DIR / "templates"
STATIC_DIR: Path = WEB_DIR / "static"


def _configure_templates() -> Jinja2Templates:
    """Build a Jinja2 environment aware of our translator and lang cookie."""
    import json as _json
    from decimal import Decimal

    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    def _t(key: str, lang: str = "uz", **fmt: object) -> str:
        return translator.t(key, lang, **fmt)

    def _tojson(value: object) -> str:
        """Serialize ORM rows / Decimals to JSON for Alpine.js x-data."""

        def default(obj: object) -> object:
            if isinstance(obj, Decimal):
                return str(obj)
            if hasattr(obj, "__table__"):
                cols = [c.name for c in obj.__table__.columns]
                return {c: getattr(obj, c) for c in cols}
            return str(obj)

        return _json.dumps(value, default=default, ensure_ascii=False)

    templates.env.globals["supported_languages"] = SUPPORTED_LANGUAGES
    templates.env.globals["language_cookie"] = LANGUAGE_COOKIE
    templates.env.filters["t"] = _t  # {{ 'menu.start_reception' | t(lang) }}
    templates.env.filters["tojson"] = _tojson
    return templates


def create_app() -> FastAPI:
    init_db()

    app = FastAPI(
        title="Klinika LOR",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )

    templates = _configure_templates()
    app.state.templates = templates
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # ----- routes -----
    app.include_router(home.router)
    app.include_router(language.router)
    app.include_router(reception.router)
    app.include_router(patients.router)
    app.include_router(cashier.router)
    app.include_router(settings_route.router)

    # ----- health check -----
    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    # ----- catch-all 404 renders a friendly page -----
    @app.exception_handler(404)
    async def not_found(request: Request, exc: object) -> HTMLResponse:  # noqa: ARG001
        lang = get_lang(request)
        return templates.TemplateResponse(
            request,
            "errors/404.html",
            {"lang": lang},
            status_code=404,
        )

    logger.info("FastAPI app created with {} route modules", 6)
    return app
