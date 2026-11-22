#!/usr/bin/env python3
"""One-off: download OFL fonts, subset to ASCII + a few symbols, save WOFF to fonts/.

SVGs shown through <img> cannot load web fonts, so render_readme_cards.py
embeds these files as base64 @font-face. Re-run only to change fonts/glyphs.
"""
from __future__ import annotations

import io
import urllib.request
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fonts"
GF = "https://raw.githubusercontent.com/google/fonts/main/ofl"

# (output name, source url, variable-axis pin or None, expect italic?)
FONTS = [
    ("serif-400.woff", f"{GF}/instrumentserif/InstrumentSerif-Regular.ttf", None, False),
    ("serif-italic.woff", f"{GF}/instrumentserif/InstrumentSerif-Italic.ttf", None, True),
    ("geist-400.woff", f"{GF}/geist/Geist%5Bwght%5D.ttf", {"wght": 400}, False),
    ("geist-600.woff", f"{GF}/geist/Geist%5Bwght%5D.ttf", {"wght": 600}, False),
    ("geist-mono.woff", f"{GF}/geistmono/GeistMono%5Bwght%5D.ttf", {"wght": 400}, False),
]

# Printable ASCII plus the arrows, dots and dashes the cards use.
UNICODES = list(range(0x20, 0x7F)) + [0x00B7, 0x2014, 0x2013, 0x2019, 0x2022, 0x2192, 0x2197, 0x2605, 0x2191]


def is_italic(font: TTFont) -> bool:
    names = " ".join(
        str(r) for r in font["name"].names if r.nameID in (2, 4, 17)
    ).lower()
    return "italic" in names or bool(font["OS/2"].fsSelection & 1)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    cache: dict[str, bytes] = {}
    for name, url, pin, want_italic in FONTS:
        if url not in cache:
            with urllib.request.urlopen(url, timeout=60) as r:
                cache[url] = r.read()
        font = TTFont(io.BytesIO(cache[url]))
        if pin:
            font = instancer.instantiateVariableFont(font, pin)
        # Google once served the italic file under the regular name: check, don't trust.
        if is_italic(font) != want_italic:
            raise SystemExit(f"{name}: italic flag mismatch (got {is_italic(font)})")
        buf = io.BytesIO()
        font.save(buf)
        buf.seek(0)
        font = TTFont(buf)

        opts = subset.Options()
        opts.layout_features = ["kern", "liga"]
        opts.name_IDs = [1, 2, 4]
        opts.hinting = False
        s = subset.Subsetter(opts)
        s.populate(unicodes=UNICODES)
        s.subset(font)
        font.flavor = "woff"
        if "meta" in font:
            del font["meta"]
        font.save(OUT / name)
        print(f"{name}: {(OUT / name).stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
