#!/usr/bin/env python3
"""Turn source-photo.png into ASCII art for the hero card (data/ascii.txt).

Usage:  python scripts/make_ascii.py [photo] [--cols 110] [--contrast 1.6] [--threshold 235]

Best input: front-facing, plain light background, good contrast. Dark pixels
become dense glyphs (ink on paper). Pixels lighter than --threshold become
blank so the background disappears. With no photo present, renders a monogram
placeholder so the pipeline still works.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ascii.txt"
RAMP = "@%#*+=-:. "          # dark -> light
CELL_ASPECT = 0.6            # mono glyph width / line height in the hero card


def placeholder(text: str = "V") -> Image.Image:
    from fontTools.ttLib import TTFont  # convert embedded WOFF to something PIL can load
    import io
    f = TTFont(ROOT / "fonts" / "serif-400.woff")
    f.flavor = None
    buf = io.BytesIO()
    f.save(buf)
    buf.seek(0)
    font = ImageFont.truetype(buf, 760)
    img = Image.new("L", (1000, 1000), 255)
    d = ImageDraw.Draw(img)
    box = d.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((img.width - w) / 2 - box[0], (img.height - h) / 2 - box[1]), text, font=font, fill=0)
    return img.filter(ImageFilter.GaussianBlur(6))


def to_ascii(img: Image.Image, cols: int, contrast: float, threshold: int) -> list[str]:
    img = ImageOps.exif_transpose(img).convert("L")
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    rows = max(1, round(cols * img.height / img.width * CELL_ASPECT))
    img = img.resize((cols, rows), Image.LANCZOS)
    px = img.load()
    lines = []
    for y in range(rows):
        row = ""
        for x in range(cols):
            v = px[x, y]
            row += " " if v >= threshold else RAMP[min(len(RAMP) - 1, v * len(RAMP) // 256)]
        lines.append(row.rstrip())
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("photo", nargs="?", default=str(ROOT / "source-photo.png"))
    ap.add_argument("--cols", type=int, default=110)
    ap.add_argument("--contrast", type=float, default=1.6)
    ap.add_argument("--threshold", type=int, default=235)
    a = ap.parse_args()

    photo = Path(a.photo)
    img = Image.open(photo) if photo.exists() else placeholder()
    if not photo.exists():
        print(f"{photo.name} not found: writing monogram placeholder")
    lines = to_ascii(img, a.cols, a.contrast, a.threshold)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(lines)} rows x {a.cols} cols")


if __name__ == "__main__":
    main()
