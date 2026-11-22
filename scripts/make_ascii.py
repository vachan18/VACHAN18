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


def cutout(img: Image.Image) -> Image.Image:
    """Remove a busy background with OpenCV GrabCut (subject assumed centred in frame)."""
    import cv2
    import numpy as np
    rgb = np.array(img.convert("RGB"))[:, :, ::-1].copy()
    h, w = rgb.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    rect = (int(w * .05), int(h * .04), int(w * .90), int(h * .96))
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(rgb, mask, rect, bgd, fgd, 8, cv2.GC_INIT_WITH_RECT)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    # keep only the largest blob (the person), smooth the edge
    n, labels, stats, _ = cv2.connectedComponentsWithStats(fg)
    if n > 1:
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        fg = np.where(labels == big, 255, 0).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    out = img.convert("RGBA")
    out.putalpha(Image.fromarray(fg))
    return out


def to_ascii(img: Image.Image, cols: int, contrast: float, threshold: int) -> list[str]:
    img = ImageOps.exif_transpose(img)
    alpha = img.getchannel("A") if img.mode == "RGBA" else None
    gray = img.convert("L")
    if alpha is not None:
        # Equalise tones over the subject only, so dark clothing keeps its folds
        # instead of collapsing into a solid block of '@'.
        subject = alpha.point(lambda v: 255 if v >= 128 else 0)
        gray = ImageOps.equalize(gray, mask=subject)
        gray = Image.composite(gray, Image.new("L", gray.size, 255), subject)
    else:
        gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(contrast)
    rows = max(1, round(cols * gray.height / gray.width * CELL_ASPECT))
    gray = gray.resize((cols, rows), Image.LANCZOS)
    a = alpha.resize((cols, rows), Image.LANCZOS).load() if alpha is not None else None
    px = gray.load()
    lines = []
    for y in range(rows):
        row = ""
        for x in range(cols):
            v = px[x, y]
            if (a is not None and a[x, y] < 128) or v >= threshold:
                row += " "
            else:
                row += RAMP[min(len(RAMP) - 1, v * len(RAMP) // 256)]
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
    ap.add_argument("--crop", help="x0,y0,x1,y1 in source pixels, e.g. head and shoulders")
    ap.add_argument("--cutout", action="store_true", help="remove background (needs opencv-python)")
    a = ap.parse_args()

    photo = Path(a.photo)
    img = Image.open(photo) if photo.exists() else placeholder()
    if not photo.exists():
        print(f"{photo.name} not found: writing monogram placeholder")
    if a.crop:
        img = img.crop(tuple(int(v) for v in a.crop.split(",")))
    if a.cutout:
        img = cutout(img)
    lines = to_ascii(img, a.cols, a.contrast, a.threshold)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(lines)} rows x {a.cols} cols")


if __name__ == "__main__":
    main()
