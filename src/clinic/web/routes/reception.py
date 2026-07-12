"""Reception (Qabul) — the busiest form in the app.

- ``GET  /reception``               — new form with today's date pre-filled
- ``GET  /reception/{id}``          — edit an existing reception
- ``POST /reception``               — save (new) and redirect
- ``POST /reception/{id}``          — save (update) and redirect
- ``GET  /reception/search-patient``— HTMX autocomplete partial
- ``GET  /reception/{id}/print``    — download docx paper
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from loguru import logger
from sqlalchemy.orm import Session

from clinic.domain import (
    catalog_loader,
    doctor_service,
    patient_service,
    reception_service,
    service_catalog_service,
)
from clinic.printing import docx_builder
from clinic.web.deps import DbDep, get_lang

router = APIRouter(prefix="/reception", tags=["reception"])


# ----- form rendering --------------------------------------------------------


def _form_context(
    request: Request,
    session: Session,
    *,
    reception=None,
    errors: list[str] | None = None,
    prefill: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble everything the reception form needs to render."""
    lang = get_lang(request)
    return {
        "lang": lang,
        "reception": reception,
        "prefill": prefill or {},
        "errors": errors or [],
        "today": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "doctors": doctor_service.list_active(session),
        "services": service_catalog_service.list_active(session),
        "complaints": catalog_loader.complaints_catalog(),
        "discharge_types": catalog_loader.discharge_types_catalog(),
        "lor_status": catalog_loader.lor_status_catalog(),
        "current_year": datetime.now().year,
    }


@router.get("", response_class=HTMLResponse)
def new_form(request: Request, session: Session = DbDep) -> HTMLResponse:
    templates = request.app.state.templates
    ctx = _form_context(request, session)
    return templates.TemplateResponse(request, "reception/form.html", ctx)


# ----- HTMX partials (must come before /{reception_id}) ---------------------


@router.get("/search-patient", response_class=HTMLResponse)
def search_patient(
    request: Request,
    q: str = "",
    session: Session = DbDep,
) -> HTMLResponse:
    """Return a dropdown of matching patients as an HTMX fragment."""
    templates = request.app.state.templates
    matches = patient_service.search(session, q, limit=8) if len(q.strip()) >= 2 else []
    return templates.TemplateResponse(
        request,
        "reception/_patient_suggestions.html",
        {"lang": get_lang(request), "matches": matches, "q": q},
    )


@router.get("/{reception_id}", response_class=HTMLResponse)
def edit_form(
    reception_id: int, request: Request, session: Session = DbDep
) -> HTMLResponse:
    reception = reception_service.get(session, reception_id)
    if reception is None:
        raise HTTPException(404)
    templates = request.app.state.templates
    ctx = _form_context(request, session, reception=reception)
    return templates.TemplateResponse(request, "reception/form.html", ctx)


# ----- save ------------------------------------------------------------------


def _form_to_dict(form: Any) -> dict[str, Any]:
    """Convert FormData into a plain dict that Jinja can iterate.

    Multi-value fields (checkbox groups) become lists so the template can look
    up ``prefill['complaints_codes']`` reliably.
    """
    out: dict[str, Any] = {}
    for key in form.keys():
        values = form.getlist(key)
        out[key] = values if len(values) > 1 else values[0]
    return out


def _parse_form(form: dict[str, Any]) -> reception_service.ReceptionInput:
    """Translate a raw form dict into a validated ``ReceptionInput``."""
    codes = [c for c in form.getlist("complaints_codes") if c]
    details: dict[str, str] = {}
    for code in codes:
        detail = form.get(f"discharge__{code}")
        if detail:
            details[code] = detail

    patient = patient_service.PatientInput(
        full_name=(form.get("patient_full_name") or "").strip(),
        birth_year=int(form.get("patient_birth_year") or 0),
        address=(form.get("patient_address") or "").strip() or None,
        phone=(form.get("patient_phone") or "").strip() or None,
    )

    date_str = form.get("reception_date") or ""
    try:
        reception_date = datetime.fromisoformat(date_str)
    except ValueError:
        reception_date = datetime.now()

    lor_text = (form.get("lor_status_text") or "").strip()
    lor_status = {"text": lor_text} if lor_text else None

    return reception_service.ReceptionInput(
        patient=patient,
        doctor_id=int(form.get("doctor_id") or 0),
        reception_date=reception_date,
        diagnosis=(form.get("diagnosis") or "").strip(),
        complaints_codes=codes,
        complaints_details=details,
        complaints_note=(form.get("complaints_note") or "").strip() or None,
        anamnesis=(form.get("anamnesis") or "").strip() or None,
        lor_status=lor_status,
        recommendation=(form.get("recommendation") or "").strip() or None,
    )


@router.post("", response_class=HTMLResponse)
async def create(request: Request, session: Session = DbDep) -> Response:
    form = await request.form()
    try:
        data = _parse_form(form)
        reception = reception_service.create(session, data)
        session.commit()
    except reception_service.ReceptionValidationError as e:
        session.rollback()
        templates = request.app.state.templates
        ctx = _form_context(request, session, errors=e.args[0], prefill=_form_to_dict(form))
        return templates.TemplateResponse(request, "reception/form.html", ctx, status_code=422)

    logger.info("Created reception {} for patient {}", reception.id, reception.patient_id)
    next_url = form.get("_next") or "/"
    if next_url == "cashier":
        return RedirectResponse(f"/cashier?reception_id={reception.id}", status_code=303)
    return RedirectResponse(f"/patients/{reception.patient_id}?flash=saved", status_code=303)


@router.post("/{reception_id}", response_class=HTMLResponse)
async def update(reception_id: int, request: Request, session: Session = DbDep) -> Response:
    form = await request.form()
    try:
        data = _parse_form(form)
        reception_service.update(session, reception_id, data)
        session.commit()
    except reception_service.ReceptionValidationError as e:
        session.rollback()
        templates = request.app.state.templates
        reception = reception_service.get(session, reception_id)
        ctx = _form_context(request, session, reception=reception, errors=e.args[0], prefill=_form_to_dict(form))
        return templates.TemplateResponse(request, "reception/form.html", ctx, status_code=422)

    reception = reception_service.get(session, reception_id)
    return RedirectResponse(f"/patients/{reception.patient_id}?flash=saved", status_code=303)


# ----- print -----------------------------------------------------------------


@router.get("/{reception_id}/print")
def print_paper(reception_id: int, request: Request, session: Session = DbDep) -> Response:
    reception = reception_service.get(session, reception_id)
    if reception is None:
        raise HTTPException(404)
    lang = get_lang(request)
    payload = docx_builder.build_reception_docx(reception, lang)
    filename = f"qabul_{reception.id}_{reception.reception_date:%Y%m%d}.docx"
    return Response(
        content=payload,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
