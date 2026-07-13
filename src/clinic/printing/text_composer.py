"""Turn structured selections (checkboxes, radios) into medical prose.

Used both by the Reception window's real-time preview and later by the Word
export step so the two always agree.

Two entry points:

* :func:`compose_complaints` — flat list of complaint codes + optional discharge
  types + freeform note.
* :func:`compose_lor_status` — the four-method LOR STATUS dictionary produced
  by :class:`clinic.ui.reception.lor_status_widget.LorStatusWidget`.
"""

from __future__ import annotations

from collections.abc import Iterable

from clinic.domain.catalog_loader import (
    complaints_catalog,
    discharge_types_catalog,
    lor_status_catalog,
)

# ============================================================================
# Public helpers
# ============================================================================


def _localized(entry: dict, key: str, lang: str) -> str:
    """Look up ``lang`` in ``entry[key]`` (or ``entry[f'{key}_{lang}']``)."""
    nested = entry.get(key)
    if isinstance(nested, dict):
        return str(nested.get(lang) or nested.get("uz") or "")
    return str(entry.get(f"{key}_{lang}") or entry.get(f"{key}_uz") or "")


def _find_option(field: dict, code: str) -> dict | None:
    for option in field.get("options", []) or []:
        if option.get("code") == code:
            return option
    return None


def _index_complaints(lang: str) -> dict[str, str]:
    """Return ``{item_code: localized_label}`` for all built-in complaints."""
    catalog = complaints_catalog()
    result: dict[str, str] = {}
    for section in catalog.get("sections", []):
        for item in section.get("items", []):
            label = item.get(lang) or item.get("uz") or ""
            result[item["code"]] = label
    return result


def _index_discharge_types(lang: str) -> dict[str, str]:
    catalog = discharge_types_catalog()
    return {
        item["code"]: (item.get(lang) or item.get("uz") or "")
        for item in catalog.get("types", [])
    }


# ============================================================================
# Complaints prose
# ============================================================================


COMPLAINTS_INTRO = {
    "uz": "Бемор қуйидагиларга шикоят қилади",
    "ru": "Пациент предъявляет жалобы на",
}
COMPLAINTS_ADDITIONAL = {
    "uz": "Қўшимча",
    "ru": "Дополнительно",
}


def compose_complaints(
    codes: Iterable[str],
    details: dict[str, str] | None,
    note: str | None,
    *,
    lang: str = "uz",
) -> str:
    """Return a natural-language sentence summarising the complaint selection."""
    codes = list(codes or [])
    details = details or {}
    labels = _index_complaints(lang)
    discharge = _index_discharge_types(lang)

    parts: list[str] = []
    for code in codes:
        base = labels.get(code)
        if not base:
            continue
        detail_code = details.get(code)
        if detail_code:
            detail_label = discharge.get(detail_code, detail_code)
            # e.g. "quloqdan ajralma (yiringli)"
            parts.append(f"{base.lower()} ({detail_label.lower()})")
        else:
            parts.append(base.lower())

    sentences: list[str] = []
    if parts:
        intro = COMPLAINTS_INTRO.get(lang, COMPLAINTS_INTRO["uz"])
        sentences.append(f"{intro}: {', '.join(parts)}.")

    note_clean = (note or "").strip()
    if note_clean:
        prefix = COMPLAINTS_ADDITIONAL.get(lang, COMPLAINTS_ADDITIONAL["uz"])
        sentences.append(f"{prefix}: {note_clean}")

    return " ".join(sentences).strip()


# ============================================================================
# LOR STATUS prose
# ============================================================================


LOR_INTRO = {"uz": "LOR STATUS", "ru": "ЛОР СТАТУС"}


def _label_for_option(field: dict, code: str, lang: str) -> str:
    opt = _find_option(field, code)
    if opt is None:
        return ""
    return str(opt.get(lang) or opt.get("uz") or code)


def _label_for_side(catalog: dict, code: str, lang: str) -> str:
    for side in catalog.get("sides", []):
        if side.get("code") == code:
            return str(side.get(lang) or side.get("uz") or code)
    return code


def _label_for_degree(catalog: dict, code: str, lang: str) -> str:
    for degree in catalog.get("degrees", []):
        if degree.get("code") == code:
            return str(degree.get(lang) or degree.get("uz") or code)
    return code


def _render_field(
    catalog: dict,
    field: dict,
    value,
    lang: str,
) -> str:
    """Render one field value into a short human phrase."""
    if value is None or value == "" or value == []:
        return ""

    ftype = field.get("type")

    if ftype == "radio":
        return _label_for_option(field, value, lang)

    if ftype in {"checkbox_multi"}:
        if not isinstance(value, list):
            return ""
        return ", ".join(
            filter(None, (_label_for_option(field, v, lang).lower() for v in value))
        )

    if ftype == "checkbox":
        if not value:
            return ""
        label = field.get("label", {})
        return str(label.get(lang) or label.get("uz") or "")

    if ftype == "side":
        return _label_for_side(catalog, value, lang).lower()

    if ftype == "degree":
        return _label_for_degree(catalog, value, lang)

    if ftype == "text":
        return str(value).strip()

    return ""


def _render_section(
    catalog: dict,
    section: dict,
    section_value: dict,
    lang: str,
) -> str:
    """Assemble one section (e.g. 'Tashqi burun') into a sentence."""
    if not section_value:
        return ""

    pieces: list[str] = []
    for field in section.get("fields", []):
        code = field["code"]
        raw = section_value.get(code)
        # Respect visible_when — if the gating field's value doesn't match,
        # skip so we don't leak hidden data into the prose.
        vw = field.get("visible_when")
        if vw and not _visible_when_satisfied(vw, section_value):
            continue
        rendered = _render_field(catalog, field, raw, lang)
        if rendered:
            pieces.append(rendered)

    if not pieces:
        return ""

    name = section.get("name", {})
    label = str(name.get(lang) or name.get("uz") or section.get("code", ""))
    return f"{label}: {'; '.join(pieces)}."


def _visible_when_satisfied(rule: dict, current: dict) -> bool:
    """Return True when every ``{field: expected}`` pair matches the current values."""
    for key, expected in rule.items():
        actual = current.get(key)
        if isinstance(expected, list):
            if isinstance(actual, list):
                if not any(a in expected for a in actual):
                    return False
            elif actual not in expected:
                return False
        else:
            if isinstance(actual, list):
                if expected not in actual:
                    return False
            elif actual != expected:
                return False
    return True


def _render_method(catalog: dict, method: dict, method_value, lang: str) -> str:
    """Render a single otolaryngology method (rhinoscopy, otoscopy, ...)."""
    name = method.get("name", {})
    method_label = str(name.get(lang) or name.get("uz") or method.get("code", ""))

    # Free-text fallback (used by the web app's simplified LOR editor):
    # ``method_value`` may be a plain string. Emit it verbatim under the
    # method heading so both storage formats round-trip cleanly.
    if isinstance(method_value, str):
        text = method_value.strip()
        return f"{method_label}: {text}" if text else ""

    # Otoscopy stores per-ear dictionaries.
    if method.get("per_ear"):
        ear_labels = {e["code"]: (e.get(lang) or e.get("uz") or e["code"]) for e in method.get("ears", [])}
        lines: list[str] = [f"{method_label}:"]
        for ear in method.get("ears", []):
            code = ear["code"]
            ear_value = (method_value or {}).get(code, {})
            section_lines: list[str] = []
            for section in method.get("sections", []):
                if section.get("visible_when_perforation"):
                    perf = ear_value.get("tympanic_membrane", {}).get("perforation")
                    if perf in (None, "none"):
                        continue
                rendered = _render_section(catalog, section, ear_value.get(section["code"], {}), lang)
                if rendered:
                    section_lines.append("    " + rendered)
            if section_lines:
                lines.append(f"  {ear_labels.get(code, code)}:")
                lines.extend(section_lines)
        return "\n".join(lines) if len(lines) > 1 else ""

    section_lines: list[str] = []
    for section in method.get("sections", []):
        rendered = _render_section(catalog, section, (method_value or {}).get(section["code"], {}), lang)
        if rendered:
            section_lines.append(rendered)

    if not section_lines:
        return ""
    return f"{method_label}: " + " ".join(section_lines)


def compose_lor_status(lor_status: dict | None, *, lang: str = "uz") -> str:
    """Turn the LOR STATUS dictionary into a multi-paragraph string."""
    if not lor_status:
        return ""

    catalog = lor_status_catalog()
    intro = LOR_INTRO.get(lang, LOR_INTRO["uz"])
    blocks: list[str] = []

    # 1) Structured methods defined by the desktop catalog.
    known_codes = set()
    for method in catalog.get("methods", []):
        code = method["code"]
        known_codes.add(code)
        value = lor_status.get(code)
        payload = value if isinstance(value, str) else (value or {})
        rendered = _render_method(catalog, method, payload, lang)
        if rendered:
            blocks.append(rendered)

    # 2) Any extra free-text keys not defined in the catalog (e.g. the web
    # form uses shorter codes like ``rhinoscopy`` even when the catalog uses
    # richer sub-structures — future custom codes also land here).
    for code, value in lor_status.items():
        if code in known_codes:
            continue
        if isinstance(value, str) and value.strip():
            # Best-effort humanised label: title-case the code.
            heading = code.replace("_", " ").upper()
            blocks.append(f"{heading}: {value.strip()}")

    if not blocks:
        return ""
    return f"{intro}:\n\n" + "\n\n".join(blocks)


__all__ = ["compose_complaints", "compose_lor_status"]
