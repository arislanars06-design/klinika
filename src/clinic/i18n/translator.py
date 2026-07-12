"""Runtime translator with Qt signal for hot-swapping the UI language.

Usage::

    from clinic.i18n.translator import translator, t

    translator.set_language("uz")
    label.setText(t("menu.start_reception"))

Widgets that need to update on language changes can connect to
``translator.language_changed`` and re-render themselves.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger
from PySide6.QtCore import QObject, Signal

from clinic.config import settings

SUPPORTED_LANGUAGES: tuple[str, ...] = ("uz", "ru")
DEFAULT_LANGUAGE: str = "uz"


class Translator(QObject):
    """Loads JSON translation files and emits a signal on language change."""

    language_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._language: str = DEFAULT_LANGUAGE
        self._strings: dict[str, dict[str, str]] = {}
        self._load_all()

    # ----- loading -----

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

    # ----- public API -----

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, lang: str) -> None:
        if lang not in SUPPORTED_LANGUAGES:
            logger.warning("Unsupported language requested: {}", lang)
            return
        if lang == self._language:
            return
        self._language = lang
        logger.info("Language switched to: {}", lang)
        self.language_changed.emit(lang)

    def t(self, key: str, **fmt: Any) -> str:
        """Look up ``key`` and format with ``fmt`` kwargs.

        Falls back to Uzbek, then to the raw key if nothing matches.
        """
        value = (
            self._strings.get(self._language, {}).get(key)
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


def t(key: str, **fmt: Any) -> str:
    """Shortcut around ``translator.t()`` for concise call sites."""
    return translator.t(key, **fmt)
