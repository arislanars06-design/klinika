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


def _method_indices(lang: str) -> dict[str, dict[str, Any]]:
    """Return a per-method index that maps section codes/field codes/option codes to labels."""
    catalog = lor_status_catalog()
    globals_labels: dict[str, str] = {}
    for row in catalog.get("sides", ()):
        globals_labels[row["code"]] = row[lang]
    for row in catalog.get("degrees", ()):
        globals_labels[row["code"]] = row[lang]

    indices: dict[str, dict[str, Any]] = {}
    for method in catalog.get("methods", []):
        m_idx: dict[str, Any] = {
            "name": method["name"][lang],
            "per_ear": method.get("per_ear", False),
            "ears": {row["code"]: row[lang] for row in method.get("ears", ())},
            "sections": {},
        }
        for section in method.get("sections", []):
            fields: dict[str, dict[str, str]] = {}
            for field in section.get("fields", []):
                options: dict[str, str] = {}
                for opt in field.get("options", ()):
                    options[opt["code"]] = opt[lang]
                fields[field["code"]] = options
            m_idx["sections"][section["code"]] = {
                "name": section["name"][lang],
                "fields": fields,
            }
        indices[method["code"]] = m_idx

    indices["_globals"] = globals_labels
    return indices


def _humanize_value(
    value: Any,
    field_options: dict[str, str],
    globals_labels: dict[str, str],
) -> str:
    """Turn a code (or list of codes) into a comma-separated human label."""
    if isinstance(value, list):
        return ", ".join(
            field_options.get(v, globals_labels.get(v, str(v))) for v in value
        )
    return field_options.get(value, globals_labels.get(value, str(value)))


def _format_section(
    section_label: str,
    section_data: dict[str, Any],
    section_meta: dict[str, Any],
    globals_labels: dict[str, str],
) -> str | None:
    """Render one anatomical section as ``Label: field1=v; field2=v``."""
    if not isinstance(section_data, dict) or not section_data:
        return None

    fields_meta = section_meta.get("fields", {})
    fragments: list[str] = []
    for field_code, value in section_data.items():
        if value in (None, "", []):
            continue
        pretty = _humanize_value(value, fields_meta.get(field_code, {}), globals_labels)
        fragments.append(pretty)

    if not fragments:
        return None
    return f"{section_label}: " + ", ".join(fragments) + "."


def render_lor_status(status: dict[str, Any] | None, lang: str = "uz") -> str:
    """Render LOR STATUS dict into plain, doctor-friendly text.

    Handles three input shapes:

    * ``{"text": "…"}`` — free-form fallback, returned as-is.
    * ``{"rhinoscopy": {"section": {"field": "value"}, …}, …}`` — structured.
    * ``{"otoscopy": {"AD": {…}, "AS": {…}}, …}`` — per-ear otoscopy.
    """
    if not status:
        return ""

    indices = _method_indices(lang)
    globals_labels = indices.get("_globals", {})

    method_blocks: list[str] = []

    for method_code, method_data in status.items():
        if method_code == "text":
            continue
        method_meta = indices.get(method_code)
        if not method_meta or not isinstance(method_data, dict):
            continue

        section_metas = method_meta["sections"]
        header = method_meta["name"]

        if method_meta.get("per_ear"):
            ear_lines: list[str] = []
            for ear_code, ear_label in method_meta["ears"].items():
                ear_data = method_data.get(ear_code)
                if not isinstance(ear_data, dict) or not ear_data:
                    continue
                sections: list[str] = []
                for section_code, section_data in ear_data.items():
                    meta = section_metas.get(section_code)
                    if meta is None:
                        continue
                    line = _format_section(meta["name"], section_data, meta, globals_labels)
                    if line:
                        sections.append(line)
                if sections:
                    ear_lines.append(f"  {ear_label}: " + " ".join(sections))
            if ear_lines:
                method_blocks.append(header + ":\n" + "\n".join(ear_lines))
            continue

        sections: list[str] = []
        for section_code, section_data in method_data.items():
            meta = section_metas.get(section_code)
            if meta is None:
                continue
            line = _format_section(meta["name"], section_data, meta, globals_labels)
            if line:
                sections.append(line)
        if sections:
            method_blocks.append(f"{header}: " + " ".join(sections))

    body = "\n\n".join(method_blocks)

    # Append the free-form fallback text if present.
    text = str(status.get("text", "")).strip()
    if text:
        body = f"{body}\n\n{text}" if body else text
    return body


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
