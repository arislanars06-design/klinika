"""Reusable input validators for the domain and presentation layers.

Validators raise :class:`ValidationError` which carries structured field-level
error information. UI code can convert these to localized messages via
``clinic.i18n.translator.t()``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime

# ============================================================================
# Error type
# ============================================================================


@dataclass
class FieldError:
    """A single validation failure tied to a form field."""

    field: str
    message_key: str  # e.g. "validation.required"
    params: Mapping[str, str | int] = field(default_factory=dict)


class ValidationError(Exception):
    """Raised when one or more fields fail validation.

    ``errors`` maps ``field_name`` → :class:`FieldError`. When multiple errors
    exist for the same field, only the first is kept — the UI shows one message
    per field anyway.
    """

    def __init__(self, errors: Iterable[FieldError] | None = None) -> None:
        self.errors: dict[str, FieldError] = {}
        if errors:
            for err in errors:
                self.errors.setdefault(err.field, err)
        super().__init__(self._summary())

    def add(self, field: str, message_key: str, **params: str | int) -> None:
        self.errors.setdefault(field, FieldError(field, message_key, dict(params)))

    def __bool__(self) -> bool:
        return bool(self.errors)

    def _summary(self) -> str:
        if not self.errors:
            return "ValidationError"
        return "; ".join(f"{k}:{e.message_key}" for k, e in self.errors.items())


# ============================================================================
# Regexes / constants
# ============================================================================

# Letters (Latin + Cyrillic + apostrophes) plus internal spaces
_NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳ' \-]+$")
# +998 XX XXX XX XX and similar; 9..15 digits after the leading '+'
_PHONE_RE = re.compile(r"^\+\d{9,15}$")

MIN_NAME_LENGTH = 5
MIN_DIAGNOSIS_LENGTH = 3
MIN_BIRTH_YEAR = 1900


def _current_year() -> int:
    return datetime.now().year


# ============================================================================
# Individual validators
# ============================================================================


def validate_full_name(name: str, *, field_name: str = "full_name") -> str:
    """Return the normalized name or raise ``ValidationError``.

    Trims surrounding whitespace, collapses internal runs to a single space.
    Enforces minimum length and allowed characters.
    """
    err = ValidationError()
    if not name or not name.strip():
        err.add(field_name, "validation.required")
        raise err

    normalized = re.sub(r"\s+", " ", name.strip())
    if len(normalized) < MIN_NAME_LENGTH:
        err.add(field_name, "validation.min_length", n=MIN_NAME_LENGTH)
        raise err
    if not _NAME_RE.match(normalized):
        err.add(field_name, "validation.name_chars")
        raise err
    return normalized


def validate_birth_year(
    year: int | str | None,
    *,
    field_name: str = "birth_year",
) -> int:
    err = ValidationError()
    if year is None or (isinstance(year, str) and not year.strip()):
        err.add(field_name, "validation.required")
        raise err

    try:
        year_int = int(year)
    except (TypeError, ValueError):
        err.add(
            field_name,
            "validation.year_range",
            min=MIN_BIRTH_YEAR,
            max=_current_year(),
        )
        raise err from None

    if year_int < MIN_BIRTH_YEAR or year_int > _current_year():
        err.add(
            field_name,
            "validation.year_range",
            min=MIN_BIRTH_YEAR,
            max=_current_year(),
        )
        raise err
    return year_int


def validate_phone(
    phone: str | None,
    *,
    field_name: str = "phone",
    required: bool = False,
) -> str | None:
    """Return the normalized phone (or ``None`` if empty and optional)."""
    if phone is None or not phone.strip():
        if required:
            err = ValidationError()
            err.add(field_name, "validation.required")
            raise err
        return None

    # Strip whitespace, dashes, parens; keep leading '+'
    cleaned = re.sub(r"[\s\-()]", "", phone.strip())
    if not _PHONE_RE.match(cleaned):
        err = ValidationError()
        err.add(field_name, "validation.phone_format")
        raise err
    return cleaned


def validate_diagnosis(text: str, *, field_name: str = "diagnosis") -> str:
    err = ValidationError()
    if not text or not text.strip():
        err.add(field_name, "validation.required")
        raise err

    normalized = text.strip()
    if len(normalized) < MIN_DIAGNOSIS_LENGTH:
        err.add(field_name, "validation.min_length", n=MIN_DIAGNOSIS_LENGTH)
        raise err
    return normalized


def validate_complaints(
    codes: list[str],
    note: str | None,
    *,
    field_name: str = "complaints",
) -> None:
    """At least one code selected or a non-empty note is required."""
    has_codes = bool(codes)
    has_note = bool(note and note.strip())
    if not (has_codes or has_note):
        err = ValidationError()
        err.add(field_name, "validation.complaints_required")
        raise err


def validate_doctor_selected(
    doctor_id: int | None,
    *,
    field_name: str = "doctor",
) -> int:
    err = ValidationError()
    if doctor_id is None:
        err.add(field_name, "validation.required")
        raise err
    return doctor_id


# ============================================================================
# Composite helper
# ============================================================================


def collect_errors(*validators) -> ValidationError:  # type: ignore[no-untyped-def]
    """Run each zero-arg validator, collecting failures into one exception.

    Each argument should be a ``functools.partial`` (or lambda) that either
    returns a normalized value or raises ``ValidationError``. Returns a
    (possibly empty) ``ValidationError`` — the caller decides whether to raise.
    """
    combined = ValidationError()
    for v in validators:
        try:
            v()
        except ValidationError as ve:
            for name, e in ve.errors.items():
                combined.errors.setdefault(name, e)
    return combined


__all__ = [
    "MIN_BIRTH_YEAR",
    "MIN_DIAGNOSIS_LENGTH",
    "MIN_NAME_LENGTH",
    "FieldError",
    "ValidationError",
    "collect_errors",
    "validate_birth_year",
    "validate_complaints",
    "validate_diagnosis",
    "validate_doctor_selected",
    "validate_full_name",
    "validate_phone",
]
