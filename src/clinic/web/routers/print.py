"""Reception → Word download endpoint."""

from __future__ import annotations

import io

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from clinic.domain import clinic_info_service, doctor_service, patient_service, reception_service
from clinic.printing.docx_builder import build_reception_document
from clinic.web.dependencies import require_login, resolve_language

router = APIRouter(prefix="/print")


@router.get("/reception/{reception_id}.docx")
def print_reception(request: Request, reception_id: int, _user: str = Depends(require_login)):
    rec = reception_service.get(reception_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="reception_not_found")
    patient = patient_service.get(rec.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="patient_not_found")
    doctor = doctor_service.get(rec.doctor_id)

    clinic = clinic_info_service.load()
    lang = resolve_language(request)

    doc = build_reception_document(
        reception=rec,
        patient=patient,
        doctor=doctor,
        clinic={
            "name_uz": clinic.name_uz,
            "name_ru": clinic.name_ru,
            "address_uz": clinic.address_uz,
            "address_ru": clinic.address_ru,
            "phone": clinic.phone,
            "logo_path": clinic.logo_path,
        },
        lang=lang,
    )

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)

    filename = f"reception_{reception_id}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
