"""CRUD for user-added and overridden catalog items.

Three storage tiers:

1. Built-in JSON (``catalogs/*.json``) — shipped read-only reference data.
2. ``catalog_overrides`` table — user edits (rename / hide) applied on top
   of built-in items. Keyed by a compound ``code`` like ``section.ear`` or
   ``option.rhinoscopy.external_nose.state.unchanged``.
3. ``complaint_catalog_custom`` / ``lor_catalog_custom`` — user-added rows.

The merged view (built-in + overrides + customs) is exposed through
:mod:`clinic.domain.catalog_loader` so the reception form and text composer
don't need to know where an item came from.

Override code paths
-------------------

For **complaints** (``kind='complaint'``):

- ``section.<section_code>`` \u2014 rename or hide a whole section
  (e.g. ``section.ear``)
- ``<item_code>`` \u2014 rename or hide an individual item (backwards-compat
  with the initial implementation; item codes are globally unique)

For **LOR STATUS** (``kind='lor'``):

- ``method.<method_code>`` \u2014 rename a method (e.g. ``method.rhinoscopy``)
- ``section.<method>.<section>`` \u2014 rename or hide a section
- ``field.<method>.<section>.<field>`` \u2014 rename the label of a field that
  ships with an explicit ``label`` (rare)
- ``option.<method>.<section>.<field>.<option>`` \u2014 rename or hide a
  single option inside a radio / checkbox_multi field
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from clinic.db.database import session_scope
from clinic.db.models import (
    CatalogOverride,
    ComplaintCatalogCustom,
    LorCatalogCustom,
)
from clinic.infrastructure.validators import ValidationError

# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


@dataclass
class ComplaintCustomDTO:
    id: int
    code: str
    section: str
    name_uz: str
    name_ru: str
    has_discharge_type: bool
    is_active: bool

    @classmethod
    def from_orm(cls, row: ComplaintCatalogCustom) -> "ComplaintCustomDTO":
        return cls(
            id=row.id,
            code=row.code,
            section=row.section,
            name_uz=row.name_uz,
            name_ru=row.name_ru,
            has_discharge_type=bool(row.has_discharge_type),
            is_active=bool(row.is_active),
        )


@dataclass
class CatalogOverrideDTO:
    """One override row (edit or hide of a built-in element)."""

    id: int
    kind: str
    code: str
    name_uz: str | None
    name_ru: str | None
    hidden: bool
    has_discharge_type: bool | None

    @classmethod
    def from_orm(cls, row: CatalogOverride) -> "CatalogOverrideDTO":
        return cls(
            id=row.id,
            kind=row.kind,
            code=row.code,
            name_uz=row.name_uz,
            name_ru=row.name_ru,
            hidden=bool(row.hidden),
            has_discharge_type=row.has_discharge_type,
        )


@dataclass
class LorCustomDTO:
    id: int
    code: str
    method: str
    section: str
    field_type: str
    label_uz: str
    label_ru: str
    options_json: list | None
    is_active: bool

    @classmethod
    def from_orm(cls, row: LorCatalogCustom) -> "LorCustomDTO":
        return cls(
            id=row.id,
            code=row.code,
            method=row.method,
            section=row.section,
            field_type=row.field_type,
            label_uz=row.label_uz,
            label_ru=row.label_ru,
            options_json=list(row.options_json) if row.options_json else None,
            is_active=bool(row.is_active),
        )


# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------

VALID_COMPLAINT_SECTIONS = ("general", "ear", "nose", "pharynx", "larynx")
VALID_LOR_METHODS = ("rhinoscopy", "pharyngoscopy", "otoscopy", "laryngoscopy")
VALID_LOR_FIELD_TYPES = ("text", "checkbox", "radio", "checkbox_multi")
VALID_OVERRIDE_KINDS = ("complaint", "lor")

CUSTOM_LOR_SECTION = "custom"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_CODE_ALLOWED = re.compile(r"[^a-z0-9_]+")
# Overrides use compound codes like "section.ear" or
# "option.rhinoscopy.external_nose.state.unchanged" so the pattern is
# permissive enough to cover them.
_OVERRIDE_CODE_OK = re.compile(r"^[A-Za-z0-9_.-]+$")


def _slug_from_label(prefix: str, label: str) -> str:
    from clinic.infrastructure.translit import cyrillic_to_latin

    latin = cyrillic_to_latin(label) if label else ""
    slug = _CODE_ALLOWED.sub("_", latin.lower()).strip("_")
    slug = slug[:40] if slug else "custom"
    return f"{prefix}_{slug}"


def _unique_complaint_code(session, base: str) -> str:
    from sqlalchemy import select

    candidate = base
    n = 1
    while session.execute(
        select(ComplaintCatalogCustom.id).where(ComplaintCatalogCustom.code == candidate)
    ).scalar_one_or_none() is not None:
        n += 1
        candidate = f"{base}_{n}"
    return candidate


def _unique_lor_code(session, base: str) -> str:
    from sqlalchemy import select

    candidate = base
    n = 1
    while session.execute(
        select(LorCatalogCustom.id).where(LorCatalogCustom.code == candidate)
    ).scalar_one_or_none() is not None:
        n += 1
        candidate = f"{base}_{n}"
    return candidate


def _validate_bilingual(name_uz: str, name_ru: str) -> tuple[str, str]:
    errors = ValidationError()
    uz = (name_uz or "").strip()
    ru = (name_ru or "").strip()
    if not uz:
        errors.add("name_uz", "validation.required")
    if not ru:
        errors.add("name_ru", "validation.required")
    if errors:
        raise errors
    return uz, ru


def _parse_options(raw: str) -> list[dict]:
    if not raw or not raw.strip():
        return []
    options: list[dict] = []
    for i, line in enumerate(raw.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        if "|" in line:
            uz, ru = [p.strip() for p in line.split("|", 1)]
        else:
            uz = ru = line
        options.append({"code": f"opt{i}", "uz": uz or ru, "ru": ru or uz})
    return options


def _options_to_lines(options: list[dict] | None) -> str:
    if not options:
        return ""
    return "\n".join(f"{o.get('uz', '')} | {o.get('ru', '')}" for o in options)


# ---------------------------------------------------------------------------
# Complaints CRUD (user-added)
# ---------------------------------------------------------------------------


def list_complaints(*, active_only: bool = False) -> list[ComplaintCustomDTO]:
    from sqlalchemy import select

    with session_scope() as session:
        stmt = select(ComplaintCatalogCustom).order_by(
            ComplaintCatalogCustom.section, ComplaintCatalogCustom.id
        )
        if active_only:
            stmt = stmt.where(ComplaintCatalogCustom.is_active.is_(True))
        rows = session.execute(stmt).scalars().all()
        return [ComplaintCustomDTO.from_orm(r) for r in rows]


def get_complaint(item_id: int) -> ComplaintCustomDTO | None:
    with session_scope() as session:
        row = session.get(ComplaintCatalogCustom, item_id)
        return ComplaintCustomDTO.from_orm(row) if row else None


def create_complaint(
    *,
    section: str,
    name_uz: str,
    name_ru: str,
    has_discharge_type: bool = False,
) -> ComplaintCustomDTO:
    uz, ru = _validate_bilingual(name_uz, name_ru)
    if section not in VALID_COMPLAINT_SECTIONS:
        err = ValidationError()
        err.add("section", "validation.invalid_choice")
        raise err

    with session_scope() as session:
        base = _slug_from_label(section, uz)
        code = _unique_complaint_code(session, base)
        row = ComplaintCatalogCustom(
            code=code,
            section=section,
            name_uz=uz,
            name_ru=ru,
            has_discharge_type=bool(has_discharge_type),
            is_active=True,
        )
        session.add(row)
        session.flush()
        _bump_catalog_version()
        return ComplaintCustomDTO.from_orm(row)


def update_complaint(
    item_id: int,
    *,
    section: str | None = None,
    name_uz: str | None = None,
    name_ru: str | None = None,
    has_discharge_type: bool | None = None,
    is_active: bool | None = None,
) -> ComplaintCustomDTO | None:
    with session_scope() as session:
        row = session.get(ComplaintCatalogCustom, item_id)
        if row is None:
            return None

        errors = ValidationError()
        if name_uz is not None and not name_uz.strip():
            errors.add("name_uz", "validation.required")
        if name_ru is not None and not name_ru.strip():
            errors.add("name_ru", "validation.required")
        if section is not None and section not in VALID_COMPLAINT_SECTIONS:
            errors.add("section", "validation.invalid_choice")
        if errors:
            raise errors

        if section is not None:
            row.section = section
        if name_uz is not None:
            row.name_uz = name_uz.strip()
        if name_ru is not None:
            row.name_ru = name_ru.strip()
        if has_discharge_type is not None:
            row.has_discharge_type = bool(has_discharge_type)
        if is_active is not None:
            row.is_active = bool(is_active)

        _bump_catalog_version()
        return ComplaintCustomDTO.from_orm(row)


def delete_complaint(item_id: int) -> bool:
    with session_scope() as session:
        row = session.get(ComplaintCatalogCustom, item_id)
        if row is None:
            return False
        session.delete(row)
        _bump_catalog_version()
        return True


# ---------------------------------------------------------------------------
# LOR STATUS CRUD (user-added)
# ---------------------------------------------------------------------------


def list_lor(*, active_only: bool = False) -> list[LorCustomDTO]:
    from sqlalchemy import select

    with session_scope() as session:
        stmt = select(LorCatalogCustom).order_by(
            LorCatalogCustom.method, LorCatalogCustom.id
        )
        if active_only:
            stmt = stmt.where(LorCatalogCustom.is_active.is_(True))
        rows = session.execute(stmt).scalars().all()
        return [LorCustomDTO.from_orm(r) for r in rows]


def get_lor(item_id: int) -> LorCustomDTO | None:
    with session_scope() as session:
        row = session.get(LorCatalogCustom, item_id)
        return LorCustomDTO.from_orm(row) if row else None


def create_lor(
    *,
    method: str,
    field_type: str,
    label_uz: str,
    label_ru: str,
    options_raw: str = "",
) -> LorCustomDTO:
    uz, ru = _validate_bilingual(label_uz, label_ru)
    errors = ValidationError()
    if method not in VALID_LOR_METHODS:
        errors.add("method", "validation.invalid_choice")
    if field_type not in VALID_LOR_FIELD_TYPES:
        errors.add("field_type", "validation.invalid_choice")
    if errors:
        raise errors

    options = None
    if field_type in ("radio", "checkbox_multi"):
        parsed = _parse_options(options_raw)
        if not parsed:
            err = ValidationError()
            err.add("options", "validation.required")
            raise err
        options = parsed

    with session_scope() as session:
        base = _slug_from_label(method, uz)
        code = _unique_lor_code(session, base)
        row = LorCatalogCustom(
            code=code,
            method=method,
            section=CUSTOM_LOR_SECTION,
            field_type=field_type,
            label_uz=uz,
            label_ru=ru,
            options_json=options,
            is_active=True,
        )
        session.add(row)
        session.flush()
        _bump_catalog_version()
        return LorCustomDTO.from_orm(row)


def update_lor(
    item_id: int,
    *,
    method: str | None = None,
    field_type: str | None = None,
    label_uz: str | None = None,
    label_ru: str | None = None,
    options_raw: str | None = None,
    is_active: bool | None = None,
) -> LorCustomDTO | None:
    with session_scope() as session:
        row = session.get(LorCatalogCustom, item_id)
        if row is None:
            return None

        errors = ValidationError()
        if label_uz is not None and not label_uz.strip():
            errors.add("label_uz", "validation.required")
        if label_ru is not None and not label_ru.strip():
            errors.add("label_ru", "validation.required")
        if method is not None and method not in VALID_LOR_METHODS:
            errors.add("method", "validation.invalid_choice")
        if field_type is not None and field_type not in VALID_LOR_FIELD_TYPES:
            errors.add("field_type", "validation.invalid_choice")
        if errors:
            raise errors

        if method is not None:
            row.method = method
        if field_type is not None:
            row.field_type = field_type
        if label_uz is not None:
            row.label_uz = label_uz.strip()
        if label_ru is not None:
            row.label_ru = label_ru.strip()
        if is_active is not None:
            row.is_active = bool(is_active)

        final_type = row.field_type
        if options_raw is not None:
            if final_type in ("radio", "checkbox_multi"):
                parsed = _parse_options(options_raw)
                if not parsed:
                    err = ValidationError()
                    err.add("options", "validation.required")
                    raise err
                row.options_json = parsed
            else:
                row.options_json = None
        elif final_type not in ("radio", "checkbox_multi"):
            row.options_json = None

        _bump_catalog_version()
        return LorCustomDTO.from_orm(row)


def delete_lor(item_id: int) -> bool:
    with session_scope() as session:
        row = session.get(LorCatalogCustom, item_id)
        if row is None:
            return False
        session.delete(row)
        _bump_catalog_version()
        return True


# ---------------------------------------------------------------------------
# Cache invalidation hook
# ---------------------------------------------------------------------------


def _bump_catalog_version() -> None:
    try:
        from clinic.domain import catalog_loader

        catalog_loader.bump_custom_version()
    except Exception:
        pass


def options_to_lines(options: list[dict] | None) -> str:
    return _options_to_lines(options)


# ---------------------------------------------------------------------------
# Overrides (built-in items)
# ---------------------------------------------------------------------------


def list_complaint_overrides() -> dict[str, CatalogOverrideDTO]:
    return _list_overrides("complaint")


def list_lor_overrides() -> dict[str, CatalogOverrideDTO]:
    return _list_overrides("lor")


def _list_overrides(kind: str) -> dict[str, CatalogOverrideDTO]:
    from sqlalchemy import select

    with session_scope() as session:
        rows = session.execute(
            select(CatalogOverride).where(CatalogOverride.kind == kind)
        ).scalars().all()
        return {r.code: CatalogOverrideDTO.from_orm(r) for r in rows}


def set_override(
    kind: str,
    code: str,
    *,
    name_uz: str | None = None,
    name_ru: str | None = None,
    has_discharge_type: bool | None = None,
    hidden: bool | None = None,
) -> CatalogOverrideDTO:
    """Create-or-update the override row for a built-in item.

    Only fields explicitly passed are written; ``None`` means "leave alone".
    Blank / whitespace-only ``name_uz`` or ``name_ru`` clears that column
    so the built-in default is restored for that language.
    """
    errors = ValidationError()
    if kind not in VALID_OVERRIDE_KINDS:
        errors.add("kind", "validation.invalid_choice")
    code = (code or "").strip()
    if not code:
        errors.add("code", "validation.required")
    elif not _OVERRIDE_CODE_OK.match(code):
        errors.add("code", "validation.invalid_choice")
    if errors:
        raise errors

    from sqlalchemy import select

    def _clean(v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None

    with session_scope() as session:
        row = session.execute(
            select(CatalogOverride).where(
                CatalogOverride.kind == kind, CatalogOverride.code == code
            )
        ).scalar_one_or_none()

        if row is None:
            row = CatalogOverride(kind=kind, code=code)
            session.add(row)

        if name_uz is not None:
            row.name_uz = _clean(name_uz)
        if name_ru is not None:
            row.name_ru = _clean(name_ru)
        if has_discharge_type is not None:
            row.has_discharge_type = bool(has_discharge_type)
        if hidden is not None:
            row.hidden = bool(hidden)

        session.flush()
        _bump_catalog_version()
        return CatalogOverrideDTO.from_orm(row)


def reset_override(kind: str, code: str) -> bool:
    """Remove the override row for ``(kind, code)`` \u2014 built-in default restored."""
    from sqlalchemy import select

    with session_scope() as session:
        row = session.execute(
            select(CatalogOverride).where(
                CatalogOverride.kind == kind, CatalogOverride.code == code
            )
        ).scalar_one_or_none()
        if row is None:
            return False
        session.delete(row)
        _bump_catalog_version()
        return True


# ---- Convenience wrappers (kept for backwards compatibility) --------------


def set_complaint_override(
    code: str,
    *,
    name_uz: str | None = None,
    name_ru: str | None = None,
    has_discharge_type: bool | None = None,
    hidden: bool | None = None,
) -> CatalogOverrideDTO:
    return set_override(
        "complaint",
        code,
        name_uz=name_uz,
        name_ru=name_ru,
        has_discharge_type=has_discharge_type,
        hidden=hidden,
    )


def set_lor_override(
    code: str,
    *,
    name_uz: str | None = None,
    name_ru: str | None = None,
    hidden: bool | None = None,
) -> CatalogOverrideDTO:
    return set_override(
        "lor", code, name_uz=name_uz, name_ru=name_ru, hidden=hidden
    )


def reset_complaint_override(code: str) -> bool:
    return reset_override("complaint", code)


def reset_lor_override(code: str) -> bool:
    return reset_override("lor", code)


__all__ = [
    "CUSTOM_LOR_SECTION",
    "CatalogOverrideDTO",
    "ComplaintCustomDTO",
    "LorCustomDTO",
    "VALID_COMPLAINT_SECTIONS",
    "VALID_LOR_FIELD_TYPES",
    "VALID_LOR_METHODS",
    "VALID_OVERRIDE_KINDS",
    "create_complaint",
    "create_lor",
    "delete_complaint",
    "delete_lor",
    "get_complaint",
    "get_lor",
    "list_complaint_overrides",
    "list_complaints",
    "list_lor",
    "list_lor_overrides",
    "options_to_lines",
    "reset_complaint_override",
    "reset_lor_override",
    "reset_override",
    "set_complaint_override",
    "set_lor_override",
    "set_override",
    "update_complaint",
    "update_lor",
]
