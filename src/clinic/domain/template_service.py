"""Management of the shipped Word template file.

The reception .docx renderer looks for a template at
``settings.templates_dir / "reception_template.docx"``. If it exists it is
used as a ``docxtpl`` template; otherwise the renderer falls back to
programmatic ``python-docx`` rendering.

This service exposes a tiny CRUD-ish API around that single file so the
Settings screen can:

- inspect the file's status (exists, size, mtime)
- accept an uploaded replacement
- reset to the shipped default (regenerates via ``build_reception_template``)
- delete the file entirely (then the fallback renderer kicks in)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from loguru import logger

from clinic.config import settings
from clinic.printing.docx_builder import TEMPLATE_FILENAME


@dataclass
class TemplateStatus:
    """Snapshot of the currently-installed Word template."""

    exists: bool
    path: Path
    size_bytes: int
    modified: datetime | None

    @property
    def size_kb(self) -> float:
        return round(self.size_bytes / 1024.0, 1) if self.size_bytes else 0.0


# Hard cap on uploaded template size — keeps upload handling simple. A
# realistic reception template is < 100 KB; 5 MB is a very generous limit
# that still guards against accidental huge uploads.
MAX_TEMPLATE_BYTES = 5 * 1024 * 1024

# docx MIME + magic bytes. .docx is a ZIP archive so the first two bytes
# are "PK". We use the magic check because Windows browsers often send
# ``application/octet-stream`` or a Word-specific mimetype rather than the
# ``vnd.openxmlformats`` MIME.
_DOCX_MAGIC = b"PK\x03\x04"


class TemplateError(Exception):
    """Raised for validation failures on template upload."""


def template_path() -> Path:
    return Path(settings.templates_dir) / TEMPLATE_FILENAME


def status() -> TemplateStatus:
    p = template_path()
    if not p.is_file():
        return TemplateStatus(exists=False, path=p, size_bytes=0, modified=None)
    st = p.stat()
    return TemplateStatus(
        exists=True,
        path=p,
        size_bytes=st.st_size,
        modified=datetime.fromtimestamp(st.st_mtime),
    )


def save_uploaded(payload: bytes) -> TemplateStatus:
    """Validate + persist an uploaded .docx as the current template.

    Raises :class:`TemplateError` on any validation issue.
    """
    if not payload:
        raise TemplateError("empty")
    if len(payload) > MAX_TEMPLATE_BYTES:
        raise TemplateError("too_large")
    if not payload.startswith(_DOCX_MAGIC):
        raise TemplateError("invalid")

    # Round-trip through python-docx to make sure the file is a readable
    # Word document. A raw ZIP will pass the magic check but might not be
    # a valid .docx.
    import io

    from docx import Document as _Doc

    try:
        _ = _Doc(io.BytesIO(payload))
    except Exception as exc:
        logger.warning("Rejected uploaded template: {}", exc)
        raise TemplateError("invalid") from exc

    p = template_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(payload)
    logger.info("Saved uploaded template ({} bytes) to {}", len(payload), p)
    return status()


def reset_to_default() -> TemplateStatus:
    """Rewrite the template file from the shipped baseline."""
    from scripts.build_reception_template import build_default_template

    build_default_template(template_path())
    logger.info("Reception template reset to shipped default")
    return status()


def delete() -> bool:
    """Remove the template file. Returns True if a file was removed."""
    p = template_path()
    if not p.is_file():
        return False
    p.unlink()
    logger.info("Reception template deleted")
    return True


__all__ = [
    "MAX_TEMPLATE_BYTES",
    "TemplateError",
    "TemplateStatus",
    "delete",
    "reset_to_default",
    "save_uploaded",
    "status",
    "template_path",
]
