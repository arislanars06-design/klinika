"""Convert uz.json values from Latin Uzbek to Cyrillic Uzbek.

Transliteration rules:
- Multi-char sequences (processed first): sh→ш, ch→ч, ng→нг, o'→ў, g'→ғ
- Single chars: a→а, b→б, d→д, e→е, f→ф, g→г, h→ҳ, i→и, j→ж, k→к,
  l→л, m→м, n→н, o→о, p→п, q→қ, r→р, s→с, t→т, u→у, v→в, x→х, y→й, z→з

Preserves:
- {placeholder} tokens unchanged
- Already-Cyrillic text unchanged
- HTML tags, URLs, CSS class names
- File extensions (.docx, .db, etc.)
- Technical keywords (LOR, Word, SQLite, etc.)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

UZ_JSON_PATH = Path(__file__).resolve().parent.parent / "src" / "clinic" / "i18n" / "uz.json"

# Multi-character mappings (order matters: longer sequences first)
MULTI_MAP_LOWER = [
    ("sh", "\u0448"),   # ш
    ("ch", "\u0447"),   # ч
    ("o\u2018", "\u045e"),  # o' → ў (with left single quote)
    ("o'", "\u045e"),   # o' → ў (with apostrophe)
    ("o\u2019", "\u045e"),  # o' → ў (with right single quote)
    ("g\u2018", "\u0493"),  # g' → ғ
    ("g'", "\u0493"),   # g' → ғ
    ("g\u2019", "\u0493"),  # g' → ғ
]

MULTI_MAP_UPPER = [
    ("Sh", "\u0428"),   # Ш
    ("SH", "\u0428"),
    ("Ch", "\u0427"),   # Ч
    ("CH", "\u0427"),
    ("O\u2018", "\u040E"),  # O' → Ў
    ("O'", "\u040E"),
    ("O\u2019", "\u040E"),
    ("G\u2018", "\u0492"),  # G' → Ғ
    ("G'", "\u0492"),
    ("G\u2019", "\u0492"),
]

# Single character mappings (lowercase)
SINGLE_MAP_LOWER = {
    'a': '\u0430',  # а
    'b': '\u0431',  # б
    'd': '\u0434',  # д
    'e': '\u0435',  # е
    'f': '\u0444',  # ф
    'g': '\u0433',  # г
    'h': '\u04B3',  # ҳ
    'i': '\u0438',  # и
    'j': '\u0436',  # ж
    'k': '\u043A',  # к
    'l': '\u043B',  # л
    'm': '\u043C',  # м
    'n': '\u043D',  # н
    'o': '\u043E',  # о
    'p': '\u043F',  # п
    'q': '\u049B',  # қ
    'r': '\u0440',  # р
    's': '\u0441',  # с
    't': '\u0442',  # т
    'u': '\u0443',  # у
    'v': '\u0432',  # в
    'x': '\u0445',  # х
    'y': '\u0439',  # й
    'z': '\u0437',  # з
}

SINGLE_MAP_UPPER = {k.upper(): v.upper() for k, v in SINGLE_MAP_LOWER.items()}


def is_cyrillic(ch: str) -> bool:
    """Check if a character is in a Cyrillic Unicode range."""
    code = ord(ch)
    return (0x0400 <= code <= 0x04FF) or (0x0500 <= code <= 0x052F)


def transliterate_segment(text: str) -> str:
    """Transliterate a Latin Uzbek text segment to Cyrillic."""
    if not text:
        return text

    result: list[str] = []
    i = 0
    length = len(text)

    while i < length:
        matched = False

        # Try multi-char mappings (upper first for case sensitivity)
        for src, dst in MULTI_MAP_UPPER + MULTI_MAP_LOWER:
            src_len = len(src)
            if i + src_len <= length and text[i:i + src_len] == src:
                result.append(dst)
                i += src_len
                matched = True
                break

        if matched:
            continue

        ch = text[i]

        # Skip already-Cyrillic characters
        if is_cyrillic(ch):
            result.append(ch)
            i += 1
            continue

        # Try single character mappings
        if ch in SINGLE_MAP_UPPER:
            result.append(SINGLE_MAP_UPPER[ch])
            i += 1
        elif ch in SINGLE_MAP_LOWER:
            result.append(SINGLE_MAP_LOWER[ch])
            i += 1
        else:
            # Keep as-is (digits, punctuation, whitespace, etc.)
            result.append(ch)
            i += 1

    return "".join(result)


def convert_value(value: str) -> str:
    """Convert a single JSON value from Latin Uzbek to Cyrillic.

    Preserves {placeholders}, HTML tags, URLs, and file extensions unchanged.
    """
    if not value:
        return value

    # Combined pattern for all tokens that should NOT be transliterated.
    protected_pattern = re.compile(
        r'\{[^}]+\}'        # {placeholders}
        r'|<[^>]+>'         # HTML tags
        r'|https?://\S+'    # URLs
        r'|\*\.\w+'         # wildcard file patterns like *.docx
        r'|\*\.\*'          # *.* pattern
        r'|\.(?:docx|db|old-)'  # specific file extensions
        r'|SQLite'          # proper noun
        r'|Word'            # proper noun
        r'|LOR'             # acronym
        r'|LOG'             # acronym
        r'|(?<!\w)X+(?!\w)' # standalone X sequences (phone format placeholders)
    )

    # Use finditer + slicing approach to separate protected tokens from text
    parts: list[str] = []
    last_end = 0
    for m in protected_pattern.finditer(value):
        start, end = m.start(), m.end()
        if start > last_end:
            parts.append(transliterate_segment(value[last_end:start]))
        parts.append(value[start:end])  # Keep protected token as-is
        last_end = end
    if last_end < len(value):
        parts.append(transliterate_segment(value[last_end:]))

    return "".join(parts)


def main() -> None:
    # First, read the ORIGINAL Latin uz.json (we need to re-read it fresh
    # from git if it was already converted in a prior run).
    import subprocess
    result = subprocess.run(
        ["git", "show", "HEAD:src/clinic/i18n/uz.json"],
        capture_output=True, text=True, cwd=str(UZ_JSON_PATH.parent.parent.parent.parent),
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
    else:
        # Fall back to reading the file as-is
        with open(UZ_JSON_PATH, encoding="utf-8") as f:
            data = json.load(f)

    converted: dict[str, str] = {}
    for key, value in data.items():
        converted[key] = convert_value(value)

    with open(UZ_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Converted {len(converted)} entries in {UZ_JSON_PATH}")


if __name__ == "__main__":
    main()
