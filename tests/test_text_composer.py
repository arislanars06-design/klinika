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
    assert "Қўшимча" in text
    assert "quloqda og'riq bor" in text


def test_complaints_single_code_uz() -> None:
    text = compose_complaints(["ear_pain"], None, None, lang="uz")
    assert text.startswith("Бемор қуйидагиларга шикоят қилади")
    assert "қулоқда оғриқ" in text.lower()


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
    assert "қулоқда оғриқ" in text.lower()
    assert "бурун битиши" in text.lower()
    assert "Қўшимча: 3 kundan beri" in text or "Qo'shimcha: 3 kundan beri" in text


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
    # Default (renderer path) — no leading "LOR STATUS:" intro; callers
    # add their own section heading.
    text = compose_lor_status(data, lang="uz")
    assert "LOR STATUS" not in text  # intro no longer duplicated
    assert "РИНОСКОПИЯ" in text
    assert "Ўзгармаган" in text
    assert "Еркин" in text

    # Opt-in path — the desktop live-preview widget still needs the intro
    # because the surrounding label is generic.
    with_heading = compose_lor_status(data, lang="uz", include_heading=True)
    assert with_heading.startswith("LOR STATUS")
    assert "РИНОСКОПИЯ" in with_heading


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
    assert "ОТОСКОПИЯ" in text
    assert "AD" in text
    assert "AS" in text
    # AS-only tympanic cavity section (perforation != none)
    assert "йиринг" in text.lower()


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
    assert "букрилик" not in text.lower()
    assert "Ўзгармаган" in text


def test_lor_ru_language() -> None:
    data = {
        "rhinoscopy": {"breathing": {"state": "free"}},
    }
    # Renderer path — no intro.
    text = compose_lor_status(data, lang="ru")
    assert "ЛОР СТАТУС" not in text
    assert "РИНОСКОПИЯ" in text
    assert "Свободное" in text

    # Preview path — intro is re-added in Russian too.
    with_heading = compose_lor_status(data, lang="ru", include_heading=True)
    assert with_heading.startswith("ЛОР СТАТУС")
