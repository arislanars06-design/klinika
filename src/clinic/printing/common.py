"""Helpers shared by the printing sub-package.

The three builders (reception form, receipt, statistics) all need to turn
Decimal values into human-readable strings and to open the freshly-written
``.docx`` file with the OS default handler.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from loguru import logger


def format_money(value: Decimal | float | int) -> str:
    """Format a currency amount with spaces as thousand separators."""
    v = float(value)
    if v == int(v):
        return f"{int(v):,}".replace(",", " ")
    return f"{v:,.2f}".replace(",", " ")


def format_date(value: date | datetime | None, *, with_time: bool = False) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M" if with_time else "%d.%m.%Y")
    return value.strftime("%d.%m.%Y")


def format_age(birth_year: int, today: date | None = None) -> int:
    today = today or date.today()
    return max(0, today.year - birth_year)


def open_document(path: Path) -> bool:
    """Attempt to open ``path`` with the user's default handler.

    Falls back gracefully on headless environments — the file is always
    written, this is a best-effort convenience for interactive sessions.
    Returns ``True`` if a launch command was executed.
    """
    path = Path(path)
    if not path.exists():
        logger.warning("Cannot open missing document: {}", path)
        return False
    try:
        if sys.platform.startswith("win"):
            import os

            os.startfile(str(path))  # type: ignore[attr-defined]
            return True
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.Popen(
            [opener, str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        logger.exception("Failed to open document with system handler")
        return False


__all__ = ["format_age", "format_date", "format_money", "open_document"]
