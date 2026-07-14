"""Domain service for CRUD over the custom LOR STATUS catalog.

Bundled LOR STATUS items ship in ``catalogs/lor_status.json``. Users can add
their own via ``settings/lor_status`` — those extras live in the
``lor_catalog_custom`` table and are merged into the reception form by
:mod:`clinic.domain.catalog_loader`.

For MVP the ``options`` payload is captured as a comma-separated list of
labels; each entry is stored as ``{"code": <slug>, "uz": <label>, "ru": <label>}``
so the reception form renders it just like a bundled option.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from clinic.db.database import session_scope
from clinic.db.models import LorCatalogCustom
from clinic.infrastructure.validators import ValidationError

VALID_METHODS = ("rhinoscopy", "pharyngoscopy", "laryngoscopy", "otoscopy")
VALID_FIELD_TYPES = ("radio", "checkbox", "text", "side", "degree", "checkbox_multi")


@dataclass
class LorCustomDTO:
    id: int
    code: str
    method: str
    section: str
    field_type: str
    label_uz: str
    label_ru: str
    options: list[dict[str, str]]
    is_active: bool

    @property
    def options_text(self) -> str:
        """Return options as a comma-separated string for edit forms."""
        return ", ".join(o.get("uz") or o.get("code") or "" for o in self.options)

    @classmethod
    def from_orm(cls, row: LorCatalogCustom) -> LorCustomDTO:
        return cls(
            id=row.id,
            code=row.code,
            method=row.method,
            section=row.section,
            field_type=row.field_type,
            label_uz=row.label_uz,
            label_ru=row.label_ru,
            options=list(row.options_json or []),
            is_active=bool(row.is_active),
        )


def list_custom(*, active_only: bool = False) -> list[LorCustomDTO]:
    with session_scope() as session:
        stmt = select(LorCatalogCustom)
        if active_only:
            stmt = stmt.where(LorCatalogCustom.is_active.is_(True))
        stmt = stmt.order_by(LorCatalogCustom.method, LorCatalogCustom.id)
        rows = list(session.execute(stmt).scalars())
        return [LorCustomDTO.from_orm(r) for r in rows]


def get(item_id: int) -> LorCustomDTO | None:
    with session_scope() as session:
        row = session.get(LorCatalogCustom, item_id)
        return LorCustomDTO.from_orm(row) if row else None


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")


def _parse_options(raw: str | None) -> list[dict[str, str]]:
    """Split a comma-separated string into ``[{code, uz, ru}, ...]`` entries."""
    if not raw:
        return []
    labels = [p.strip() for p in raw.split(",") if p.strip()]
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for i, label in enumerate(labels):
        code = _slug(label) or f"opt_{i+1}"
        # Deduplicate codes so downstream lookups stay unambiguous.
        base = code
        j = 2
        while code in seen:
            code = f"{base}_{j}"
            j += 1
        seen.add(code)
        result.append({"code": code, "uz": label, "ru": label})
    return result


def _validate(
    *,
    method: str,
    section: str,
    field_type: str,
    label_uz: str,
    label_ru: str,
) -> tuple[str, str, str, str, str]:
    errors = ValidationError()
    method_norm = (method or "").strip().lower()
    section_norm = (section or "").strip()
    field_type_norm = (field_type or "").strip().lower()
    label_uz_norm = (label_uz or "").strip()
    label_ru_norm = (label_ru or "").strip()
    if method_norm not in VALID_METHODS:
        errors.add("method", "validation.invalid_choice")
    if field_type_norm not in VALID_FIELD_TYPES:
        errors.add("field_type", "validation.invalid_choice")
    if not section_norm:
        errors.add("section", "validation.required")
    if not label_uz_norm:
        errors.add("label_uz", "validation.required")
    if not label_ru_norm:
        errors.add("label_ru", "validation.required")
    if errors:
        raise errors
    return method_norm, section_norm, field_type_norm, label_uz_norm, label_ru_norm


def _make_code(session, method: str, section: str, label: str) -> str:
    slug = _slug(f"{section}_{label}")[:48] or "custom"
    base = f"custom_{method}_{slug}"
    candidate = base
    suffix = 2
    while session.execute(
        select(LorCatalogCustom).where(LorCatalogCustom.code == candidate)
    ).scalar_one_or_none() is not None:
        candidate = f"{base}_{suffix}"
        suffix += 1
    return candidate


def create(
    *,
    method: str,
    section: str,
    field_type: str,
    label_uz: str,
    label_ru: str,
    options_raw: str | None = None,
) -> LorCustomDTO:
    method, section, field_type, label_uz, label_ru = _validate(
        method=method, section=section, field_type=field_type,
        label_uz=label_uz, label_ru=label_ru,
    )
    options = _parse_options(options_raw) if field_type in ("radio", "checkbox_multi") else []

    with session_scope() as session:
        code = _make_code(session, method, section, label_uz)
        row = LorCatalogCustom(
            code=code,
            method=method,
            section=section,
            field_type=field_type,
            label_uz=label_uz,
            label_ru=label_ru,
            options_json=options or None,
            is_active=True,
        )
        session.add(row)
        session.flush()
        return LorCustomDTO.from_orm(row)


def update(
    item_id: int,
    *,
    method: str | None = None,
    section: str | None = None,
    field_type: str | None = None,
    label_uz: str | None = None,
    label_ru: str | None = None,
    options_raw: str | None = None,
    is_active: bool | None = None,
) -> LorCustomDTO | None:
    errors = ValidationError()
    with session_scope() as session:
        row = session.get(LorCatalogCustom, item_id)
        if row is None:
            return None
        if method is not None:
            v = method.strip().lower()
            if v not in VALID_METHODS:
                errors.add("method", "validation.invalid_choice")
            else:
                row.method = v
        if section is not None:
            v = section.strip()
            if not v:
                errors.add("section", "validation.required")
            else:
                row.section = v
        if field_type is not None:
            v = field_type.strip().lower()
            if v not in VALID_FIELD_TYPES:
                errors.add("field_type", "validation.invalid_choice")
            else:
                row.field_type = v
        if label_uz is not None:
            v = label_uz.strip()
            if not v:
                errors.add("label_uz", "validation.required")
            else:
                row.label_uz = v
        if label_ru is not None:
            v = label_ru.strip()
            if not v:
                errors.add("label_ru", "validation.required")
            else:
                row.label_ru = v
        if options_raw is not None:
            row.options_json = (
                _parse_options(options_raw)
                if row.field_type in ("radio", "checkbox_multi")
                else None
            )
        if is_active is not None:
            row.is_active = bool(is_active)
        if errors:
            raise errors
        return LorCustomDTO.from_orm(row)


def set_active(item_id: int, is_active: bool) -> LorCustomDTO | None:
    with session_scope() as session:
        row = session.get(LorCatalogCustom, item_id)
        if row is None:
            return None
        row.is_active = bool(is_active)
        return LorCustomDTO.from_orm(row)


def delete(item_id: int) -> bool:
    with session_scope() as session:
        row = session.get(LorCatalogCustom, item_id)
        if row is None:
            return False
        session.delete(row)
        return True


def as_field_dict(dto: LorCustomDTO) -> dict[str, Any]:
    """Shape a custom entry so it looks like a bundled JSON field."""
    field: dict[str, Any] = {
        "code": dto.code,
        "type": dto.field_type,
    }
    if dto.field_type in ("radio", "checkbox_multi"):
        field["options"] = [dict(o) for o in dto.options]
    elif dto.field_type == "checkbox":
        field["label"] = {"uz": dto.label_uz, "ru": dto.label_ru}
    return field


__all__ = [
    "VALID_FIELD_TYPES",
    "VALID_METHODS",
    "LorCustomDTO",
    "as_field_dict",
    "create",
    "delete",
    "get",
    "list_custom",
    "set_active",
    "update",
]
