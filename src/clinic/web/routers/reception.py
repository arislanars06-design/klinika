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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _form_context(
    request: Request,
    form: dict[str, Any] | None = None,
    form_errors: dict[str, str] | None = None,
    reception=None,
) -> dict[str, Any]:
    return {
        "form": form or {},
        "form_errors": form_errors or {},
        "reception": reception,
        "doctors": doctor_service.list_all(active_only=False),
        "complaints": catalog_loader.complaints_catalog(),
        "lor_catalog": catalog_loader.lor_status_catalog(),
        "address_catalog": catalog_loader.address_catalog(),
    }


def _compose_address(region_code: str, district_code: str, extra: str) -> str:
    """Build a human-readable free-text address from the cascade selection."""
    parts: list[str] = []
    if region_code or district_code:
        cat = catalog_loader.address_catalog()
        region = next((r for r in cat.get("regions", []) if r["code"] == region_code), None)
        if region:
            reg_name = region["name"].get("uz") or region["code"]
            parts.append(reg_name)
            if district_code:
                district = next(
                    (d for d in region.get("districts", []) if d["code"] == district_code),
                    None,
                )
                if district:
                    parts.append(district["name"].get("uz") or district["code"])
    if extra and extra.strip():
        parts.append(extra.strip())
    return ", ".join(parts)


def _parse_address(text: str | None) -> tuple[str, str, str]:
    """Best-effort split of a stored address string back into region/district/extra.

    We saved the address as ``"<region>, <district>, <extra>"``. If the first
    two segments match catalog entries we return their codes; otherwise the
    whole string flows into ``extra`` so the operator can still see it.
    """
    if not text:
        return "", "", ""
    cat = catalog_loader.address_catalog()
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return "", "", ""

    reg_name = parts[0]
    region = next(
        (r for r in cat.get("regions", [])
         if r["name"].get("uz") == reg_name or r["name"].get("ru") == reg_name),
        None,
    )
    if region is None:
        return "", "", text
    region_code = region["code"]

    if len(parts) < 2:
        return region_code, "", ""

    dist_name = parts[1]
    district = next(
        (d for d in region.get("districts", [])
         if d["name"].get("uz") == dist_name or d["name"].get("ru") == dist_name),
        None,
    )
    if district is None:
        return region_code, "", ", ".join(parts[1:])
    district_code = district["code"]
    extra = ", ".join(parts[2:]) if len(parts) > 2 else ""
    return region_code, district_code, extra


def _collect_lor_status(form_data, catalog: dict) -> dict:
    """Reconstruct the nested ``lor_status`` dict from the flat form.

    Field names look like:
        ``lor__<method>__<section>__<field_code>``       — plain method
        ``lor__<method>__<ear>__<section>__<field_code>``  — per-ear method

    Values may be radios (single string), checkbox_multi (list of strings), or
    plain checkboxes (``"1"`` when checked). Everything empty is skipped.
    """
    getlist = getattr(form_data, "getlist", None)

    result: dict[str, dict[str, dict[str, Any]]] = {}
    for method in catalog.get("methods", []):
        per_ear = method.get("per_ear", False)
        prefixes: list[str] = []
        if per_ear:
            for ear in method.get("ears", []):
                prefixes.append(f"{method['code']}__{ear['code']}")
        else:
            prefixes.append(method["code"])

        for prefix in prefixes:
            method_bucket: dict[str, dict[str, Any]] = {}
            for section in method.get("sections", []):
                section_code = section["code"]
                section_bucket: dict[str, Any] = {}
                for field in section.get("fields", []):
                    name = f"lor__{prefix}__{section_code}__{field['code']}"
                    ftype = field.get("type")
                    if ftype in {"radio", "side", "degree"}:
                        val = (form_data.get(name) or "").strip()
                        if val:
                            section_bucket[field["code"]] = val
                    elif ftype == "checkbox_multi":
                        if getlist:
                            values = [v for v in getlist(name) if v]
                        else:
                            raw = form_data.get(name)
                            values = [raw] if raw else []
                        if values:
                            section_bucket[field["code"]] = values
                    elif ftype == "checkbox":
                        if form_data.get(name):
                            section_bucket[field["code"]] = True
                if section_bucket:
                    method_bucket[section_code] = section_bucket
            if method_bucket:
                result[prefix] = method_bucket

    return result


def _parse_form(form_data, lor_catalog: dict) -> tuple[ReceptionInput, dict[str, Any]]:
    """Convert raw form data → (ReceptionInput, form_state_for_redisplay)."""
    complaints_codes = (
        form_data.getlist("complaints")
        if hasattr(form_data, "getlist")
        else form_data.get("complaints", [])
    )
    if isinstance(complaints_codes, str):
        complaints_codes = [complaints_codes]

    lor_status = _collect_lor_status(form_data, lor_catalog)

    raw_patient_id = (form_data.get("patient_id") or "").strip()
    patient_id = int(raw_patient_id) if raw_patient_id.isdigit() else None

    raw_doctor_id = (form_data.get("doctor_id") or "").strip()
    doctor_id: int | None = int(raw_doctor_id) if raw_doctor_id.isdigit() else None

    # Address: region + district selects + optional freetext extra.
    address_region = (form_data.get("address_region") or "").strip()
    address_district = (form_data.get("address_district") or "").strip()
    address_extra = (form_data.get("address") or "").strip()
    composed_address = _compose_address(address_region, address_district, address_extra)

    patient_input = PatientInput(
        full_name=(form_data.get("full_name") or "").strip(),
        birth_year=(form_data.get("birth_year") or "").strip(),
        address=composed_address or None,
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
        "address": address_extra,
        "address_region": address_region,
        "address_district": address_district,
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
def new_reception(
    request: Request,
    patient_id: int | None = None,
    _user: str = Depends(require_login),
):
    form: dict[str, Any] = {}
    if patient_id:
        p = patient_service.get(patient_id)
        if p:
            region_code, district_code, extra = _parse_address(p.address)
            form = {
                "patient_id": p.id,
                "full_name": p.full_name,
                "birth_year": p.birth_year,
                "address": extra,
                "address_region": region_code,
                "address_district": district_code,
                "phone": p.phone,
            }
    return render(request, "reception/form.html", _form_context(request, form=form))


@router.post("/new")
async def create_reception(request: Request, _user: str = Depends(require_login)):
    lor_catalog = catalog_loader.lor_status_catalog()
    form_data = await request.form()
    rec_input, form_state = _parse_form(form_data, lor_catalog)
    try:
        rec, _patient, _created = reception_service.save(rec_input)
    except ValidationError as ve:
        return render(
            request, "reception/form.html",
            _form_context(request, form=form_state, form_errors=ve.errors),
            status_code=400,
        )
    request.session.setdefault("flash", []).append({
        "level": "success",
        "text": "Qabul saqlandi." if resolve_language(request) == "uz" else "Приём сохранён.",
    })
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
def edit_reception_form(
    request: Request, reception_id: int, _user: str = Depends(require_login)
):
    rec = reception_service.get(reception_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="reception_not_found")
    patient = patient_service.get(rec.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="patient_not_found")
    region_code, district_code, extra = _parse_address(patient.address)
    form = {
        "patient_id": patient.id,
        "full_name": patient.full_name,
        "birth_year": patient.birth_year,
        "address": extra,
        "address_region": region_code,
        "address_district": district_code,
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
async def update_reception(
    request: Request, reception_id: int, _user: str = Depends(require_login)
):
    rec = reception_service.get(reception_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="reception_not_found")
    lor_catalog = catalog_loader.lor_status_catalog()
    form_data = await request.form()
    rec_input, form_state = _parse_form(form_data, lor_catalog)
    rec_input.patient_id = rec.patient_id
    try:
        reception_service.update(reception_id, rec_input)
    except ValidationError as ve:
        return render(
            request, "reception/form.html",
            _form_context(request, form=form_state, form_errors=ve.errors, reception=rec),
            status_code=400,
        )
    request.session.setdefault("flash", []).append({
        "level": "success",
        "text": "Qabul yangilandi." if resolve_language(request) == "uz" else "Приём обновлён.",
    })
    return RedirectResponse(url=f"/reception/{reception_id}", status_code=303)
