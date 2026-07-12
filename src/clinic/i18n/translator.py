"""Lightweight i18n helper used by the web layer.

Loads JSON translation files on import and exposes a ``t()`` function that
accepts an optional ``lang`` override so it can be used from Jinja2 templates
and FastAPI dependencies. There are no Qt or event-loop dependencies here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger

from clinic.config import settings

SUPPORTED_LANGUAGES: tuple[str, ...] = ("uz", "ru")
DEFAULT_LANGUAGE: str = "uz"


class Translator:
    """In-memory dictionary of translated strings keyed by language."""

    def __init__(self) -> None:
        self._strings: dict[str, dict[str, str]] = {}
        self._load_all()

    def _load_all(self) -> None:
        i18n_dir: Path = settings.i18n_dir
        for lang in SUPPORTED_LANGUAGES:
            path = i18n_dir / f"{lang}.json"
            if not path.is_file():
                logger.warning("Translation file missing: {}", path)
                self._strings[lang] = {}
                continue
            with path.open("r", encoding="utf-8") as f:
                self._strings[lang] = json.load(f)
            logger.debug("Loaded {} strings for '{}'", len(self._strings[lang]), lang)

    def reload(self) -> None:
        """Rescan the i18n directory (useful in dev after editing JSON)."""
        self._strings.clear()
        self._load_all()

    def is_supported(self, lang: str) -> bool:
        return lang in SUPPORTED_LANGUAGES

    def t(self, key: str, lang: str = DEFAULT_LANGUAGE, /, **fmt: Any) -> str:
        """Look up ``key`` in ``lang``, falling back to Uzbek and then to the raw key."""
        value = (
            self._strings.get(lang, {}).get(key)
            or self._strings.get(DEFAULT_LANGUAGE, {}).get(key)
            or key
        )
        if fmt:
            try:
                return value.format(**fmt)
            except (KeyError, IndexError):
                return value
        return value


translator = Translator()


def t(key: str, lang: str = DEFAULT_LANGUAGE, **fmt: Any) -> str:
    """Shortcut around ``translator.t()``. Used from Python code."""
    return translator.t(key, lang, **fmt)
