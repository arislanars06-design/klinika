"""Read-only loader for bundled JSON catalogs.

Loads ``complaints.json``, ``lor_status.json``, and ``discharge_types.json``
into simple dicts and caches them. UI code stays free of file I/O.

The complaints and LOR STATUS catalogs are additionally merged with any
user-added rows stored in the ``complaint_catalog_custom`` and
``lor_catalog_custom`` tables. The merge happens on every call (cheap) but
the built-in JSON is only parsed once. The DB portion is refreshed lazily
via ``_custom_version`` — whenever the settings/catalogs CRUD mutates a
row it calls :func:`bump_custom_version` which forces the next merge to
re-query the tables.
"""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from loguru import logger

from clinic.config import settings

# Bumped by ``custom_catalog_service`` on every CRUD mutation so the merged
# catalog is regenerated on the next read.
_custom_version: int = 0


def bump_custom_version() -> None:
    """Invalidate the merged-catalog cache."""
    global _custom_version
    _custom_version += 1


def _load_json(filename: str) -> dict[str, Any]:
    path: Path = settings.catalogs_dir / filename
    if not path.is_file():
        logger.error("Catalog file missing: {}", path)
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Built-in JSON catalogs (cached forever — files ship with the app)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _complaints_raw() -> dict[str, Any]:
    return _load_json("complaints.json")


@lru_cache(maxsize=1)
def _lor_status_raw() -> dict[str, Any]:
    return _load_json("lor_status.json")


@lru_cache(maxsize=1)
def discharge_types_catalog() -> dict[str, Any]:
    return _load_json("discharge_types.json")


@lru_cache(maxsize=1)
def address_catalog() -> dict[str, Any]:
    """Uzbekistan regions + districts (used by the reception address selects)."""
    return _load_json("address.json")


# ---------------------------------------------------------------------------
# Merged (built-in + DB customs) catalogs
# ---------------------------------------------------------------------------


def complaints_catalog() -> dict[str, Any]:
    """Return the complaints catalog including user-added items.

    The shape matches the JSON schema; custom items are appended to the
    ``items`` list of the matching section (or a synthetic "custom" section
    if no matching one exists).
    """
    return _merge_complaints(_custom_version)


def lor_status_catalog() -> dict[str, Any]:
    """Return the LOR STATUS catalog with user-added items appended.

    Each method gains an extra "custom" section that lists the DB-backed
    items belonging to that method.
    """
    return _merge_lor(_custom_version)


# ---------------------------------------------------------------------------
# Merge implementation (memoised by ``_custom_version``)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=4)
def _merge_complaints(_version: int) -> dict[str, Any]:
    """Merge JSON complaints with rows from the custom + override tables."""
    merged = copy.deepcopy(_complaints_raw())
    sections = merged.setdefault("sections", [])
    section_map = {sec["code"]: sec for sec in sections}

    # ---- Apply built-in overrides (rename / hide) --------------------------
    overrides = _fetch_overrides("complaint")
    for section in sections:
        filtered: list[dict] = []
        for item in section.get("items", []):
            ov = overrides.get(item.get("code"))
            if ov is None:
                filtered.append(item)
                continue
            if ov.get("hidden"):
                continue  # user hid this built-in
            # Apply rename / discharge override in place.
            if ov.get("name_uz"):
                item["uz"] = ov["name_uz"]
            if ov.get("name_ru"):
                item["ru"] = ov["name_ru"]
            if ov.get("has_discharge_type") is not None:
                item["has_discharge_type"] = bool(ov["has_discharge_type"])
            item["_overridden"] = True
            filtered.append(item)
        section["items"] = filtered

    # ---- Append user-added items ------------------------------------------
    for row in _fetch_custom_complaints():
        section = section_map.get(row["section"])
        if section is None:
            # Unknown section → create a "Custom" bucket to keep the item visible.
            section = {
                "code": row["section"],
                "name": {"uz": row["section"].upper(), "ru": row["section"].upper()},
                "items": [],
                "custom": True,
            }
            sections.append(section)
            section_map[row["section"]] = section
        section.setdefault("items", []).append({
            "code": row["code"],
            "uz": row["name_uz"],
            "ru": row["name_ru"],
            "has_discharge_type": bool(row.get("has_discharge_type")),
            "_custom_id": row["id"],
        })
    return merged


@lru_cache(maxsize=4)
def _merge_lor(_version: int) -> dict[str, Any]:
    """Merge JSON LOR STATUS with rows from the custom + override tables."""
    merged = copy.deepcopy(_lor_status_raw())
    methods = merged.setdefault("methods", [])
    method_map = {m["code"]: m for m in methods}

    # ---- Apply built-in overrides (rename / hide) to every field ----------
    overrides = _fetch_overrides("lor")
    for method in methods:
        for section in method.get("sections", []):
            filtered_fields: list[dict] = []
            for field in section.get("fields", []):
                ov = overrides.get(field.get("code"))
                if ov is None:
                    filtered_fields.append(field)
                    continue
                if ov.get("hidden"):
                    continue
                if ov.get("name_uz") or ov.get("name_ru"):
                    label = dict(field.get("label") or {})
                    if ov.get("name_uz"):
                        label["uz"] = ov["name_uz"]
                    if ov.get("name_ru"):
                        label["ru"] = ov["name_ru"]
                    field["label"] = label
                field["_overridden"] = True
                filtered_fields.append(field)
            section["fields"] = filtered_fields

    # Group customs by method.
    grouped: dict[str, list[dict]] = {}
    for row in _fetch_custom_lor():
        grouped.setdefault(row["method"], []).append(row)

    for method_code, rows in grouped.items():
        method = method_map.get(method_code)
        if method is None:
            continue  # unknown method — ignore.
        # Build a single "custom" section per method.
        fields: list[dict] = []
        for row in rows:
            ftype = row["field_type"]
            field: dict = {
                "code": row["code"],
                "type": ftype,
            }
            if ftype == "checkbox":
                field["label"] = {"uz": row["name_uz"], "ru": row["name_ru"]}
            else:
                # For radio/checkbox_multi/text the label text goes into the
                # ``label`` map so the template can render a heading.
                field["label"] = {"uz": row["name_uz"], "ru": row["name_ru"]}
            if row.get("options_json"):
                field["options"] = row["options_json"]
            fields.append(field)

        if not fields:
            continue

        section = {
            "code": "custom_items",
            "custom": True,
            "name": {
                "uz": "Қўшимча (созламадан)",
                "ru": "Дополнительно (из настроек)",
            },
            "fields": fields,
        }
        method.setdefault("sections", []).append(section)

    return merged


# ---------------------------------------------------------------------------
# DB access (kept local to avoid import cycles at module load)
# ---------------------------------------------------------------------------


def _fetch_custom_complaints() -> list[dict[str, Any]]:
    """Return active custom complaints as plain dicts (or [] if DB not ready)."""
    try:
        from sqlalchemy import select

        from clinic.db.database import session_scope
        from clinic.db.models import ComplaintCatalogCustom
    except Exception:
        return []

    try:
        with session_scope() as session:
            rows = session.execute(
                select(ComplaintCatalogCustom).where(
                    ComplaintCatalogCustom.is_active.is_(True)
                ).order_by(ComplaintCatalogCustom.id)
            ).scalars().all()
            return [
                {
                    "id": r.id,
                    "code": r.code,
                    "section": r.section,
                    "name_uz": r.name_uz,
                    "name_ru": r.name_ru,
                    "has_discharge_type": bool(r.has_discharge_type),
                }
                for r in rows
            ]
    except Exception:
        # Table may not exist yet (fresh install) — behave as if empty.
        logger.debug("Custom complaints table unavailable")
        return []


def _fetch_overrides(kind: str) -> dict[str, dict[str, Any]]:
    """Return ``{code: override_dict}`` for the given kind, or {} on error."""
    try:
        from sqlalchemy import select

        from clinic.db.database import session_scope
        from clinic.db.models import CatalogOverride
    except Exception:
        return {}
    try:
        with session_scope() as session:
            rows = session.execute(
                select(CatalogOverride).where(CatalogOverride.kind == kind)
            ).scalars().all()
            return {
                r.code: {
                    "name_uz": r.name_uz,
                    "name_ru": r.name_ru,
                    "hidden": bool(r.hidden),
                    "has_discharge_type": r.has_discharge_type,
                }
                for r in rows
            }
    except Exception:
        logger.debug("Catalog overrides table unavailable")
        return {}


def _fetch_custom_lor() -> list[dict[str, Any]]:
    try:
        from sqlalchemy import select

        from clinic.db.database import session_scope
        from clinic.db.models import LorCatalogCustom
    except Exception:
        return []

    try:
        with session_scope() as session:
            rows = session.execute(
                select(LorCatalogCustom).where(
                    LorCatalogCustom.is_active.is_(True)
                ).order_by(LorCatalogCustom.id)
            ).scalars().all()
            return [
                {
                    "id": r.id,
                    "code": r.code,
                    "method": r.method,
                    "section": r.section,
                    "field_type": r.field_type,
                    "name_uz": r.label_uz,
                    "name_ru": r.label_ru,
                    "options_json": list(r.options_json) if r.options_json else None,
                }
                for r in rows
            ]
    except Exception:
        logger.debug("Custom LOR catalog table unavailable")
        return []


# ---------------------------------------------------------------------------
# Cache-invalidation
# ---------------------------------------------------------------------------


def reload_all() -> None:
    """Drop cached copies (useful after user edits catalog files)."""
    _complaints_raw.cache_clear()
    _lor_status_raw.cache_clear()
    discharge_types_catalog.cache_clear()
    address_catalog.cache_clear()
    _merge_complaints.cache_clear()
    _merge_lor.cache_clear()
    bump_custom_version()
    logger.debug("Catalog caches cleared")
