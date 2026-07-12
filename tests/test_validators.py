"""Unit tests for :mod:`clinic.infrastructure.validators`."""

from __future__ import annotations

import pytest

from clinic.infrastructure.validators import (
    ValidationError,
    validate_birth_year,
    validate_complaints,
    validate_diagnosis,
    validate_doctor_selected,
    validate_full_name,
    validate_phone,
)

# ----- full_name -----


class TestFullName:
    def test_valid_name(self) -> None:
        assert validate_full_name("Aliyev Anvar") == "Aliyev Anvar"

    def test_collapses_whitespace(self) -> None:
        assert validate_full_name("  Aliyev    Anvar  ") == "Aliyev Anvar"

    def test_cyrillic(self) -> None:
        assert validate_full_name("Иванов Иван") == "Иванов Иван"

    def test_apostrophe_allowed(self) -> None:
        assert validate_full_name("O'zbekov Ali") == "O'zbekov Ali"

    def test_hyphen_allowed(self) -> None:
        assert validate_full_name("Aliyev-Karim Anvar") == "Aliyev-Karim Anvar"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_full_name("")
        assert "full_name" in exc.value.errors
        assert exc.value.errors["full_name"].message_key == "validation.required"

    def test_too_short_raises(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_full_name("Ali")
        assert exc.value.errors["full_name"].message_key == "validation.min_length"

    def test_bad_chars_raises(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_full_name("Anvar123 Aliyev")
        assert exc.value.errors["full_name"].message_key == "validation.name_chars"


# ----- birth_year -----


class TestBirthYear:
    def test_valid(self) -> None:
        assert validate_birth_year(1990) == 1990

    def test_string_coercion(self) -> None:
        assert validate_birth_year("1985") == 1985

    def test_below_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_birth_year(1899)

    def test_above_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_birth_year(3000)

    def test_missing_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_birth_year(None)

    def test_gibberish_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_birth_year("abc")


# ----- phone -----


class TestPhone:
    def test_valid_uzbek(self) -> None:
        assert validate_phone("+998901234567") == "+998901234567"

    def test_strips_spaces_and_dashes(self) -> None:
        assert validate_phone("+998 90 - 123 - 45 - 67") == "+998901234567"

    def test_empty_optional_returns_none(self) -> None:
        assert validate_phone("") is None

    def test_empty_required_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_phone("", required=True)

    def test_missing_plus_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_phone("998901234567")

    def test_letters_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_phone("+998abc")


# ----- diagnosis -----


class TestDiagnosis:
    def test_valid(self) -> None:
        assert validate_diagnosis("Otitis media") == "Otitis media"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_diagnosis("")

    def test_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_diagnosis("Ot")


# ----- complaints -----


class TestComplaints:
    def test_has_code(self) -> None:
        validate_complaints(["ear_pain"], None)

    def test_has_note_only(self) -> None:
        validate_complaints([], "some note")

    def test_both_empty_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_complaints([], "")

    def test_whitespace_note_treated_as_empty(self) -> None:
        with pytest.raises(ValidationError):
            validate_complaints([], "   \n\t")


# ----- doctor_selected -----


class TestDoctorSelected:
    def test_valid(self) -> None:
        assert validate_doctor_selected(1) == 1

    def test_none_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_doctor_selected(None)
