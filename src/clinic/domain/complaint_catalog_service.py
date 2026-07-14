"""Domain service for CRUD over the custom complaint catalog.

Bundled complaints ship in ``catalogs/complaints.json``. Users can extend the
list at runtime via ``settings/complaints`` — those extras live in the
``complaint_catalog_custom`` table and are merged into the reception form by
:mod:`clinic.domain.catalog_loader`.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from clinic.db.database import session_scope
from clinic.db.models import ComplaintCatalogCustom
from clinic.infrastructure.validators import ValidationError

VALID_SECTIONS = ("general", "ear", "nose", "pharynx", "larynx")


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
    def from_orm(cls, row: ComplaintCatalogCustom) -> ComplaintCustomDTO:
        return cls(
            id=row.id,
            code=row.code,
            section=row.section,
            name_uz=row.name_uz,
            name_ru=row.name_ru,
            has_discharge_type=bool(row.has_discharge_type),
            is_active=bool(row.is_active),
        )


def list_custom(*, active_only: bool = False) -> list[ComplaintCustomDTO]:
    with session_scope() as session:
        stmt = select(ComplaintCatalogCustom)
        if active_only:
            stmt = stmt.where(ComplaintCatalogCustom.is_active.is_(True))
        stmt = stmt.order_by(ComplaintCatalogCustom.section, ComplaintCatalogCustom.id)
        rows = list(session.execute(stmt).scalars())
        return [ComplaintCustomDTO.from_orm(r) for r in rows]


def get(complaint_id: int) -> ComplaintCustomDTO | None:
    with session_scope() as session:
        row = session.get(ComplaintCatalogCustom, complaint_id)
        return ComplaintCustomDTO.from_orm(row) if row else None


def _validate(section: str, name_uz: str, name_ru: str) -> tuple[str, str, str]:
    errors = ValidationError()
    section = (section or "").strip().lower()
    uz = (name_uz or "").strip()
    ru = (name_ru or "").strip()
    if section not in VALID_SECTIONS:
        errors.add("section", "validation.invalid_choice")
    if not uz:
        errors.add("name_uz", "validation.required")
    if not ru:
        errors.add("name_ru", "validation.required")
    if errors:
        raise errors
    return section, uz, ru


def _make_code(session, section: str, name_uz: str) -> str:
    """Build a unique-ish stable ``code`` for the row.

    We concatenate section + a slugged prefix of the Uzbek name and, if there
    is a collision, append a numeric suffix. Codes are only used to identify
    the entry in the merged catalog; they never surface in the UI.
    """
    import re

    slug = re.sub(r"[^a-z0-9]+", "_", name_uz.lower())[:32].strip("_") or "custom"
    base = f"custom_{section}_{slug}"
    candidate = base
    suffix = 2
    while session.execute(
        select(ComplaintCatalogCustom).where(ComplaintCatalogCustom.code == candidate)
    ).scalar_one_or_none() is not None:
        candidate = f"{base}_{suffix}"
        suffix += 1
    return candidate


def create(
    *,
    section: str,
    name_uz: str,
    name_ru: str,
    has_discharge_type: bool = False,
) -> ComplaintCustomDTO:
    section, uz, ru = _validate(section, name_uz, name_ru)
    with session_scope() as session:
        code = _make_code(session, section, uz)
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
        return ComplaintCustomDTO.from_orm(row)


def update(
    complaint_id: int,
    *,
    section: str | None = None,
    name_uz: str | None = None,
    name_ru: str | None = None,
    has_discharge_type: bool | None = None,
    is_active: bool | None = None,
) -> ComplaintCustomDTO | None:
    errors = ValidationError()
    with session_scope() as session:
        row = session.get(ComplaintCatalogCustom, complaint_id)
        if row is None:
            return None
        if section is not None:
            candidate = section.strip().lower()
            if candidate not in VALID_SECTIONS:
                errors.add("section", "validation.invalid_choice")
            else:
                row.section = candidate
        if name_uz is not None:
            v = name_uz.strip()
            if not v:
                errors.add("name_uz", "validation.required")
            else:
                row.name_uz = v
        if name_ru is not None:
            v = name_ru.strip()
            if not v:
                errors.add("name_ru", "validation.required")
            else:
                row.name_ru = v
        if has_discharge_type is not None:
            row.has_discharge_type = bool(has_discharge_type)
        if is_active is not None:
            row.is_active = bool(is_active)
        if errors:
            raise errors
        return ComplaintCustomDTO.from_orm(row)


def set_active(complaint_id: int, is_active: bool) -> ComplaintCustomDTO | None:
    with session_scope() as session:
        row = session.get(ComplaintCatalogCustom, complaint_id)
        if row is None:
            return None
        row.is_active = bool(is_active)
        return ComplaintCustomDTO.from_orm(row)


def delete(complaint_id: int) -> bool:
    with session_scope() as session:
        row = session.get(ComplaintCatalogCustom, complaint_id)
        if row is None:
            return False
        session.delete(row)
        return True


__all__ = [
    "VALID_SECTIONS",
    "ComplaintCustomDTO",
    "create",
    "delete",
    "get",
    "list_custom",
    "set_active",
    "update",
]
