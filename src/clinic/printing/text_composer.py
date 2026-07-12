"""Convert structured reception data into natural-language paragraphs.

Used by both the on-screen preview and the ``.docx`` builder. Keeping the
rendering here means the same wording appears everywhere the printout is
consumed.
"""

from __future__ import annotations

from typing import Any

from clinic.db.models import Reception
from clinic.domain.catalog_loader import (
    complaints_catalog,
    discharge_types_catalog,
    lor_status_catalog,
)


def _index_complaints(lang: str) -> dict[str, tuple[str, str]]:
    """Map ``complaint_code -> (section_name, label)`` for a given language."""
    idx: dict[str, tuple[str, str]] = {}
    for section in complaints_catalog().get("sections", []):
        section_name = section["name"][lang]
        for item in section["items"]:
            idx[item["code"]] = (section_name, item[lang])
    return idx


def _index_discharge(lang: str) -> dict[str, str]:
    return {row["code"]: row[lang] for row in discharge_types_catalog().get("types", [])}


def render_complaints(
    codes: list[str] | None,
    details: dict[str, str] | None,
    note: str | None,
    lang: str = "uz",
) -> str:
    """Render complaints as ``Section: item1, item2 (details). Section: ...``."""
    codes = codes or []
    details = details or {}
    if not codes and not (note or "").strip():
        return ""

    idx = _index_complaints(lang)
    discharge = _index_discharge(lang)

    grouped: dict[str, list[str]] = {}
    order: list[str] = []
    for code in codes:
        section_label = idx.get(code)
        if section_label is None:
            continue
        section, label = section_label
        if section not in grouped:
            grouped[section] = []
            order.append(section)
        detail_code = details.get(code)
        detail_text = discharge.get(detail_code) if detail_code else None
        grouped[section].append(f"{label} ({detail_text})" if detail_text else label)

    parts = [f"{section}: {', '.join(items)}." for section, items in ((s, grouped[s]) for s in order)]
    result = " ".join(parts)

    if note and note.strip():
        prefix = "Qo'shimcha" if lang == "uz" else "Дополнительно"
        result = f"{result} {prefix}: {note.strip()}." if result else f"{prefix}: {note.strip()}."
    return result


# ----- LOR STATUS -----------------------------------------------------------


def _index_lor_options(lang: str) -> dict[str, dict[str, str]]:
    """Return ``{method: {code: label}}`` for every option value in the catalog."""
    idx: dict[str, dict[str, str]] = {}
    catalog = lor_status_catalog()
    for method in catalog.get("methods", []):
        labels: dict[str, str] = {}
        for section in method.get("sections", []):
            for field in section.get("fields", []):
                for option in field.get("options", ()):
                    labels[option["code"]] = option[lang]
        idx[method["code"]] = labels

    # Global "side" and "degree" labels shared across methods.
    globals_labels: dict[str, str] = {}
    for row in catalog.get("sides", ()):
        globals_labels[row["code"]] = row[lang]
    for row in catalog.get("degrees", ()):
        globals_labels[row["code"]] = row[lang]
    idx["_globals"] = globals_labels
    return idx


def render_lor_status(status: dict[str, Any] | None, lang: str = "uz") -> str:
    """Render LOR STATUS dict into plain text.

    Accepts two shapes:
    - ``{"text": "free-form text"}`` — returned as-is (used for M2 MVP where
      doctors type into a text area).
    - Structured method/section/field dict — flattened into ``Method: k=v; k=v.``
    """
    if not status:
        return ""

    if isinstance(status, dict) and set(status.keys()) == {"text"}:
        return str(status["text"]).strip()

    idx = _index_lor_options(lang)
    labels_map = {
        method["code"]: method["name"][lang]
        for method in lor_status_catalog().get("methods", [])
    }

    lines: list[str] = []
    for method_code, method_data in status.items():
        if method_code.startswith("_"):
            continue
        method_label = labels_map.get(method_code, method_code)
        pairs: list[str] = []
        method_labels = idx.get(method_code, {})
        globals_labels = idx.get("_globals", {})

        def _readable(val: Any) -> str:
            if isinstance(val, list):
                return ", ".join(method_labels.get(v, globals_labels.get(v, str(v))) for v in val)
            return method_labels.get(val, globals_labels.get(val, str(val)))

        for section_code, section_data in method_data.items():
            if isinstance(section_data, dict):
                for field_code, value in section_data.items():
                    pairs.append(f"{section_code}.{field_code}={_readable(value)}")
            else:
                pairs.append(f"{section_code}={_readable(section_data)}")

        if pairs:
            lines.append(f"{method_label}: " + "; ".join(pairs) + ".")

    return "\n".join(lines)


# ----- Full reception -------------------------------------------------------


def render_reception_body(reception: Reception, lang: str = "uz") -> dict[str, str]:
    """Return each renderable block of a reception as a dict of strings.

    Keys: ``complaints``, ``anamnesis``, ``lor_status``, ``diagnosis``, ``recommendation``.
    """
    return {
        "complaints": render_complaints(
            reception.complaints_codes,
            reception.complaints_details,
            reception.complaints_note,
            lang,
        ),
        "anamnesis": (reception.anamnesis or "").strip(),
        "lor_status": render_lor_status(reception.lor_status, lang),
        "diagnosis": (reception.diagnosis or "").strip(),
        "recommendation": (reception.recommendation or "").strip(),
    }
