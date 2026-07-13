"""Reception (visit) create / edit / view."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from clinic.domain import (
    catalog_loader,
    doctor_service,
    patient_service,
    reception_service,
)
from clinic.domain.dto import PatientInput, ReceptionInput
from clinic.infrastructure.validators import ValidationError
from clinic.printing.text_composer import compose_complaints, compose_lor_status
from clinic.web.dependencies import render, require_login, resolve_language

router = APIRouter(prefix="/reception")

# LOR methods exposed as a fixed list (matches the freetext editor in Phase 1)
LOR_METHODS = [
    {"code": "rhinoscopy",    "icon": "\U0001F443", "name": {"uz": "Rinoskopiya",    "ru": "Риноскопия"}},
    {"code": "pharyngoscopy", "icon": "\U0001F62E", "name": {"uz": "Faringoskopiya", "ru": "Фарингоскопия"}},
    {"code": "otoscopy",      "icon": "\U0001F442", "name": {"uz": "Otoskopiya",     "ru": "Отоскопия"}},
    {"code": "laryngoscopy",  "icon": "\U0001F5E3", "name": {"uz": "Laringoskopiya", "ru": "Ларингоскопия"}},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _form_context(request: Request, form: dict[str, Any] | None = None,
                  form_errors: dict[str, str] | None = None,
                  reception=None) -> dict[str, Any]:
    return {
        "form": form or {},
        "form_errors": form_errors or {},
        "reception": reception,
        "doctors": doctor_service.list_all(active_only=False),
        "complaints": catalog_loader.complaints_catalog(),
        "lor_methods": LOR_METHODS,
    }


def _parse_form(form_data) -> tuple[ReceptionInput, dict[str, Any]]:
    """Convert raw form data → (ReceptionInput, form_state_for_redisplay)."""
    complaints_codes = form_data.getlist("complaints") if hasattr(form_data, "getlist") else form_data.get("complaints", [])
    if isinstance(complaints_codes, str):
        complaints_codes = [complaints_codes]

    lor_status: dict[str, str] = {}
    for method in LOR_METHODS:
        val = (form_data.get(f"lor_{method['code']}") or "").strip()
        if val:
            lor_status[method["code"]] = val

    raw_patient_id = (form_data.get("patient_id") or "").strip()
    patient_id = int(raw_patient_id) if raw_patient_id.isdigit() else None

    raw_doctor_id = (form_data.get("doctor_id") or "").strip()
    doctor_id: int | None = int(raw_doctor_id) if raw_doctor_id.isdigit() else None

    patient_input = PatientInput(
        full_name=(form_data.get("full_name") or "").strip(),
        birth_year=(form_data.get("birth_year") or "").strip(),
        address=(form_data.get("address") or "").strip() or None,
        phone=(form_data.get("phone") or "").strip() or None,
    )
    rec_input = ReceptionInput(
        patient=patient_input,
        patient_id=patient_id,
        doctor_id=doctor_id,
        reception_date=datetime.utcnow(),
        complaints_codes=list(complaints_codes),
        complaints_details={},
        complaints_note=(form_data.get("complaints_note") or "").strip() or None,
        anamnesis=(form_data.get("anamnesis") or "").strip() or None,
        lor_status=lor_status or None,
        diagnosis=(form_data.get("diagnosis") or "").strip(),
        recommendation=(form_data.get("recommendation") or "").strip() or None,
    )
    form_state = {
        "patient_id": patient_id,
        "full_name": patient_input.full_name,
        "birth_year": patient_input.birth_year,
        "address": patient_input.address,
        "phone": patient_input.phone,
        "complaints_codes": list(complaints_codes),
        "complaints_note": rec_input.complaints_note,
        "anamnesis": rec_input.anamnesis,
        "lor_status": lor_status,
        "diagnosis": rec_input.diagnosis,
        "recommendation": rec_input.recommendation,
        "doctor_id": doctor_id,
    }
    return rec_input, form_state


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/new")
def new_reception(request: Request, patient_id: int | None = None,
                  _user: str = Depends(require_login)):
    form: dict[str, Any] = {}
    if patient_id:
        p = patient_service.get(patient_id)
        if p:
            form = {
                "patient_id": p.id,
                "full_name": p.full_name,
                "birth_year": p.birth_year,
                "address": p.address,
                "phone": p.phone,
            }
    return render(request, "reception/form.html", _form_context(request, form=form))


@router.post("/new")
async def create_reception(request: Request, _user: str = Depends(require_login)):
    form_data = await request.form()
    rec_input, form_state = _parse_form(form_data)
    try:
        rec, _patient, _created = reception_service.save(rec_input)
    except ValidationError as ve:
        return render(
            request, "reception/form.html",
            _form_context(request, form=form_state, form_errors=ve.errors),
            status_code=400,
        )
    request.session.setdefault("flash", []).append(
        {"level": "success", "text": "Qabul saqlandi." if resolve_language(request) == "uz" else "Приём сохранён."}
    )
    return RedirectResponse(url=f"/reception/{rec.id}", status_code=303)


@router.get("/{reception_id}")
def view_reception(request: Request, reception_id: int, _user: str = Depends(require_login)):
    rec = reception_service.get(reception_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="reception_not_found")
    patient = patient_service.get(rec.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="patient_not_found")
    doctor = doctor_service.get(rec.doctor_id)
    lang = resolve_language(request)
    return render(request, "reception/detail.html", {
        "reception": rec,
        "patient": patient,
        "doctor": doctor,
        "complaints_text": compose_complaints(
            rec.complaints_codes, rec.complaints_details, rec.complaints_note, lang=lang
        ),
        "lor_status_text": compose_lor_status(rec.lor_status, lang=lang),
    })


@router.get("/{reception_id}/edit")
def edit_reception_form(request: Request, reception_id: int, _user: str = Depends(require_login)):
    rec = reception_service.get(reception_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="reception_not_found")
    patient = patient_service.get(rec.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="patient_not_found")
    form = {
        "patient_id": patient.id,
        "full_name": patient.full_name,
        "birth_year": patient.birth_year,
        "address": patient.address,
        "phone": patient.phone,
        "complaints_codes": rec.complaints_codes,
        "complaints_note": rec.complaints_note,
        "anamnesis": rec.anamnesis,
        "lor_status": rec.lor_status or {},
        "diagnosis": rec.diagnosis,
        "recommendation": rec.recommendation,
        "doctor_id": rec.doctor_id,
    }
    return render(request, "reception/form.html", _form_context(request, form=form, reception=rec))


@router.post("/{reception_id}/edit")
async def update_reception(request: Request, reception_id: int, _user: str = Depends(require_login)):
    rec = reception_service.get(reception_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="reception_not_found")
    form_data = await request.form()
    rec_input, form_state = _parse_form(form_data)
    rec_input.patient_id = rec.patient_id
    try:
        reception_service.update(reception_id, rec_input)
    except ValidationError as ve:
        return render(
            request, "reception/form.html",
            _form_context(request, form=form_state, form_errors=ve.errors, reception=rec),
            status_code=400,
        )
    request.session.setdefault("flash", []).append(
        {"level": "success", "text": "Qabul yangilandi." if resolve_language(request) == "uz" else "Приём обновлён."}
    )
    return RedirectResponse(url=f"/reception/{reception_id}", status_code=303)
