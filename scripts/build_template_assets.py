"""Generate the two default images used by the compact reception template.

The output goes into ``templates/assets/``:

  * ``logo.png`` — a stylised round "NurMed" clinic logo (blue circle
    with three small icons and the clinic name in white).
  * ``qr.png``   — a real QR code linking to the clinic Instagram page
    (``https://instagram.com/nurmed_lor``).

The images are checked into git so ``build_reception_template.py`` can
embed them without any external step.  Clinics that want to use their
own real logo / QR simply drop replacement PNGs (same file names) into
``templates/assets/`` and re-run::

    python scripts/build_reception_template.py

Both files are pure PNG so they open in every image editor.  The colour
palette matches the reference NurMed brand shown in Uzbek Cyrillic
letterheads (blue #29A6DA).
"""

from __future__ import annotations

from pathlib import Path

import segno
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "templates" / "assets"

# ----------------------------------------------------------------------------
# NurMed brand constants
# ----------------------------------------------------------------------------

BRAND_BLUE = (41, 166, 218)          # ≈ #29A6DA — main circle fill
BRAND_BLUE_DARK = (28, 133, 178)     # circle inner ring
WHITE = (255, 255, 255)

LOGO_SIZE = 600                      # px — final square PNG side
QR_TARGET_URL = "https://instagram.com/nurmed_lor"


# ----------------------------------------------------------------------------
# Logo generator
# ----------------------------------------------------------------------------

def _load_font(size: int) -> ImageFont.ImageFont:
    """Pick the first available TrueType font, falling back to default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "C:/Windows/Fonts/arialbd.ttf",         # Windows (build-time only)
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_ear_glyph(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int) -> None:
    """Very simplified 'ear' pictogram — outer C shape."""
    # Outer white arc, thick
    draw.arc(
        (cx - r, cy - r, cx + r, cy + r),
        start=30, end=290, fill=WHITE, width=max(4, r // 5),
    )
    # Inner lobe
    inner = r // 3
    draw.ellipse(
        (cx - inner, cy + r // 3 - inner, cx + inner, cy + r // 3 + inner),
        outline=WHITE, width=max(3, inner // 3),
    )


def _draw_spine_glyph(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int) -> None:
    """Very simplified 'spine / snake' pictogram — S curve."""
    # Approximate an S using two arcs
    w = max(3, r // 4)
    top_box = (cx - r // 2, cy - r, cx + r // 2, cy)
    bot_box = (cx - r // 2, cy, cx + r // 2, cy + r)
    draw.arc(top_box, start=180, end=360, fill=WHITE, width=w)
    draw.arc(bot_box, start=0, end=180, fill=WHITE, width=w)


def _draw_drop_glyph(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int) -> None:
    """Very simplified 'water drop' pictogram."""
    # Triangle tip + circle body = teardrop
    draw.polygon(
        [(cx, cy - r), (cx - r // 2, cy), (cx + r // 2, cy)],
        fill=WHITE,
    )
    draw.ellipse((cx - r // 2, cy - r // 4, cx + r // 2, cy + r), fill=WHITE)


def make_logo(dst: Path, size: int = LOGO_SIZE) -> Path:
    """Create the round NurMed brand mark as ``dst``."""
    img = Image.new("RGB", (size, size), WHITE)
    draw = ImageDraw.Draw(img)

    # Filled brand circle
    pad = int(size * 0.02)
    draw.ellipse((pad, pad, size - pad, size - pad), fill=BRAND_BLUE)

    # Three small glyphs across the upper half
    glyph_r = size // 12
    row_y = int(size * 0.38)
    xs = (int(size * 0.30), int(size * 0.50), int(size * 0.70))
    _draw_ear_glyph(draw, xs[0], row_y, glyph_r)
    _draw_spine_glyph(draw, xs[1], row_y, glyph_r)
    _draw_drop_glyph(draw, xs[2], row_y, glyph_r)

    # Text — "NurMed" in the lower third
    font = _load_font(size // 5)
    text = "NurMed"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = int(size * 0.60)
    draw.text((tx, ty), text, fill=WHITE, font=font)

    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, "PNG", optimize=True)
    return dst


# ----------------------------------------------------------------------------
# QR generator
# ----------------------------------------------------------------------------

def make_qr(dst: Path, url: str = QR_TARGET_URL, size: int = LOGO_SIZE) -> Path:
    """Generate a QR code for ``url``, saved as ``dst``.

    Uses ``segno`` because it produces small, high-contrast QR PNGs
    without external image libraries.
    """
    q = segno.make(url, error="m")

    # Save a temp file that segno can write to, then re-export at the
    # correct pixel size via Pillow so we don't fight segno's DPI logic.
    tmp = dst.with_suffix(".tmp.png")
    q.save(str(tmp), scale=10, border=2, dark="black", light="white")

    # Re-scale to the final square size for consistency with the logo.
    img = Image.open(tmp).convert("RGB")
    img = img.resize((size, size), Image.NEAREST)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, "PNG", optimize=True)
    tmp.unlink(missing_ok=True)
    return dst


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main() -> None:
    logo_path = make_logo(ASSETS_DIR / "logo.png")
    qr_path = make_qr(ASSETS_DIR / "qr.png")
    print(f"[OK] Wrote {logo_path.relative_to(ROOT)} ({logo_path.stat().st_size:,} bytes)")
    print(f"[OK] Wrote {qr_path.relative_to(ROOT)} ({qr_path.stat().st_size:,} bytes)")
    print()
    print("Replace either PNG with your real logo / QR and re-run:")
    print("    python scripts/build_reception_template.py")


if __name__ == "__main__":
    main()
