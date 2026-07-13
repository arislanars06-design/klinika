"""FastAPI application factory.

Wires the session middleware, static files, routers, and 401→login-redirect
handler. Callers use :func:`create_app` — the singleton lives in
:mod:`clinic.web.main` for uvicorn.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.sessions import SessionMiddleware

from clinic.db.database import init_db
from clinic.web.config import web_settings
from clinic.web.dependencies import STATIC_DIR


@asynccontextmanager
async def _lifespan(app: FastAPI):
    init_db()
    logger.info("Clinic web app started (host={} port={})", web_settings.host, web_settings.port)
    yield


def create_app() -> FastAPI:
    """Return a configured FastAPI application."""
    app = FastAPI(
        title="Clinic LOR — web",
        description="Bilingual (uz/ru) web front-end for the LOR clinic system.",
        version="0.1.0",
        docs_url=None,      # Hide OpenAPI docs from clinic staff
        redoc_url=None,
        lifespan=_lifespan,
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=web_settings.secret,
        session_cookie=web_settings.session_cookie_name,
        max_age=web_settings.session_max_age,
        same_site="lax",
        https_only=False,   # LAN deployments won't have TLS
    )

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # ---- routers ----
    from clinic.web.routers import (
        auth as auth_router,
    )
    from clinic.web.routers import (
        cashier as cashier_router,
    )
    from clinic.web.routers import (
        home as home_router,
    )
    from clinic.web.routers import (
        patients as patients_router,
    )
    from clinic.web.routers import (
        print as print_router,
    )
    from clinic.web.routers import (
        reception as reception_router,
    )
    from clinic.web.routers import (
        stats as stats_router,
    )

    app.include_router(auth_router.router)
    app.include_router(home_router.router)
    app.include_router(reception_router.router)
    app.include_router(patients_router.router)
    app.include_router(cashier_router.router)
    app.include_router(stats_router.router)
    app.include_router(print_router.router)

    # ---- exception handlers ----
    from fastapi.exception_handlers import http_exception_handler as _default_http_handler

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(request: Request, exc: HTTPException):
        # Turn 401 into a redirect to the login page (preserves ``next`` target).
        if exc.status_code == 401:
            next_url = request.url.path
            if request.url.query:
                next_url = f"{next_url}?{request.url.query}"
            return RedirectResponse(url=f"/login?next={next_url}", status_code=303)
        # Delegate everything else to FastAPI's default renderer.
        return await _default_http_handler(request, exc)

    return app
