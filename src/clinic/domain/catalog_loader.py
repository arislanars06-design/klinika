"""Read-only loader for bundled JSON catalogs.

Loads ``complaints.json``, ``lor_status.json``, and ``discharge_types.json``
into simple dicts and caches them. UI code stays free of file I/O.
"""

from __future__ import annotations

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


@lru_cache(maxsize=1)
def complaints_catalog() -> dict[str, Any]:
    return _load_json("complaints.json")


@lru_cache(maxsize=1)
def lor_status_catalog() -> dict[str, Any]:
    return _load_json("lor_status.json")


@lru_cache(maxsize=1)
def discharge_types_catalog() -> dict[str, Any]:
    return _load_json("discharge_types.json")


@lru_cache(maxsize=1)
def address_catalog() -> dict[str, Any]:
    """Uzbekistan regions + districts (used by the reception address selects)."""
    return _load_json("address.json")


def reload_all() -> None:
    """Drop cached copies (useful after user edits catalog files)."""
    complaints_catalog.cache_clear()
    lor_status_catalog.cache_clear()
    discharge_types_catalog.cache_clear()
    address_catalog.cache_clear()
    logger.debug("Catalog caches cleared")
