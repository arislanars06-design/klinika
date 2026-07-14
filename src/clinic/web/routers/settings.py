"""Settings screens: clinic profile, doctors/services CRUD, users, backups.

Every route in this module requires the ``admin`` role.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from clinic.domain import (
    clinic_info_service,
    custom_catalog_service,
    doctor_service,
    service_service,
    template_service,
    user_service,
)
from clinic.domain.clinic_info_service import ClinicInfo
from clinic.infrastructure import backup as backup_service
from clinic.infrastructure.validators import ValidationError
from clinic.web.dependencies import render, require_admin

router = APIRouter(prefix="/settings")


# ---------------------------------------------------------------------------
# Landing
# ---------------------------------------------------------------------------


@router.get("")
def settings_index(request: Request, _: str = Depends(require_admin)):
    return RedirectResponse(url="/settings/clinic", status_code=303)


# ---------------------------------------------------------------------------
# Clinic profile
# ---------------------------------------------------------------------------


@router.get("/clinic")
def clinic_form(request: Request, _: str = Depends(require_admin)):
    info = clinic_info_service.load()
    return render(request, "settings/clinic.html", {"info": info, "tab": "clinic"})


@router.post("/clinic")
async def clinic_save(request: Request, _: str = Depends(require_admin)):
    form = await request.form()
    info = ClinicInfo(
        name_uz=(form.get("name_uz") or "").strip(),
        name_ru=(form.get("name_ru") or "").strip(),
        address_uz=(form.get("address_uz") or "").strip(),
        address_ru=(form.get("address_ru") or "").strip(),
        phone=(form.get("phone") or "").strip(),
        logo_path=(form.get("logo_path") or "").strip(),
        language=(form.get("language") or "uz").strip(),
        theme=(form.get("theme") or "light").strip(),
        save_folder=(form.get("save_folder") or "").strip(),
    )
    clinic_info_service.save(info)
    _flash(request, "success", "settings.clinic_saved")
    return RedirectResponse(url="/settings/clinic", status_code=303)


# ---------------------------------------------------------------------------
# Doctors
# ---------------------------------------------------------------------------


@router.get("/doctors")
def doctors_list(request: Request, _: str = Depends(require_admin)):
    return render(request, "settings/doctors.html", {
        "doctors": doctor_service.list_all(active_only=False),
        "tab": "doctors",
    })


@router.post("/doctors/new")
async def doctors_create(request: Request, _: str = Depends(require_admin)):
    form = await request.form()
    try:
        doctor_service.create(
            full_name=(form.get("full_name") or "").strip(),
            phone=(form.get("phone") or "").strip() or None,
            save_folder=(form.get("save_folder") or "").strip() or None,
        )
        _flash(request, "success", "settings.doctor_added")
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.doctor_error")
    return RedirectResponse(url="/settings/doctors", status_code=303)


@router.post("/doctors/{doctor_id}/edit")
async def doctors_update(doctor_id: int, request: Request, _: str = Depends(require_admin)):
    form = await request.form()
    try:
        # ``save_folder`` field is always present in the edit form, so we
        # always update it — empty string clears the per-doctor override.
        doctor_service.update(
            doctor_id,
            full_name=(form.get("full_name") or "").strip(),
            phone=(form.get("phone") or "").strip() or None,
            save_folder=(form.get("save_folder") or "").strip() or None,
        )
        _flash(request, "success", "settings.doctor_updated")
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.doctor_error")
    return RedirectResponse(url="/settings/doctors", status_code=303)


@router.post("/doctors/{doctor_id}/toggle")
def doctors_toggle(doctor_id: int, request: Request, _: str = Depends(require_admin)):
    current = doctor_service.get(doctor_id)
    if current is None:
        raise HTTPException(status_code=404, detail="doctor_not_found")
    doctor_service.set_active(doctor_id, not current.is_active)
    _flash(request, "success", "settings.doctor_toggled")
    return RedirectResponse(url="/settings/doctors", status_code=303)


@router.post("/doctors/{doctor_id}/delete")
def doctors_delete(doctor_id: int, request: Request, _: str = Depends(require_admin)):
    ok = doctor_service.delete(doctor_id)
    _flash(request, "success" if ok else "warning", "info.deleted" if ok else "common.not_found")
    return RedirectResponse(url="/settings/doctors", status_code=303)


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


@router.get("/services")
def services_list(request: Request, _: str = Depends(require_admin)):
    return render(request, "settings/services.html", {
        "services": service_service.list_all(active_only=False),
        "tab": "services",
    })


@router.post("/services/new")
async def services_create(request: Request, _: str = Depends(require_admin)):
    form = await request.form()
    try:
        service_service.create(
            name_uz=(form.get("name_uz") or "").strip(),
            name_ru=(form.get("name_ru") or "").strip(),
            price=(form.get("price") or "0").strip(),
        )
        _flash(request, "success", "settings.service_added")
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.service_error")
    return RedirectResponse(url="/settings/services", status_code=303)


@router.post("/services/{service_id}/edit")
async def services_update(service_id: int, request: Request, _: str = Depends(require_admin)):
    form = await request.form()
    try:
        service_service.update(
            service_id,
            name_uz=(form.get("name_uz") or "").strip(),
            name_ru=(form.get("name_ru") or "").strip(),
            price=(form.get("price") or "0").strip(),
        )
        _flash(request, "success", "settings.service_updated")
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.service_error")
    return RedirectResponse(url="/settings/services", status_code=303)


@router.post("/services/{service_id}/toggle")
def services_toggle(service_id: int, request: Request, _: str = Depends(require_admin)):
    current = service_service.get(service_id)
    if current is None:
        raise HTTPException(status_code=404, detail="service_not_found")
    service_service.set_active(service_id, not current.is_active)
    _flash(request, "success", "settings.service_toggled")
    return RedirectResponse(url="/settings/services", status_code=303)


@router.post("/services/{service_id}/delete")
def services_delete(service_id: int, request: Request, _: str = Depends(require_admin)):
    ok = service_service.delete(service_id)
    _flash(request, "success" if ok else "warning", "info.deleted" if ok else "common.not_found")
    return RedirectResponse(url="/settings/services", status_code=303)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@router.get("/users")
def users_list(request: Request, _: str = Depends(require_admin)):
    return render(request, "settings/users.html", {
        "users": user_service.list_all(active_only=False),
        "tab": "users",
    })


@router.post("/users/new")
async def users_create(request: Request, admin_user: str = Depends(require_admin)):
    del admin_user
    form = await request.form()
    try:
        user_service.create(
            username=(form.get("username") or ""),
            password=(form.get("password") or ""),
            role=(form.get("role") or "staff"),
            full_name=(form.get("full_name") or "").strip(),
        )
        _flash(request, "success", "settings.user_added")
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.user_error")
    return RedirectResponse(url="/settings/users", status_code=303)


@router.post("/users/{user_id}/edit")
async def users_update(user_id: int, request: Request, _: str = Depends(require_admin)):
    form = await request.form()
    try:
        user_service.update(
            user_id,
            role=(form.get("role") or "staff"),
            full_name=(form.get("full_name") or "").strip(),
        )
        _flash(request, "success", "settings.user_updated")
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.user_error")
    return RedirectResponse(url="/settings/users", status_code=303)


@router.post("/users/{user_id}/reset-password")
async def users_reset_password(user_id: int, request: Request, _: str = Depends(require_admin)):
    form = await request.form()
    try:
        ok = user_service.reset_password(user_id, (form.get("password") or ""))
        _flash(
            request,
            "success" if ok else "warning",
            "settings.password_reset" if ok else "common.not_found",
        )
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.user_error")
    return RedirectResponse(url="/settings/users", status_code=303)


@router.post("/users/{user_id}/toggle")
def users_toggle(user_id: int, request: Request, _: str = Depends(require_admin)):
    current = user_service.get(user_id)
    if current is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    # Don't allow admins to deactivate the last remaining active admin.
    if current.role == "admin" and current.is_active:
        actives = [u for u in user_service.list_all(active_only=True) if u.role == "admin"]
        if len(actives) <= 1:
            _flash(request, "warning", "settings.last_admin_protected")
            return RedirectResponse(url="/settings/users", status_code=303)
    user_service.set_active(user_id, not current.is_active)
    _flash(request, "success", "settings.user_toggled")
    return RedirectResponse(url="/settings/users", status_code=303)


# ---------------------------------------------------------------------------
# Catalogs (complaints + LOR STATUS) — user additions
# ---------------------------------------------------------------------------


@router.get("/catalogs")
def catalogs_page(request: Request, _: str = Depends(require_admin)):
    from clinic.domain import catalog_loader

    return render(request, "settings/catalogs.html", {
        "tab": "catalogs",
        "complaints_custom": custom_catalog_service.list_complaints(active_only=False),
        "lor_custom": custom_catalog_service.list_lor(active_only=False),
        "complaint_sections": custom_catalog_service.VALID_COMPLAINT_SECTIONS,
        "lor_methods": custom_catalog_service.VALID_LOR_METHODS,
        "lor_field_types": custom_catalog_service.VALID_LOR_FIELD_TYPES,
        # Built-in JSON exposed to the template so it can render each level
        # (method → section → field → option) with an inline edit form.
        "builtin_complaints": catalog_loader._complaints_raw().get("sections", []),
        "builtin_lor": catalog_loader._lor_status_raw().get("methods", []),
        "complaint_overrides": custom_catalog_service.list_complaint_overrides(),
        "lor_overrides": custom_catalog_service.list_lor_overrides(),
        "options_to_lines": custom_catalog_service.options_to_lines,
    })


# ----- Built-in overrides (unified endpoints) ------------------------------
#
# The code path can be any compound key (section.ear, option.rhinoscopy.
# external_nose.state.unchanged, ...) so we accept it in the form body
# rather than as a URL path parameter.


@router.post("/catalogs/builtin/edit")
async def catalogs_builtin_edit(request: Request, _: str = Depends(require_admin)):
    form = await request.form()
    kind = (form.get("kind") or "").strip()
    code = (form.get("code") or "").strip()
    # ``has_discharge_type`` is complaint-only; presence of the input in the
    # form indicates the user was on a row that supports it.
    has_dt: bool | None = None
    if "has_discharge_type_present" in form:
        has_dt = bool(form.get("has_discharge_type"))
    try:
        custom_catalog_service.set_override(
            kind,
            code,
            name_uz=form.get("name_uz"),
            name_ru=form.get("name_ru"),
            has_discharge_type=has_dt,
            hidden=False,  # saving implies visible; use the hide action to hide
        )
        _flash(request, "success", "settings.catalog_saved")
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.catalog_error")
    return RedirectResponse(url="/settings/catalogs", status_code=303)


@router.post("/catalogs/builtin/hide")
async def catalogs_builtin_hide(request: Request, _: str = Depends(require_admin)):
    form = await request.form()
    kind = (form.get("kind") or "").strip()
    code = (form.get("code") or "").strip()
    try:
        custom_catalog_service.set_override(kind, code, hidden=True)
        _flash(request, "success", "settings.catalog_hidden")
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.catalog_error")
    return RedirectResponse(url="/settings/catalogs", status_code=303)


@router.post("/catalogs/builtin/reset")
async def catalogs_builtin_reset(request: Request, _: str = Depends(require_admin)):
    form = await request.form()
    kind = (form.get("kind") or "").strip()
    code = (form.get("code") or "").strip()
    if kind not in custom_catalog_service.VALID_OVERRIDE_KINDS or not code:
        _flash(request, "warning", "common.not_found")
        return RedirectResponse(url="/settings/catalogs", status_code=303)
    ok = custom_catalog_service.reset_override(kind, code)
    _flash(
        request,
        "success" if ok else "warning",
        "settings.catalog_reset" if ok else "settings.catalog_reset_nochange",
    )
    return RedirectResponse(url="/settings/catalogs", status_code=303)


# ---- Legacy path-based endpoints (kept as thin shims for backwards compat)


@router.post("/catalogs/complaints/builtin/{code}/edit")
async def _legacy_builtin_complaint_edit(
    code: str, request: Request, _: str = Depends(require_admin)
):
    form = await request.form()
    try:
        custom_catalog_service.set_complaint_override(
            code,
            name_uz=form.get("name_uz"),
            name_ru=form.get("name_ru"),
            has_discharge_type=bool(form.get("has_discharge_type")),
            hidden=False,
        )
        _flash(request, "success", "settings.catalog_saved")
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.catalog_error")
    return RedirectResponse(url="/settings/catalogs", status_code=303)


@router.post("/catalogs/complaints/builtin/{code}/hide")
def _legacy_builtin_complaint_hide(
    code: str, request: Request, _: str = Depends(require_admin)
):
    custom_catalog_service.set_complaint_override(code, hidden=True)
    _flash(request, "success", "settings.catalog_hidden")
    return RedirectResponse(url="/settings/catalogs", status_code=303)


@router.post("/catalogs/complaints/builtin/{code}/reset")
def _legacy_builtin_complaint_reset(
    code: str, request: Request, _: str = Depends(require_admin)
):
    ok = custom_catalog_service.reset_complaint_override(code)
    _flash(
        request,
        "success" if ok else "warning",
        "settings.catalog_reset" if ok else "settings.catalog_reset_nochange",
    )
    return RedirectResponse(url="/settings/catalogs", status_code=303)


# ----- Complaints CRUD ------------------------------------------------------


@router.post("/catalogs/complaints/new")
async def catalogs_complaints_create(request: Request, _: str = Depends(require_admin)):
    form = await request.form()
    try:
        custom_catalog_service.create_complaint(
            section=(form.get("section") or "").strip(),
            name_uz=(form.get("name_uz") or "").strip(),
            name_ru=(form.get("name_ru") or "").strip(),
            has_discharge_type=bool(form.get("has_discharge_type")),
        )
        _flash(request, "success", "settings.catalog_complaint_added")
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.catalog_complaint_error")
    return RedirectResponse(url="/settings/catalogs", status_code=303)


@router.post("/catalogs/complaints/{item_id}/edit")
async def catalogs_complaints_update(
    item_id: int, request: Request, _: str = Depends(require_admin)
):
    form = await request.form()
    try:
        updated = custom_catalog_service.update_complaint(
            item_id,
            section=(form.get("section") or "").strip() or None,
            name_uz=(form.get("name_uz") or "").strip() or None,
            name_ru=(form.get("name_ru") or "").strip() or None,
            has_discharge_type=bool(form.get("has_discharge_type")),
        )
        if updated is None:
            _flash(request, "warning", "common.not_found")
        else:
            _flash(request, "success", "settings.catalog_complaint_updated")
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.catalog_complaint_error")
    return RedirectResponse(url="/settings/catalogs", status_code=303)


@router.post("/catalogs/complaints/{item_id}/toggle")
def catalogs_complaints_toggle(
    item_id: int, request: Request, _: str = Depends(require_admin)
):
    current = custom_catalog_service.get_complaint(item_id)
    if current is None:
        _flash(request, "warning", "common.not_found")
        return RedirectResponse(url="/settings/catalogs", status_code=303)
    custom_catalog_service.update_complaint(item_id, is_active=not current.is_active)
    _flash(request, "success", "settings.catalog_toggled")
    return RedirectResponse(url="/settings/catalogs", status_code=303)


@router.post("/catalogs/complaints/{item_id}/delete")
def catalogs_complaints_delete(
    item_id: int, request: Request, _: str = Depends(require_admin)
):
    ok = custom_catalog_service.delete_complaint(item_id)
    _flash(
        request,
        "success" if ok else "warning",
        "info.deleted" if ok else "common.not_found",
    )
    return RedirectResponse(url="/settings/catalogs", status_code=303)


# ----- LOR STATUS CRUD ------------------------------------------------------


@router.post("/catalogs/lor/new")
async def catalogs_lor_create(request: Request, _: str = Depends(require_admin)):
    form = await request.form()
    try:
        custom_catalog_service.create_lor(
            method=(form.get("method") or "").strip(),
            field_type=(form.get("field_type") or "text").strip(),
            label_uz=(form.get("label_uz") or "").strip(),
            label_ru=(form.get("label_ru") or "").strip(),
            options_raw=(form.get("options_raw") or ""),
        )
        _flash(request, "success", "settings.catalog_lor_added")
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.catalog_lor_error")
    return RedirectResponse(url="/settings/catalogs", status_code=303)


@router.post("/catalogs/lor/{item_id}/edit")
async def catalogs_lor_update(
    item_id: int, request: Request, _: str = Depends(require_admin)
):
    form = await request.form()
    try:
        updated = custom_catalog_service.update_lor(
            item_id,
            method=(form.get("method") or "").strip() or None,
            field_type=(form.get("field_type") or "").strip() or None,
            label_uz=(form.get("label_uz") or "").strip() or None,
            label_ru=(form.get("label_ru") or "").strip() or None,
            options_raw=form.get("options_raw"),
        )
        if updated is None:
            _flash(request, "warning", "common.not_found")
        else:
            _flash(request, "success", "settings.catalog_lor_updated")
    except ValidationError as ve:
        _flash_validation(request, ve, prefix="settings.catalog_lor_error")
    return RedirectResponse(url="/settings/catalogs", status_code=303)


@router.post("/catalogs/lor/{item_id}/toggle")
def catalogs_lor_toggle(
    item_id: int, request: Request, _: str = Depends(require_admin)
):
    current = custom_catalog_service.get_lor(item_id)
    if current is None:
        _flash(request, "warning", "common.not_found")
        return RedirectResponse(url="/settings/catalogs", status_code=303)
    custom_catalog_service.update_lor(item_id, is_active=not current.is_active)
    _flash(request, "success", "settings.catalog_toggled")
    return RedirectResponse(url="/settings/catalogs", status_code=303)


@router.post("/catalogs/lor/{item_id}/delete")
def catalogs_lor_delete(
    item_id: int, request: Request, _: str = Depends(require_admin)
):
    ok = custom_catalog_service.delete_lor(item_id)
    _flash(
        request,
        "success" if ok else "warning",
        "info.deleted" if ok else "common.not_found",
    )
    return RedirectResponse(url="/settings/catalogs", status_code=303)


# ---------------------------------------------------------------------------
# Word template
# ---------------------------------------------------------------------------


@router.get("/template")
def template_page(request: Request, _: str = Depends(require_admin)):
    return render(request, "settings/template.html", {
        "tab": "template",
        "template": template_service.status(),
        "max_size_kb": template_service.MAX_TEMPLATE_BYTES // 1024,
    })


@router.get("/template/download")
def template_download(_: str = Depends(require_admin)):
    """Send the currently-installed template as a .docx download."""
    from fastapi.responses import FileResponse

    st = template_service.status()
    if not st.exists:
        raise HTTPException(status_code=404, detail="template_not_found")
    return FileResponse(
        path=str(st.path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="reception_template.docx",
    )


@router.post("/template/upload")
async def template_upload(request: Request, _: str = Depends(require_admin)):
    from fastapi import UploadFile

    form = await request.form()
    upload = form.get("file")
    if not isinstance(upload, UploadFile) or not upload.filename:
        _flash(request, "warning", "settings.template_invalid")
        return RedirectResponse(url="/settings/template", status_code=303)

    try:
        payload = await upload.read()
    finally:
        try:
            await upload.close()
        except Exception:
            pass

    try:
        template_service.save_uploaded(payload)
        _flash(request, "success", "settings.template_uploaded")
    except template_service.TemplateError as te:
        key = {
            "too_large": "settings.template_too_large",
            "invalid":   "settings.template_invalid",
            "empty":     "settings.template_invalid",
        }.get(str(te), "settings.template_invalid")
        _flash(request, "warning", key)
    return RedirectResponse(url="/settings/template", status_code=303)


@router.post("/template/reset")
def template_reset(request: Request, _: str = Depends(require_admin)):
    template_service.reset_to_default()
    _flash(request, "success", "settings.template_reset_ok")
    return RedirectResponse(url="/settings/template", status_code=303)


@router.post("/template/delete")
def template_delete(request: Request, _: str = Depends(require_admin)):
    ok = template_service.delete()
    _flash(
        request,
        "success" if ok else "warning",
        "settings.template_deleted" if ok else "common.not_found",
    )
    return RedirectResponse(url="/settings/template", status_code=303)


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------


@router.get("/backup")
def backup_page(request: Request, _: str = Depends(require_admin)):
    return render(request, "settings/backup.html", {
        "backups": backup_service.list_backups(),
        "tab": "backup",
    })


@router.post("/backup/create")
def backup_create(request: Request, _: str = Depends(require_admin)):
    try:
        entry = backup_service.force_daily_backup()
        _flash(request, "success", "settings.backup_created",
               name=entry.filename, size=_pretty_size(entry.size_bytes))
    except FileNotFoundError:
        _flash(request, "warning", "settings.backup_no_source")
    except Exception:  # pragma: no cover — surfaced to operator
        _flash(request, "danger", "settings.backup_failed")
    return RedirectResponse(url="/settings/backup", status_code=303)


@router.post("/backup/{filename}/restore")
def backup_restore(filename: str, request: Request, _: str = Depends(require_admin)):
    source = _safe_backup_path(filename)
    if source is None:
        raise HTTPException(status_code=404, detail="backup_not_found")
    try:
        backup_service.restore_from(source)
        # Invalidate the session — the DB is a fresh one now.
        request.session.clear()
        return RedirectResponse(url="/login?next=/settings/backup", status_code=303)
    except Exception:
        _flash(request, "danger", "settings.backup_restore_failed")
        return RedirectResponse(url="/settings/backup", status_code=303)


@router.post("/backup/{filename}/delete")
def backup_delete(filename: str, request: Request, _: str = Depends(require_admin)):
    target = _safe_backup_path(filename)
    if target is None:
        raise HTTPException(status_code=404, detail="backup_not_found")
    try:
        target.unlink()
        _flash(request, "success", "settings.backup_deleted", name=filename)
    except OSError:
        _flash(request, "danger", "settings.backup_delete_failed")
    return RedirectResponse(url="/settings/backup", status_code=303)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _flash(request: Request, level: str, key: str, **params) -> None:
    from clinic.i18n.translator import translator

    request.session.setdefault("flash", []).append({
        "level": level,
        "text": translator.t(key, **params),
    })


def _flash_validation(request: Request, ve: ValidationError, *, prefix: str) -> None:
    from clinic.i18n.translator import translator

    parts = [translator.t(e.message_key, **dict(e.params)) for e in ve.errors.values()]
    joined = "; ".join(parts) if parts else translator.t("common.validation_failed")
    request.session.setdefault("flash", []).append({
        "level": "danger",
        "text": f"{translator.t(prefix)}: {joined}",
    })


def _pretty_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024  # type: ignore[assignment]
    return f"{n:.1f} TB"


def _safe_backup_path(filename: str) -> Path | None:
    """Prevent path traversal — the file must live directly in ``backups_dir``."""
    from clinic.config import settings

    if "/" in filename or "\\" in filename or ".." in filename:
        return None
    candidate = (settings.backups_dir / filename).resolve()
    try:
        candidate.relative_to(settings.backups_dir.resolve())
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate



