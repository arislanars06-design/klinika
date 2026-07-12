"""Settings hub: clinic info, doctors, and services CRUD."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from clinic.domain import doctor_service, service_catalog_service, settings_service
from clinic.web.deps import DbDep, get_lang

router = APIRouter(prefix="/settings", tags=["settings"])


# ----- overview -------------------------------------------------------------


@router.get("", response_class=HTMLResponse)
def index(request: Request, session: Session = DbDep) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(
        request,
        "settings/index.html",
        {
            "lang": get_lang(request),
            "clinic_name_uz": settings_service.get("clinic_name_uz") or "",
            "clinic_name_ru": settings_service.get("clinic_name_ru") or "",
            "clinic_address_uz": settings_service.get("clinic_address_uz") or "",
            "clinic_address_ru": settings_service.get("clinic_address_ru") or "",
            "clinic_phone": settings_service.get("clinic_phone") or "",
            "doctors": doctor_service.list_all(session),
            "services": service_catalog_service.list_all(session),
            "flash": request.query_params.get("flash"),
        },
    )


# ----- clinic info ---------------------------------------------------------


@router.post("/clinic")
async def save_clinic(request: Request) -> Response:
    form = await request.form()
    for key in (
        "clinic_name_uz",
        "clinic_name_ru",
        "clinic_address_uz",
        "clinic_address_ru",
        "clinic_phone",
    ):
        value = (form.get(key) or "").strip()
        settings_service.set_value(key, value)
    return RedirectResponse("/settings?flash=clinic_saved", status_code=303)


# ----- doctors --------------------------------------------------------------


@router.post("/doctors")
async def add_doctor(request: Request, session: Session = DbDep) -> Response:
    form = await request.form()
    name = (form.get("full_name") or "").strip()
    if not name:
        return RedirectResponse("/settings?flash=doctor_name_required", status_code=303)
    doctor_service.create(
        session,
        doctor_service.DoctorInput(full_name=name, phone=(form.get("phone") or "").strip() or None),
    )
    session.commit()
    return RedirectResponse("/settings?flash=doctor_added", status_code=303)


@router.post("/doctors/{doctor_id}/toggle")
def toggle_doctor(doctor_id: int, session: Session = DbDep) -> Response:
    doctor = doctor_service.get(session, doctor_id)
    if doctor:
        doctor_service.set_active(session, doctor_id, not doctor.is_active)
        session.commit()
    return RedirectResponse("/settings?flash=doctor_toggled", status_code=303)


# ----- services -------------------------------------------------------------


@router.post("/services")
async def add_service(request: Request, session: Session = DbDep) -> Response:
    form = await request.form()
    name_uz = (form.get("name_uz") or "").strip()
    name_ru = (form.get("name_ru") or "").strip() or name_uz
    try:
        price = Decimal((form.get("price") or "0").replace(" ", "").replace(",", "."))
    except InvalidOperation:
        price = Decimal(0)
    if not name_uz or price <= 0:
        return RedirectResponse("/settings?flash=service_invalid", status_code=303)
    service_catalog_service.create(
        session,
        service_catalog_service.ServiceInput(name_uz=name_uz, name_ru=name_ru, price=price),
    )
    session.commit()
    return RedirectResponse("/settings?flash=service_added", status_code=303)


@router.post("/services/{service_id}/toggle")
def toggle_service(service_id: int, session: Session = DbDep) -> Response:
    service = service_catalog_service.get(session, service_id)
    if service:
        service_catalog_service.set_active(session, service_id, not service.is_active)
        session.commit()
    return RedirectResponse("/settings?flash=service_toggled", status_code=303)
