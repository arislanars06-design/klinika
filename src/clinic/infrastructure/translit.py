"""Uzbek Latin ↔ Cyrillic transliteration.

Used to make patient / diagnosis search cross-alphabet: whichever script the
operator types in, the query is expanded to include the other so that
"Aliyev" also finds "Алиев" and vice versa.

The rules are intentionally lossy — they aim for high recall on names, not
perfect round-trip fidelity. Common Uzbek names (both Latin and Cyrillic) go
through cleanly; anything that doesn't map is left as-is.
"""

from __future__ import annotations

# Ordered longest-first so multigraphs (``sh``, ``ch``, ``yo``, …) win over
# their first character.
_LAT_TO_CYR: tuple[tuple[str, str], ...] = (
    ("O'", "Ў"), ("o'", "ў"),
    ("G'", "Ғ"), ("g'", "ғ"),
    ("Sh", "Ш"), ("sh", "ш"), ("SH", "Ш"),
    ("Ch", "Ч"), ("ch", "ч"), ("CH", "Ч"),
    ("Yo", "Ё"), ("yo", "ё"), ("YO", "Ё"),
    ("Yu", "Ю"), ("yu", "ю"), ("YU", "Ю"),
    ("Ya", "Я"), ("ya", "я"), ("YA", "Я"),
    ("Ye", "Е"), ("ye", "е"), ("YE", "Е"),
    ("Ts", "Ц"), ("ts", "ц"), ("TS", "Ц"),
    ("Zh", "Ж"), ("zh", "ж"), ("ZH", "Ж"),
    ("Kh", "Х"), ("kh", "х"), ("KH", "Х"),
    ("A", "А"), ("a", "а"),
    ("B", "Б"), ("b", "б"),
    ("D", "Д"), ("d", "д"),
    ("E", "Е"), ("e", "е"),
    ("F", "Ф"), ("f", "ф"),
    ("G", "Г"), ("g", "г"),
    ("H", "Ҳ"), ("h", "ҳ"),
    ("I", "И"), ("i", "и"),
    ("J", "Ж"), ("j", "ж"),
    ("K", "К"), ("k", "к"),
    ("L", "Л"), ("l", "л"),
    ("M", "М"), ("m", "м"),
    ("N", "Н"), ("n", "н"),
    ("O", "О"), ("o", "о"),
    ("P", "П"), ("p", "п"),
    ("Q", "Қ"), ("q", "қ"),
    ("R", "Р"), ("r", "р"),
    ("S", "С"), ("s", "с"),
    ("T", "Т"), ("t", "т"),
    ("U", "У"), ("u", "у"),
    ("V", "В"), ("v", "в"),
    ("X", "Х"), ("x", "х"),
    ("Y", "Й"), ("y", "й"),
    ("Z", "З"), ("z", "з"),
    ("'", "ъ"),
)

_CYR_TO_LAT: tuple[tuple[str, str], ...] = (
    ("Ў", "O'"), ("ў", "o'"),
    ("Ғ", "G'"), ("ғ", "g'"),
    ("Ш", "Sh"), ("ш", "sh"),
    ("Ч", "Ch"), ("ч", "ch"),
    ("Ё", "Yo"), ("ё", "yo"),
    ("Ю", "Yu"), ("ю", "yu"),
    ("Я", "Ya"), ("я", "ya"),
    ("Ж", "J"),  ("ж", "j"),
    ("Ц", "Ts"), ("ц", "ts"),
    ("Щ", "Sh"), ("щ", "sh"),
    ("А", "A"), ("а", "a"),
    ("Б", "B"), ("б", "b"),
    ("В", "V"), ("в", "v"),
    ("Г", "G"), ("г", "g"),
    ("Д", "D"), ("д", "d"),
    ("Е", "E"), ("е", "e"),
    ("З", "Z"), ("з", "z"),
    ("И", "I"), ("и", "i"),
    ("Й", "Y"), ("й", "y"),
    ("К", "K"), ("к", "k"),
    ("Қ", "Q"), ("қ", "q"),
    ("Л", "L"), ("л", "l"),
    ("М", "M"), ("м", "m"),
    ("Н", "N"), ("н", "n"),
    ("О", "O"), ("о", "o"),
    ("П", "P"), ("п", "p"),
    ("Р", "R"), ("р", "r"),
    ("С", "S"), ("с", "s"),
    ("Т", "T"), ("т", "t"),
    ("У", "U"), ("у", "u"),
    ("Ф", "F"), ("ф", "f"),
    ("Х", "X"), ("х", "x"),
    ("Ҳ", "H"), ("ҳ", "h"),
    ("Ъ", "'"), ("ъ", "'"),
    ("Ь", ""),  ("ь", ""),
    ("Ы", "I"), ("ы", "i"),
    ("Э", "E"), ("э", "e"),
    # Latin already? keep the char.
)


def _apply(text: str, rules: tuple[tuple[str, str], ...]) -> str:
    if not text:
        return ""
    out = text
    for src, dst in rules:
        if src in out:
            out = out.replace(src, dst)
    return out


def latin_to_cyrillic(text: str) -> str:
    """Convert an Uzbek Latin string to Cyrillic (best-effort)."""
    return _apply(text, _LAT_TO_CYR)


def cyrillic_to_latin(text: str) -> str:
    """Convert an Uzbek Cyrillic string to Latin (best-effort)."""
    return _apply(text, _CYR_TO_LAT)


def _has_cyrillic(text: str) -> bool:
    return any("\u0400" <= ch <= "\u04FF" for ch in text)


def _has_latin(text: str) -> bool:
    return any(("a" <= ch <= "z") or ("A" <= ch <= "Z") for ch in text)


# Common Uzbek spelling: Cyrillic "и" before another vowel is often written
# with an intermediate 'y' in Latin ("Алиев" → "Aliyev", "Юсупов" → not
# affected, but "Ходиев" → "Xodiyev"). Generate the alternate.
_Y_INSERT_PATTERNS: tuple[tuple[str, str], ...] = (
    ("ie", "iye"), ("io", "iyo"), ("iu", "iyu"), ("ia", "iya"),
    ("Ie", "Iye"), ("Io", "Iyo"), ("Iu", "Iyu"), ("Ia", "Iya"),
    # Also aa → aya (rare, kept off for now)
)


def _y_insert(text: str) -> str:
    out = text
    for src, dst in _Y_INSERT_PATTERNS:
        out = out.replace(src, dst)
    return out


def _y_strip(text: str) -> str:
    """Reverse of ``_y_insert`` — collapse 'iye' → 'ie' etc.

    Used when the Latin input already contains a 'y' that a Cyrillic ↔ Latin
    naive translit would have omitted. Ensures both spellings match.
    """
    out = text
    for src, dst in _Y_INSERT_PATTERNS:
        # Reverse: replace the longer form with the shorter one.
        out = out.replace(dst, src)
    return out


def expand_variants(text: str) -> list[str]:
    """Return alternative script forms of ``text``.

    - Latin-only input →  [original, cyrillic, ``latin_without_y``]
    - Cyrillic-only    →  [original, latin, ``latin_with_y_inserted``]
    - Mixed / neither  →  [original] only

    The ``y``-variant handles the common Uzbek spelling divergence where
    Cyrillic "Алиев" is written "Aliyev" in Latin — both should be found by
    either query.
    """
    if not text or not text.strip():
        return []
    variants: list[str] = [text]
    is_cyr = _has_cyrillic(text)
    is_lat = _has_latin(text)
    if is_lat and not is_cyr:
        cyr = latin_to_cyrillic(text)
        if cyr and cyr != text:
            variants.append(cyr)
        stripped = _y_strip(text)
        if stripped and stripped != text:
            variants.append(stripped)
    elif is_cyr and not is_lat:
        lat = cyrillic_to_latin(text)
        if lat and lat != text:
            variants.append(lat)
            with_y = _y_insert(lat)
            if with_y != lat:
                variants.append(with_y)
    # De-duplicate while preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for v in variants:
        if v not in seen:
            out.append(v)
            seen.add(v)
    return out


__all__ = [
    "cyrillic_to_latin",
    "expand_variants",
    "latin_to_cyrillic",
]
