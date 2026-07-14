"""Cashier flow: pick patient → cart of services → save → view/print receipt."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from clinic.domain import (
    cashier_service,
    doctor_service,
    patient_service,
    reception_service,
    service_service,
)
from clinic.domain.dto import (
    CashierItemInput,
    CashierPaymentInput,
    CashierRecordDTO,
)
from clinic.infrastructure.validators import ValidationError
from clinic.web.dependencies import render, require_login, resolve_language

router = APIRouter(prefix="/cashier")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _group_receipts(records: list[CashierRecordDTO]) -> list[dict]:
    """Bundle line-items into receipts.

    All records that share ``patient_id + reception_id`` and whose ``paid_at``
    falls within a 60-second window belong to the same receipt (this matches
    the desktop app's grouping heuristic — every save writes ``utcnow()`` in
    a single transaction).
    """
    records = sorted(records, key=lambda r: r.paid_at, reverse=True)
    receipts: list[dict] = []
    for r in records:
        bucket = None
        for existing in receipts:
            first = existing["items"][0]
            same_patient = first.patient_id == r.patient_id
            same_reception = first.reception_id == r.reception_id
            delta = abs((first.paid_at - r.paid_at).total_seconds())
            if same_patient and same_reception and delta < 60:
                bucket = existing
                break
        if bucket is None:
            bucket = {
                "first_id": r.id,
                "paid_at": r.paid_at,
                "reception_id": r.reception_id,
                "items": [],
                "total": Decimal("0"),
            }
            receipts.append(bucket)
        bucket["items"].append(r)
        bucket["total"] += r.total
    return receipts


def _find_receipt_for(record_id: int) -> tuple[CashierRecordDTO, list[CashierRecordDTO]] | None:
    """Given one record_id, load all records of the same receipt."""
    from clinic.db.database import session_scope
    from clinic.db.repository import CashierRepository

    with session_scope() as session:
        row = CashierRepository(session).get(record_id)
        if row is None:
            return None
        anchor = CashierRecordDTO.from_orm(row)

    all_for_patient = cashier_service.list_for_patient(anchor.patient_id)
    same = [
        r for r in all_for_patient
        if r.reception_id == anchor.reception_id
        and abs((r.paid_at - anchor.paid_at).total_seconds()) < 60
    ]
    return anchor, sorted(same, key=lambda r: r.id)


# ---------------------------------------------------------------------------
# Landing page: patient picker + revenue KPI
# ---------------------------------------------------------------------------


@router.get("")
def cashier_landing(request: Request, q: str | None = None, _user: str = Depends(require_login)):
    from sqlalchemy import func

    from clinic.db.database import session_scope
    from clinic.db.models import CashierRecord
    from clinic.domain import stats_service

    period = stats_service.build_period(stats_service.PeriodPreset.TODAY)
    stats = stats_service.cashier_stats(period)

    # Per-payment-type breakdown for today.
    with session_scope() as session:
        rows = (
            session.query(CashierRecord.payment_type, func.coalesce(func.sum(CashierRecord.total), 0))
            .filter(CashierRecord.paid_at >= period.start)
            .filter(CashierRecord.paid_at <= period.end)
            .group_by(CashierRecord.payment_type)
            .all()
        )
    by_type = {pt: Decimal(0) for pt in ("cash", "transfer", "terminal")}
    for pt, total in rows:
        by_type[pt or "cash"] = Decimal(total or 0)

    # All-time totals — no date filter, one row per payment_type + grand total.
    with session_scope() as session:
        all_rows_ptype = (
            session.query(
                CashierRecord.payment_type,
                func.coalesce(func.sum(CashierRecord.total), 0),
            )
            .group_by(CashierRecord.payment_type)
            .all()
        )
    all_time_by_type = {pt: Decimal(0) for pt in ("cash", "transfer", "terminal")}
    for pt, total in all_rows_ptype:
        all_time_by_type[pt or "cash"] = Decimal(total or 0)
    all_time_total = sum(all_time_by_type.values(), Decimal(0))

    # Today's payers list — one entry per receipt (grouped by paid_at bucket).
    today_history = [
        r for r in cashier_service.list_for_period(period.start, period.end)
    ] if hasattr(cashier_service, "list_for_period") else []
    if not today_history:
        # Fall back — walk each recent patient's payments.
        with session_scope() as session:
            record_ids = [
                r_id for (r_id,) in session.query(CashierRecord.id)
                .filter(CashierRecord.paid_at >= period.start)
                .filter(CashierRecord.paid_at <= period.end)
                .all()
            ]
        today_records: list[CashierRecordDTO] = []
        seen_patients: set[int] = set()
        # Cheap path: rebuild via list_for_patient (already indexed) but keep it
        # capped so a huge day doesn't blow up the landing page.
        limit = 60
        with session_scope() as session:
            for rid in record_ids:
                if len(today_records) >= limit:
                    break
                row = session.get(CashierRecord, rid)
                if row is None:
                    continue
                if row.patient_id in seen_patients:
                    continue
                seen_patients.add(row.patient_id)
                for r in cashier_service.list_for_patient(row.patient_id):
                    if period.start <= r.paid_at <= period.end:
                        today_records.append(r)
        today_history = today_records

    today_receipts = _group_receipts(today_history)[:20]

    # Load patient names in bulk so the template stays chatter-free.
    patient_names: dict[int, str] = {}
    for rc in today_receipts:
        pid = rc["items"][0].patient_id
        if pid not in patient_names:
            p = patient_service.get(pid)
            if p:
                patient_names[pid] = p.full_name

    # ---- Accumulating "all cashier patients" list ----
    # Every patient who ever had a payment, newest first. This is the
    # rolling ledger the operator sees at the bottom of the landing.
    from clinic.db.models import Patient

    with session_scope() as session:
        all_rows = (
            session.query(
                Patient.id,
                Patient.full_name,
                Patient.birth_year,
                Patient.phone,
                func.coalesce(func.sum(CashierRecord.total), 0).label("total"),
                func.count(CashierRecord.id).label("lines"),
                func.max(CashierRecord.paid_at).label("last_paid_at"),
            )
            .join(CashierRecord, CashierRecord.patient_id == Patient.id)
            .group_by(Patient.id)
            .order_by(func.max(CashierRecord.paid_at).desc())
            .limit(50)
            .all()
        )
    all_cashier_patients = [
        {
            "id": r.id,
            "full_name": r.full_name,
            "birth_year": r.birth_year,
            "phone": r.phone,
            "total": Decimal(r.total or 0),
            "lines": int(r.lines or 0),
            "last_paid_at": r.last_paid_at,
        }
        for r in all_rows
    ]

    patients = []
    if q and len(q.strip()) >= 2:
        patients = patient_service.search(q, limit=20)

    return render(request, "cashier/landing.html", {
        "q": q,
        "patients": patients,
        "today_stats": stats,
        "today_by_type": by_type,
        "today_receipts": today_receipts,
        "patient_names": patient_names,
        "all_cashier_patients": all_cashier_patients,
        "all_time_total": all_time_total,
        "all_time_by_type": all_time_by_type,
    })


# ---------------------------------------------------------------------------
# Per-patient cashier page
# ---------------------------------------------------------------------------


@router.post("/quick")
async def cashier_quick_create(request: Request, _user: str = Depends(require_login)):
    """Walk-in flow: register a bare-minimum patient inline, then jump to cart."""
    from clinic.domain.dto import PatientInput

    form = await request.form()
    patient_in = PatientInput(
        full_name=(form.get("full_name") or "").strip(),
        birth_year=(form.get("birth_year") or "").strip(),
        address=None,
        phone=(form.get("phone") or "").strip() or None,
    )
    lang = resolve_language(request)
    try:
        patient, _created = patient_service.find_or_create(patient_in)
    except ValidationError as ve:
        from clinic.i18n.translator import translator

        joined = "; ".join(
            translator.t(e.message_key, **dict(e.params)) for e in ve.errors.values()
        )
        request.session.setdefault("flash", []).append({
            "level": "danger",
            "text": (
                f"Беморни сақлаб бўлмади: {joined}" if lang == "uz"
                else f"Не удалось сохранить пациента: {joined}"
            ),
        })
        return RedirectResponse(url="/cashier", status_code=303)

    request.session.setdefault("flash", []).append({
        "level": "info",
        "text": (
            f"Бемор тайёр: {patient.full_name}." if lang == "uz"
            else f"Пациент готов: {patient.full_name}."
        ),
    })
    return RedirectResponse(url=f"/cashier/patient/{patient.id}", status_code=303)


@router.get("/patient/{patient_id}")
def cashier_patient(
    request: Request,
    patient_id: int,
    reception_id: int | None = None,
    _user: str = Depends(require_login),
):
    patient = patient_service.get(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="patient_not_found")

    services = service_service.list_all(active_only=True)
    receptions = reception_service.list_for_patient(patient_id)

    history = cashier_service.list_for_patient(patient_id)
    receipts = _group_receipts(history)

    doctor_map: dict[int, str] = {}
    for r in receptions:
        if r.doctor_id and r.doctor_id not in doctor_map:
            doc = doctor_service.get(r.doctor_id)
            if doc:
                doctor_map[r.doctor_id] = doc.full_name

    return render(request, "cashier/patient.html", {
        "patient": patient,
        "services": services,
        "receptions": receptions,
        "receipts": receipts,
        "doctor_map": doctor_map,
        "selected_reception_id": reception_id,
    })


@router.post("/patient/{patient_id}/save")
async def cashier_save(
    request: Request,
    patient_id: int,
    _user: str = Depends(require_login),
):
    patient = patient_service.get(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="patient_not_found")

    form = await request.form()
    service_ids = form.getlist("service_id") if hasattr(form, "getlist") else form.getall("service_id")
    quantities = form.getlist("quantity") if hasattr(form, "getlist") else form.getall("quantity")
    reception_raw = (form.get("reception_id") or "").strip()
    note = (form.get("note") or "").strip() or None
    reception_id = int(reception_raw) if reception_raw.isdigit() else None

    items: list[CashierItemInput] = []
    for sid, qty in zip(service_ids, quantities, strict=False):
        try:
            svc_id = int(sid)
            qty_i = int(qty)
        except (TypeError, ValueError):
            continue
        if svc_id > 0 and qty_i > 0:
            items.append(CashierItemInput(service_id=svc_id, quantity=qty_i))

    payment_type = (form.get("payment_type") or "cash").strip().lower()
    if payment_type not in ("cash", "transfer", "terminal"):
        payment_type = "cash"

    override_raw = (form.get("override_total") or "").strip()
    override_total: Decimal | None = None
    if override_raw:
        try:
            override_total = Decimal(override_raw.replace(" ", "").replace(",", "."))
            if override_total < 0:
                override_total = None
        except Exception:
            override_total = None

    payment = CashierPaymentInput(
        patient_id=patient_id,
        reception_id=reception_id,
        items=items,
        note=note,
        payment_type=payment_type,
        override_total=override_total,
    )

    lang = resolve_language(request)
    try:
        records = cashier_service.save_payment(payment)
    except ValidationError as ve:
        # Translate each FieldError.message_key into a localized message.
        from clinic.i18n.translator import translator

        messages = [translator.t(e.message_key, **dict(e.params)) for e in ve.errors.values()]
        joined = "; ".join(messages) if messages else translator.t("common.validation_failed")
        request.session.setdefault("flash", []).append(
            {"level": "danger",
             "text": (f"Тўловда хатолик: {joined}" if lang == "uz"
                      else f"Ошибка платежа: {joined}")}
        )
        return RedirectResponse(url=f"/cashier/patient/{patient_id}", status_code=303)

    request.session.setdefault("flash", []).append(
        {"level": "success",
         "text": (f"{len(records)} қатор сақланди." if lang == "uz"
                  else f"Сохранено {len(records)} строк.")}
    )
    if records:
        return RedirectResponse(url=f"/cashier/receipt/{records[0].id}", status_code=303)
    return RedirectResponse(url=f"/cashier/patient/{patient_id}", status_code=303)


# ---------------------------------------------------------------------------
# Receipt view
# ---------------------------------------------------------------------------


@router.get("/receipt/{record_id}")
def view_receipt(request: Request, record_id: int, _user: str = Depends(require_login)):
    found = _find_receipt_for(record_id)
    if found is None:
        raise HTTPException(status_code=404, detail="receipt_not_found")
    anchor, items = found
    patient = patient_service.get(anchor.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="patient_not_found")

    total = sum((r.total for r in items), Decimal("0"))
    return render(request, "cashier/receipt.html", {
        "anchor": anchor,
        "items": items,
        "patient": patient,
        "total": total,
    })


@router.post("/record/{record_id}/delete")
def delete_record(request: Request, record_id: int, _user: str = Depends(require_login)):
    """Remove one line-item — used from the patient cashier page."""
    found = _find_receipt_for(record_id)
    patient_id = found[0].patient_id if found else None
    ok = cashier_service.delete(record_id)
    lang = resolve_language(request)
    request.session.setdefault("flash", []).append(
        {"level": "success" if ok else "warning",
         "text": ("Қатор ўчирилди." if lang == "uz" else "Строка удалена.")
                 if ok else ("Қатор топилмади." if lang == "uz" else "Строка не найдена.")}
    )
    dest = f"/cashier/patient/{patient_id}" if patient_id else "/cashier"
    return RedirectResponse(url=dest, status_code=303)
