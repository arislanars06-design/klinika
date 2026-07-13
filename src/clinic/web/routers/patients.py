"""Patient list, detail, autocomplete."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from clinic.db.repository import ANY_FIELD_SEARCH, PatientSearchField
from clinic.domain import patient_service
from clinic.web.dependencies import render, require_login

router = APIRouter(prefix="/patients")


# UI ↔ backend mapping. ``any`` collapses to the catch-all SearchField.
_SEARCH_MODES: dict[str, PatientSearchField] = {
    "any":        ANY_FIELD_SEARCH,
    "full_name":  PatientSearchField(full_name=True),
    "phone":      PatientSearchField(phone=True),
    "diagnosis":  PatientSearchField(diagnosis=True),
    "medication": PatientSearchField(medication=True),
}


@router.get("")
def list_patients(
    request: Request,
    q: str | None = None,
    search_in: str = "any",
    page: int = 1,
    _user: str = Depends(require_login),
):
    from sqlalchemy import func

    from clinic.db.database import session_scope
    from clinic.db.models import Patient
    from clinic.domain import stats_service

    mode = _SEARCH_MODES.get(search_in, ANY_FIELD_SEARCH)
    page_data = patient_service.paginated_search(
        text=q or None,
        search_in=mode,
        page=max(1, page),
    )

    month_period = stats_service.build_period(stats_service.PeriodPreset.MONTH)
    monthly = stats_service.patient_stats(month_period)
    with session_scope() as session:
        total_patients = int(session.query(func.count(Patient.id)).scalar() or 0)

    patient_stats = {
        "total": total_patients,
        "new_this_month": monthly.new_patients,
        "repeat_receptions": monthly.repeat_receptions,
    }

    return render(request, "patients/list.html", {
        "page": page_data,
        "q": q,
        "search_in": search_in if search_in in _SEARCH_MODES else "any",
        "patient_stats": patient_stats,
    })


@router.get("/autocomplete", response_class=None)
def autocomplete_patients(request: Request, q: str = "", _user: str = Depends(require_login)):
    """Return ``<option>`` tags for a ``<datalist>``. HTMX-friendly."""
    if not q or len(q.strip()) < 2:
        return _html_options([])
    matches = patient_service.search(q, limit=8)
    return _html_options(
        [(p.id, f"{p.full_name} ({p.birth_year})") for p in matches]
    )


def _html_options(items: list[tuple[int, str]]):
    from fastapi.responses import HTMLResponse
    body = "".join(f'<option value="{label}" data-id="{pid}"></option>' for pid, label in items)
    return HTMLResponse(body)


@router.get("/{patient_id}")
def patient_detail(request: Request, patient_id: int, _user: str = Depends(require_login)):
    detail = patient_service.get_detail(patient_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="patient_not_found")
    return render(request, "patients/detail.html", {
        "patient": detail.patient,
        "receptions": detail.receptions,
        "payments": detail.payments,
        "doctor_names": detail.doctor_names,
    })
