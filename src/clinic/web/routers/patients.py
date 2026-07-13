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
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    _user: str = Depends(require_login),
):
    from datetime import date, datetime, time

    from sqlalchemy import func

    from clinic.db.database import session_scope
    from clinic.db.models import Patient
    from clinic.domain import stats_service

    mode = _SEARCH_MODES.get(search_in, ANY_FIELD_SEARCH)

    # ---- Parse optional date range ---------------------------------------
    df: datetime | None = None
    dt: datetime | None = None
    try:
        if date_from:
            df = datetime.combine(date.fromisoformat(date_from), time.min)
        if date_to:
            dt = datetime.combine(date.fromisoformat(date_to), time.max)
    except ValueError:
        df = dt = None  # ignore bad input, don't 500

    page_data = patient_service.paginated_search(
        text=q or None,
        search_in=mode,
        date_from=df,
        date_to=dt,
        page=max(1, page),
    )

    # ---- Stats block: total + new + repeat -------------------------------
    # When a date range is supplied, the second/third KPIs describe that
    # window instead of the current month.
    if df is not None or dt is not None:
        period = stats_service.build_custom(
            (df or datetime.min).date(),
            (dt or datetime.max).date(),
        )
        period_label = "range"
    else:
        period = stats_service.build_period(stats_service.PeriodPreset.MONTH)
        period_label = "month"
    period_stats = stats_service.patient_stats(period)
    with session_scope() as session:
        total_patients = int(session.query(func.count(Patient.id)).scalar() or 0)

    patient_stats = {
        "total": total_patients,
        "new_in_period": period_stats.new_patients,
        "repeat_in_period": period_stats.repeat_receptions,
        "period_label": period_label,
    }

    return render(request, "patients/list.html", {
        "page": page_data,
        "q": q,
        "search_in": search_in if search_in in _SEARCH_MODES else "any",
        "date_from": date_from or "",
        "date_to": date_to or "",
        "patient_stats": patient_stats,
    })


@router.post("/{patient_id}/delete")
def delete_patient(
    request: Request,
    patient_id: int,
    _user: str = Depends(require_login),
):
    """Delete a patient with all cascaded records (receptions + payments)."""
    from fastapi.responses import RedirectResponse

    from clinic.i18n.translator import translator

    ok = patient_service.delete(patient_id)
    request.session.setdefault("flash", []).append({
        "level": "success" if ok else "warning",
        "text": (
            translator.t("patients.deleted") if ok
            else translator.t("common.not_found")
        ),
    })
    # Return to the referring list URL if possible.
    referer = request.headers.get("referer", "/patients")
    if not referer.startswith("/"):
        # Same-origin only.
        from urllib.parse import urlparse

        parsed = urlparse(referer)
        referer = parsed.path + (f"?{parsed.query}" if parsed.query else "") or "/patients"
    return RedirectResponse(url=referer, status_code=303)


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
