#!/usr/bin/env python3
"""
Generate per-patch OG social preview images to og/v{version}.png.
Requires: pip install pillow
Usage: python3 scripts/build-og-images.py  (or: make og)
"""
import json, os, sys, textwrap
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    print("ERROR: Pillow not installed — run: pip install pillow", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent.parent
PATCHES_DIR = ROOT / "patches"
OG_DIR = ROOT / "og"
OG_DIR.mkdir(exist_ok=True)

W, H = 1200, 630
BG          = (10,  6,  18)
ACCENT      = (167, 139, 250)
MUTED       = (139, 130, 160)
FG          = (232, 227, 240)
STRIP_BG    = (20,  12,  36)

TYPE_COLORS = {
    "added":   (134, 239, 172),
    "changed": (252, 211,  77),
    "fixed":   (147, 197, 253),
    "removed": (252, 165, 165),
}

FONT_CANDIDATES_BOLD = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

def load_font(size, bold=False):
    candidates = FONT_CANDIDATES_BOLD if bold else FONT_CANDIDATES
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_patch(patch):
    img = Image.new("RGB", (W, H), BG)

    # Subtle top-left glow
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((-80, -80, 520, 380), fill=(45, 15, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(110))
    img = Image.blend(img, glow, 0.4)
    draw = ImageDraw.Draw(img)

    pad = 64
    version     = patch.get("version", "?")
    title       = patch.get("title", "")
    date        = patch.get("date", "")
    counts      = {t: len(patch.get(t) or []) for t in ("added", "changed", "fixed", "removed")}
    first_line  = next(
        (patch.get(t, [None])[0] for t in ("added", "changed") if patch.get(t)),
        None
    )

    # Site label
    draw.text((pad, pad), "spiritvale.tama.sh", fill=MUTED, font=load_font(22))

    # Version
    draw.text((pad, pad + 48), f"v{version}", fill=ACCENT, font=load_font(72, bold=True))

    # Title
    if title:
        draw.text((pad, pad + 138), title, fill=FG, font=load_font(40, bold=True))

    # Date
    if date:
        draw.text((pad, pad + 194), date, fill=MUTED, font=load_font(26))

    # Divider
    draw.line([(pad, 308), (W - pad, 308)], fill=(60, 40, 90), width=2)

    # Change-type pills
    x, y = pad, 336
    for t, color in TYPE_COLORS.items():
        n = counts.get(t, 0)
        if not n:
            continue
        label = f"{n} {t}"
        f = load_font(26)
        bb = draw.textbbox((0, 0), label, font=f)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        pw, ph = tw + 40, th + 16
        bg_color = tuple(max(0, int(c * 0.18)) for c in color)
        draw.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2,
                                fill=bg_color, outline=color)
        draw.text((x + 20, y + 8), label, fill=color, font=f)
        x += pw + 14

    # Teaser bullet
    if first_line:
        teaser = textwrap.shorten(first_line, width=92, placeholder="…")
        draw.text((pad, 416), f"✦  {teaser}", fill=MUTED, font=load_font(24))

    # Bottom branding strip
    draw.rectangle([(0, H - 76), (W, H)], fill=STRIP_BG)
    draw.text((pad, H - 52), "SpiritVale Patch Notes", fill=ACCENT, font=load_font(28, bold=True))
    draw.text((W - pad - 190, H - 52), "Community Hub", fill=MUTED, font=load_font(24))

    return img


def main():
    patch_files = sorted(PATCHES_DIR.glob("v*.json"))
    if not patch_files:
        print("No patch files found.", file=sys.stderr)
        sys.exit(1)

    for pf in patch_files:
        with open(pf) as f:
            patch = json.load(f)
        version = patch.get("version", pf.stem.lstrip("v"))
        out_path = OG_DIR / f"v{version}.png"
        img = draw_patch(patch)
        img.save(out_path, "PNG", optimize=True)
        print(f"  ✓ og/v{version}.png", file=sys.stderr)

    print(f"\nGenerated {len(patch_files)} OG images → og/", file=sys.stderr)


if __name__ == "__main__":
    main()
