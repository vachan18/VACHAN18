#!/usr/bin/env python3
"""Vendor brand icons for the TECH STACK card into data/icons.json.

Run by hand after editing `tech_stack` in profile-data.json:

    python scripts/vendor_icons.py

Rendering reads only data/icons.json, so CI and GitHub's <img> sandbox never
need the network. Sources (pinned):
  - Simple Icons  (CC0-1.0)  https://simpleicons.org
  - Lobe Icons    (MIT)      for brands Simple Icons doesn't carry (OpenAI)
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "icons.json"
PROFILE = json.loads((ROOT / "profile-data.json").read_text(encoding="utf-8"))

SI_VERSION = "16.38.1"
LOBE_VERSION = "1.106.0"
SI = f"https://cdn.jsdelivr.net/npm/simple-icons@{SI_VERSION}"
LOBE = f"https://cdn.jsdelivr.net/npm/@lobehub/icons-static-svg@{LOBE_VERSION}/icons"

# Brands missing from Simple Icons: slug -> (title, hex, lobe file name)
LOBE_ICONS = {"openai": ("OpenAI", "000000", "openai")}


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-cards"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def title_to_slug(title: str) -> str:
    """Simple Icons' own slug rule."""
    s = title.lower().replace("+", "plus").replace(".", "dot").replace("&", "and")
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s)


def parse_svg(svg: str) -> tuple[str, str]:
    paths = re.findall(r'<path[^>]*\sd="([^"]+)"', svg)
    if not paths:
        raise ValueError("no <path d> found")
    rule = "evenodd" if 'fill-rule="evenodd"' in svg else "nonzero"
    return " ".join(paths), rule


def main() -> None:
    stack = PROFILE["tech_stack"]
    slugs = list(dict.fromkeys(stack["top"] + stack["bottom"]))
    meta = {}
    for icon in json.loads(get(f"{SI}/data/simple-icons.json")):
        meta[icon.get("slug") or title_to_slug(icon["title"])] = icon

    icons, missing = {}, []
    for slug in slugs:
        try:
            if slug in LOBE_ICONS:
                title, hex_, name = LOBE_ICONS[slug]
                path, rule = parse_svg(get(f"{LOBE}/{name}.svg"))
                source, lic = f"@lobehub/icons-static-svg@{LOBE_VERSION}", "MIT"
            else:
                if slug not in meta:
                    raise KeyError("not in simple-icons.json")
                title, hex_ = meta[slug]["title"], meta[slug]["hex"]
                path, rule = parse_svg(get(f"{SI}/icons/{slug}.svg"))
                source, lic = f"simple-icons@{SI_VERSION}", "CC0-1.0"
        except Exception as err:  # noqa: BLE001 - report every bad slug, then fail
            missing.append(f"{slug} ({err})")
            continue
        icons[slug] = {"title": title, "hex": f"#{hex_.upper()}", "path": path, "rule": rule,
                       "source": source, "license": lic}
        print(f"  {slug:16s} {title:20s} #{hex_.upper()}")

    if missing:
        sys.exit("missing icons: " + ", ".join(missing))
    OUT.write_text(json.dumps(icons, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(icons)} icons")


if __name__ == "__main__":
    main()
