"""Convert Uzbek Latin values to Uzbek Cyrillic across the entire codebase.

Applied to:
- ``src/clinic/i18n/uz.json`` — every value
- ``src/clinic/catalogs/complaints.json`` — every ``uz`` field
- ``src/clinic/catalogs/lor_status.json`` — every ``uz`` field EXCEPT the
  phrase ``LOR STATUS`` which is preserved in Latin (medical shorthand).
- ``src/clinic/catalogs/address.json`` — every ``uz`` field

Transliteration rules (Uzbek modern Cyrillic):

Longest match wins. Ordered patterns:
    o'      -> ў
    g'      -> ғ
    sh      -> ш
    ch      -> ч
    yo      -> ё          (only when NOT followed by ``'``; ``yo'`` is y + o' → йў)
    ya      -> я
    yu      -> ю
    ye      -> е
    ng      -> нг         (kept as two chars — Cyrillic Uzbek writes 'нг')
Then single characters:
    a→а b→б d→д e→е f→ф g→г h→ҳ i→и j→ж k→к l→л m→м n→н o→о p→п q→қ
    r→р s→с t→т u→у v→в x→х y→й z→з
Apostrophe policy:
    * ``'`` between consonants or after a vowel where it marks glottal stop
      → ъ (yer belgisi)  — applied only if the preceding letter is a Uzbek
      vowel/consonant and the following letter is also a letter. This handles
      ``ma'lumot`` → ``маълумот``.

Preserved (never transliterated):
- ``{placeholder}`` tokens
- HTML tags ``<...>``
- URLs ``http(s)://...``
- Wildcards like ``*.docx``
- Standalone technical tokens: SQLite, Word, LOR, HTTP, HTTPS, PDF, JSON, XML, DB
- All already-Cyrillic characters
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UZ_JSON = ROOT / "src" / "clinic" / "i18n" / "uz.json"

# ---------------------------------------------------------------------------
# Transliteration rules — longest first.
# ---------------------------------------------------------------------------

# Multi-char rules processed at each position in longest-first order.
MULTI_RULES: tuple[tuple[str, str], ...] = (
    ("o'", "ў"), ("O'", "Ў"),
    ("o\u2018", "ў"), ("O\u2018", "Ў"),
    ("o\u2019", "ў"), ("O\u2019", "Ў"),
    ("g'", "ғ"), ("G'", "Ғ"),
    ("g\u2018", "ғ"), ("G\u2018", "Ғ"),
    ("g\u2019", "ғ"), ("G\u2019", "Ғ"),
    ("Sh", "Ш"), ("SH", "Ш"), ("sh", "ш"),
    ("Ch", "Ч"), ("CH", "Ч"), ("ch", "ч"),
    ("Yo", "Ё"), ("YO", "Ё"), ("yo", "ё"),
    ("Ya", "Я"), ("YA", "Я"), ("ya", "я"),
    ("Yu", "Ю"), ("YU", "Ю"), ("yu", "ю"),
    ("Ye", "Е"), ("YE", "Е"), ("ye", "е"),
)

SINGLE_MAP: dict[str, str] = {
    "a": "а", "b": "б", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "ҳ",
    "i": "и", "j": "ж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о",
    "p": "п", "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в",
    "x": "х", "y": "й", "z": "з",
    "A": "А", "B": "Б", "D": "Д", "E": "Е", "F": "Ф", "G": "Г", "H": "Ҳ",
    "I": "И", "J": "Ж", "K": "К", "L": "Л", "M": "М", "N": "Н", "O": "О",
    "P": "П", "Q": "Қ", "R": "Р", "S": "С", "T": "Т", "U": "У", "V": "В",
    "X": "Х", "Y": "Й", "Z": "З",
}

CYRILLIC_LOWER = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюяўғқҳ")
CYRILLIC_UPPER = {c.upper() for c in CYRILLIC_LOWER}
CYRILLIC = CYRILLIC_LOWER | CYRILLIC_UPPER
LATIN_LOWER = set("abcdefghijklmnopqrstuvwxyz")
LATIN = LATIN_LOWER | {c.upper() for c in LATIN_LOWER}

# Standalone tokens (word-boundary matched) that stay in Latin form.
KEEP_TOKENS = frozenset({
    "LOR", "LOR STATUS", "SQLite", "Word", "HTTP", "HTTPS", "PDF", "JSON",
    "XML", "URL", "SQL", "DB", "CSV", "PNG", "JPG", "JPEG", "GIF", "SVG",
    "CSS", "HTML", "JS", "API", "REST", "UI", "UX", "M1", "M2", "M3", "M4",
    "M5", "AD", "AS", "TLS", "LAN", "OS",
})

# Protected substring patterns — regex slots that keep their content verbatim.
PROTECTED_RE = re.compile(
    r"""(
        \{[^}]+\}                              # {placeholder}
        | <[^>]+>                              # <html tag>
        | https?://\S+                         # URL
        | \*\.\w+                              # *.docx wildcard
        | \b(?:                                # KEEP_TOKENS word-boundary
            LOR\ STATUS
            | SQLite | Word | LOR | HTTP | HTTPS | PDF | JSON | XML | URL
            | SQL | DB | CSV | PNG | JPG | JPEG | GIF | SVG | CSS | HTML
            | JS | API | REST | UI | UX | M[1-5] | AD | AS | TLS | LAN | OS
          )\b
    )""",
    re.VERBOSE,
)


_APOSTROPHES = "'\u2018\u2019"


def _try_multi_at(text: str, pos: int) -> tuple[str, int] | None:
    """Return (replacement, consumed) if any multi-char rule matches at ``pos``.

    Special case: ``yo/ya/yu/ye`` are NOT matched when the next character is
    an apostrophe — that pattern means ``y + o'`` (two separate letters:
    ``й`` + ``ў``) rather than the combined vowel ``ё``.
    """
    for src, dst in MULTI_RULES:
        if not text.startswith(src, pos):
            continue
        if src.lower() in {"yo", "ya", "yu", "ye"}:
            next_pos = pos + len(src)
            if next_pos < len(text) and text[next_pos] in _APOSTROPHES:
                continue
        return dst, len(src)
    return None


def _apostrophe_becomes_yer(text: str, pos: int) -> bool:
    """Decide whether ``'`` at ``pos`` should become ``ъ`` (Cyrillic yer).

    Rule of thumb: the apostrophe as a glottal-stop marker sits between two
    letters (either Latin or already Cyrillic). If the previous letter is
    ``o`` or ``g`` we skip — that's already the ``o'``/``g'`` case handled
    by MULTI_RULES.
    """
    if pos == 0 or pos + 1 >= len(text):
        return False
    prev = text[pos - 1]
    nxt = text[pos + 1]
    if prev in {"o", "O", "g", "G"}:
        return False
    return (prev in LATIN or prev in CYRILLIC) and (nxt in LATIN or nxt in CYRILLIC)


def transliterate_segment(text: str) -> str:
    """Transliterate a Latin-Uzbek segment to Cyrillic (best-effort)."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        # Skip already-Cyrillic characters unchanged.
        if text[i] in CYRILLIC:
            out.append(text[i])
            i += 1
            continue

        multi = _try_multi_at(text, i)
        if multi is not None:
            dst, consumed = multi
            out.append(dst)
            i += consumed
            continue

        ch = text[i]
        if ch in {"'", "\u2018", "\u2019"}:
            if _apostrophe_becomes_yer(text, i):
                out.append("ъ")
            else:
                out.append(ch)
            i += 1
            continue

        out.append(SINGLE_MAP.get(ch, ch))
        i += 1
    return "".join(out)


def transliterate(value: str) -> str:
    """Convert a JSON-value-like string to Cyrillic, keeping protected parts."""
    if not isinstance(value, str) or not value:
        return value
    pieces: list[str] = []
    cursor = 0
    for m in PROTECTED_RE.finditer(value):
        start, end = m.start(), m.end()
        if start > cursor:
            pieces.append(transliterate_segment(value[cursor:start]))
        pieces.append(value[start:end])  # verbatim
        cursor = end
    if cursor < len(value):
        pieces.append(transliterate_segment(value[cursor:]))
    return "".join(pieces)


# ---------------------------------------------------------------------------
# File processors
# ---------------------------------------------------------------------------


def convert_json_file(path: Path, *, walk_keys: str | None = None) -> int:
    """Rewrite ``path`` in place; return the number of leaf string values changed.

    - When ``walk_keys`` is None (i.e. flat dict of str→str), every value is
      transliterated.
    - When ``walk_keys`` is a JSON pointer-ish selector like ``"uz"``, we
      recursively walk the structure and only transliterate values whose key
      matches ``walk_keys`` (typical for catalog files with nested ``name``
      and ``uz``/``ru`` bilingual maps).
    """
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    changed = 0

    def _walk(node):
        nonlocal changed
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if walk_keys is None:
                    if isinstance(v, str):
                        new = transliterate(v)
                        if new != v:
                            node[k] = new
                            changed += 1
                    else:
                        _walk(v)
                else:
                    if k == walk_keys and isinstance(v, str):
                        new = transliterate(v)
                        if new != v:
                            node[k] = new
                            changed += 1
                    else:
                        _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(data)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return changed


def convert_uz_json() -> int:
    """uz.json is flat key→value — every value goes through transliterate()."""
    with UZ_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)
    changed = 0
    for k, v in data.items():
        new = transliterate(v)
        if new != v:
            data[k] = new
            changed += 1
    with UZ_JSON.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return changed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


CATALOGS_DIR = ROOT / "src" / "clinic" / "catalogs"


def main() -> None:
    tot = 0
    n = convert_uz_json()
    print(f"uz.json:            {n:>4d} values updated")
    tot += n

    n = convert_json_file(CATALOGS_DIR / "complaints.json", walk_keys="uz")
    print(f"complaints.json:    {n:>4d} uz values updated")
    tot += n

    n = convert_json_file(CATALOGS_DIR / "lor_status.json", walk_keys="uz")
    print(f"lor_status.json:    {n:>4d} uz values updated")
    tot += n

    address_path = CATALOGS_DIR / "address.json"
    if address_path.is_file():
        n = convert_json_file(address_path, walk_keys="uz")
        print(f"address.json:       {n:>4d} uz values updated")
        tot += n

    print(f"\nTotal:              {tot:>4d} strings converted")


if __name__ == "__main__":
    main()
