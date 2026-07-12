"""Tests for :mod:`clinic.printing.text_composer`."""

from __future__ import annotations

from clinic.printing.text_composer import compose_complaints, compose_lor_status

# ============================================================
# compose_complaints
# ============================================================


def test_complaints_empty_returns_empty_string() -> None:
    assert compose_complaints([], None, None) == ""


def test_complaints_note_only() -> None:
    text = compose_complaints([], None, "quloqda og'riq bor")
    assert "Qo'shimcha" in text
    assert "quloqda og'riq bor" in text


def test_complaints_single_code_uz() -> None:
    text = compose_complaints(["ear_pain"], None, None, lang="uz")
    assert text.startswith("Bemor quyidagilarga shikoyat qiladi")
    assert "quloqda og'riq" in text.lower()


def test_complaints_single_code_ru() -> None:
    text = compose_complaints(["ear_pain"], None, None, lang="ru")
    assert "Пациент" in text
    assert "боль в ухе" in text.lower()


def test_complaints_with_discharge_detail() -> None:
    text = compose_complaints(
        ["ear_discharge"], {"ear_discharge": "purulent"}, None, lang="uz"
    )
    assert "(yiringli)" in text.lower()


def test_complaints_with_note_and_codes() -> None:
    text = compose_complaints(
        ["ear_pain", "nose_congestion"],
        None,
        "3 kundan beri",
        lang="uz",
    )
    assert "quloqda og'riq" in text.lower()
    assert "burun bitishi" in text.lower()
    assert "Qo'shimcha: 3 kundan beri" in text


def test_complaints_unknown_code_ignored() -> None:
    text = compose_complaints(["totally_bogus"], None, None, lang="uz")
    assert text == ""


# ============================================================
# compose_lor_status
# ============================================================


def test_lor_empty_returns_empty() -> None:
    assert compose_lor_status(None) == ""
    assert compose_lor_status({}) == ""


def test_lor_rhinoscopy_basic() -> None:
    data = {
        "rhinoscopy": {
            "external_nose": {"state": "unchanged"},
            "breathing": {"state": "free"},
        }
    }
    text = compose_lor_status(data, lang="uz")
    assert "LOR STATUS" in text
    assert "RINOSKOPIYA" in text
    assert "O'zgarmagan" in text
    assert "Erkin" in text


def test_lor_otoscopy_per_ear_rendering() -> None:
    data = {
        "otoscopy": {
            "AD": {
                "auricle_canal": {"shape": "normal", "canal_width": "normal"},
                "tympanic_membrane": {"color": "pearly_gray", "perforation": "none"},
            },
            "AS": {
                "auricle_canal": {"shape": "normal", "canal_width": "normal"},
                "tympanic_membrane": {"color": "hyperemic", "perforation": "central"},
                "tympanic_cavity": {"contents": ["pus"]},
            },
        }
    }
    text = compose_lor_status(data, lang="uz")
    assert "OTOSKOPIYA" in text
    assert "AD" in text
    assert "AS" in text
    # AS-only tympanic cavity section (perforation != none)
    assert "yiring" in text.lower()


def test_lor_visible_when_hides_field() -> None:
    """A field whose gating value does NOT match should not appear in prose."""
    # deformity_type only visible when state == "deformed"
    data = {
        "rhinoscopy": {
            "external_nose": {"state": "unchanged", "deformity_type": ["hump"]},
        }
    }
    text = compose_lor_status(data, lang="uz")
    # "Bukrilik" should not appear because state is 'unchanged'
    assert "bukrilik" not in text.lower()
    assert "O'zgarmagan" in text


def test_lor_ru_language() -> None:
    data = {
        "rhinoscopy": {"breathing": {"state": "free"}},
    }
    text = compose_lor_status(data, lang="ru")
    assert "ЛОР СТАТУС" in text
    assert "РИНОСКОПИЯ" in text
    assert "Свободное" in text
