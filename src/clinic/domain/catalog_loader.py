"""Read-only loader for bundled JSON catalogs, merged with user-added extras.

Loads ``complaints.json``, ``lor_status.json``, and ``discharge_types.json``
into simple dicts and caches them. User-added items from the DB
(``complaint_catalog_custom`` and ``lor_catalog_custom``) are merged in on
every call so the reception form always reflects the latest custom entries.
"""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from loguru import logger

from clinic.config import settings


def _load_json(filename: str) -> dict[str, Any]:
    path: Path = settings.catalogs_dir / filename
    if not path.is_file():
        logger.error("Catalog file missing: {}", path)
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Bundled JSON — cached because the files never change at runtime.
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _bundled_complaints() -> dict[str, Any]:
    return _load_json("complaints.json")


@lru_cache(maxsize=1)
def _bundled_lor_status() -> dict[str, Any]:
    return _load_json("lor_status.json")


@lru_cache(maxsize=1)
def discharge_types_catalog() -> dict[str, Any]:
    return _load_json("discharge_types.json")


@lru_cache(maxsize=1)
def address_catalog() -> dict[str, Any]:
    """Uzbekistan regions + districts (used by the reception address selects)."""
    return _load_json("address.json")


# ---------------------------------------------------------------------------
# Merged catalogs — DO NOT cache; user CRUD invalidates them on every write.
# ---------------------------------------------------------------------------


def complaints_catalog() -> dict[str, Any]:
    """Bundled complaints merged with user-added custom rows.

    Custom rows are appended to their matching ``section``. If a custom row
    references a section that isn't in the bundled file we still surface it
    under a synthesised section so nothing goes missing.
    """
    merged = copy.deepcopy(_bundled_complaints())
    try:
        from clinic.domain import complaint_catalog_service
    except Exception:  # pragma: no cover — defensive import order
        return merged

    try:
        customs = complaint_catalog_service.list_custom(active_only=True)
    except Exception:
        logger.exception("Failed to load custom complaints")
        return merged
    if not customs:
        return merged

    sections = merged.setdefault("sections", [])
    section_map = {s["code"]: s for s in sections}
    for row in customs:
        target = section_map.get(row.section)
        if target is None:
            target = {
                "code": row.section,
                "name": {"uz": row.section.upper(), "ru": row.section.upper()},
                "items": [],
            }
            sections.append(target)
            section_map[row.section] = target
        item: dict[str, Any] = {
            "code": row.code,
            "uz": row.name_uz,
            "ru": row.name_ru,
        }
        if row.has_discharge_type:
            item["has_discharge_type"] = True
        target.setdefault("items", []).append(item)
    return merged


def lor_status_catalog() -> dict[str, Any]:
    """Bundled LOR STATUS merged with user-added custom fields.

    Custom rows are appended to the matching method under a section named after
    their ``section`` string. New sections/methods are created on the fly when
    the referenced code isn't in the bundled file, so freshly added items are
    always visible.
    """
    merged = copy.deepcopy(_bundled_lor_status())
    try:
        from clinic.domain import lor_catalog_service
    except Exception:  # pragma: no cover
        return merged

    try:
        customs = lor_catalog_service.list_custom(active_only=True)
    except Exception:
        logger.exception("Failed to load custom LOR items")
        return merged
    if not customs:
        return merged

    methods = merged.setdefault("methods", [])
    method_map = {m["code"]: m for m in methods}
    for row in customs:
        method = method_map.get(row.method)
        if method is None:
            method = {
                "code": row.method,
                "name": {"uz": row.method.upper(), "ru": row.method.upper()},
                "sections": [],
            }
            methods.append(method)
            method_map[row.method] = method
        sections = method.setdefault("sections", [])
        section_key = (row.section or "custom").strip()
        section = next((s for s in sections if s["code"] == section_key), None)
        if section is None:
            section = {
                "code": section_key,
                "name": {"uz": section_key, "ru": section_key},
                "fields": [],
            }
            sections.append(section)
        section.setdefault("fields", []).append(lor_catalog_service.as_field_dict(row))
    return merged


def reload_all() -> None:
    """Drop cached copies (useful after user edits catalog files)."""
    _bundled_complaints.cache_clear()
    _bundled_lor_status.cache_clear()
    discharge_types_catalog.cache_clear()
    address_catalog.cache_clear()
    logger.debug("Catalog caches cleared")
