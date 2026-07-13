"""Patient list, detail, autocomplete."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from clinic.db.repository import ANY_FIELD_SEARCH, PatientSearchField
from clinic.domain import patient_service
from clinic.web.dependencies import render, require_login

router = APIRouter(prefix="/patients")


VALID_SEARCH_FIELDS: tuple[PatientSearchField, ...] = (
    "any", "full_name", "phone", "address", "diagnosis",
)


@router.get("")
def list_patients(
    request: Request,
    q: str | None = None,
    search_in: str = "any",
    page: int = 1,
    _user: str = Depends(require_login),
):
    if search_in not in VALID_SEARCH_FIELDS:
        search_in = ANY_FIELD_SEARCH
    page_data = patient_service.paginated_search(
        text=q or None,
        search_in=search_in,
        page=max(1, page),
    )
    return render(request, "patients/list.html", {
        "page": page_data,
        "q": q,
        "search_in": search_in,
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
