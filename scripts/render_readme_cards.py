#!/usr/bin/env python3
"""Render every README card in cards/ as a self-contained animated SVG.

Inputs : profile-data.json, data/contributions.json, data/ascii.txt, fonts/*.woff
Output : cards/*.svg

Only techniques that survive GitHub's <img> sandbox are used: inline <style>
with CSS @keyframes, SMIL (<set>, <animateTransform>), and fonts embedded as
base64 WOFF. No scripts, no external requests.

Every animated element's *resting* style is its final state; keyframes only
describe where it comes from (fill-mode: both). So switching animation off
(STATIC=1, or prefers-reduced-motion) leaves the finished card on screen.

STATIC=1 python scripts/render_readme_cards.py  -> end-state cards for screenshots.
"""
from __future__ import annotations

import base64
import html
import json
import os
from datetime import date
from functools import lru_cache
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
FONTS = ROOT / "fonts"
STATIC = os.getenv("STATIC") == "1"

PROFILE = json.loads((ROOT / "profile-data.json").read_text(encoding="utf-8"))
DATA = json.loads((ROOT / "data" / "contributions.json").read_text(encoding="utf-8"))

# ---- palette ---------------------------------------------------------------
PAPER, LINE, INK, BODY, MUTED = "#f3f3f1", "#e2e2dd", "#111111", "#3a3a3c", "#6e6e73"
BLUE, RED, YELLOW = "#2f55ff", "#ff4632", "#ffc83d"
TILE = {  # bg, fg, soft
    "blue": (BLUE, "#ffffff", "rgba(255,255,255,.72)"),
    "red": (RED, "#ffffff", "rgba(255,255,255,.75)"),
    "yellow": (YELLOW, INK, "rgba(17,17,17,.68)"),
    "paper": (PAPER, INK, "rgba(17,17,17,.62)"),
}
HEAT = ["#e4e4df", "#c7d2ff", "#8ea4ff", "#5577ff", BLUE, "#1d38c9"]
LANG = {"Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
        "HTML": "#e34c26", "Astro": "#ff5a03", "CSS": "#563d7c", "Java": "#b07219"}

# ---- fonts -----------------------------------------------------------------
FACES = {  # css family, file, weight, style
    "serif": ("Instrument Serif", "serif-400.woff", 400, "normal"),
    "serif-i": ("Instrument Serif", "serif-italic.woff", 400, "italic"),
    "sans": ("Geist", "geist-400.woff", 400, "normal"),
    "sans-b": ("Geist", "geist-600.woff", 600, "normal"),
    "mono": ("Geist Mono", "geist-mono.woff", 400, "normal"),
}
SERIF = "'Instrument Serif',Georgia,serif"
SANS = "Geist,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'Geist Mono',ui-monospace,Menlo,Consolas,monospace"


def font_css(*faces: str) -> str:
    out = []
    for key in faces:
        fam, file, weight, style = FACES[key]
        b64 = base64.b64encode((FONTS / file).read_bytes()).decode()
        out.append(f"@font-face{{font-family:'{fam}';font-weight:{weight};font-style:{style};"
                   f"src:url(data:font/woff;base64,{b64}) format('woff')}}")
    return "".join(out)


@lru_cache(maxsize=None)
def _advances(face: str) -> tuple[dict, int]:
    f = TTFont(FONTS / FACES[face][1])
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    return {cp: hmtx[g][0] for cp, g in cmap.items()}, f["head"].unitsPerEm


def measure(text: str, face: str, size: float) -> float:
    adv, upm = _advances(face)
    fallback = adv.get(ord("n"), upm // 2)
    return sum(adv.get(ord(c), fallback) for c in text) * size / upm


def wrap(text: str, face: str, size: float, width: float, max_lines: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if measure(trial, face, size) <= width:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        cur = w
        if len(lines) == max_lines:
            break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines and " ".join(lines) != " ".join(words):
        last = lines[-1]
        while last and measure(last + "…", face, size) > width:
            last = last[:-1].rstrip()
        lines[-1] = last.rstrip(",.;:") + "…"
    return lines


def fit(text: str, face: str, size: float, width: float) -> str:
    if measure(text, face, size) <= width:
        return text
    while text and measure(text + "…", face, size) > width:
        text = text[:-1]
    return text.rstrip() + "…"


def esc(s) -> str:
    return html.escape(str(s), quote=True)


# ---- shared animation ------------------------------------------------------
BASE_CSS = """
text{font-kerning:normal}
.r,.f,.p,.g,.s,.t,.cu{animation-duration:.8s;animation-fill-mode:both;animation-timing-function:cubic-bezier(.2,.7,.2,1);transform-box:fill-box}
.r{animation-name:rise}
.f{animation-name:fade;animation-duration:.5s}
.p{animation-name:pop;animation-duration:.45s;transform-origin:center}
.g{animation-name:grow;animation-duration:.9s;transform-origin:50% 100%}
.s{animation-name:swing;animation-duration:1.1s;transform-origin:50% 100%;transform-box:view-box}
.t{animation-name:type;animation-duration:.01s;animation-timing-function:step-end}
.ring{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 3.2s ease-out infinite}
.dot{animation:dot 1.8s ease-in-out infinite}
.nudge{transform-box:fill-box;animation:nudge 1.6s ease-in-out infinite}
.caret{animation:caret 1s step-end infinite}
@keyframes rise{from{opacity:0;transform:translateY(14px)}}
@keyframes fade{from{opacity:0}}
@keyframes type{from{opacity:0}}
@keyframes pop{from{opacity:0;transform:scale(.2)}70%{transform:scale(1.12)}}
@keyframes grow{from{transform:scaleY(0)}}
@keyframes swing{0%{opacity:0;transform:translateY(90px) rotate(-7deg)}55%{opacity:1;transform:translateY(-8px) rotate(1.6deg)}78%{transform:translateY(3px) rotate(-.6deg)}100%{transform:none}}
@keyframes ring{0%{opacity:.55;transform:scale(.4)}100%{opacity:0;transform:scale(2.6)}}
@keyframes dot{50%{opacity:.25}}
@keyframes nudge{50%{transform:translate(3px,-3px)}}
@keyframes caret{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""
STATIC_CSS = "*{animation:none!important}"


def d(sec: float) -> str:
    """Inline animation-delay."""
    return f'style="animation-delay:{sec:.3f}s"'


def svg(w: int, h: int, label: str, body: str, faces: tuple[str, ...], css: str = "",
        defs: str = "") -> str:
    style = font_css(*faces) + BASE_CSS + css + (STATIC_CSS if STATIC else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
            f"<title>{esc(label)}</title><style>{style}</style>"
            f"{f'<defs>{defs}</defs>' if defs else ''}{body}</svg>\n")


def card_bg(w: int, h: int, fill: str = PAPER, stroke: str = LINE) -> str:
    return (f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="18" '
            f'fill="{fill}" stroke="{stroke}"/>')


def shine_gradient(gid: str, base: str, glint: str, width: float, begin: float,
                   dur: float = 7) -> str:
    """Gradient fill whose bright band sweeps across text (SVG has no background-clip:text)."""
    anim = "" if STATIC else (
        f'<animateTransform attributeName="gradientTransform" type="translate" '
        f'from="{-width} 0" to="{width} 0" begin="{begin}s" dur="{dur}s" repeatCount="indefinite"/>')
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="0" '
            f'x2="{width}" y2="0" gradientTransform="translate({-width} 0)">'
            f'<stop offset="0" stop-color="{base}"/><stop offset=".40" stop-color="{base}"/>'
            f'<stop offset=".5" stop-color="{glint}"/><stop offset=".60" stop-color="{base}"/>'
            f'<stop offset="1" stop-color="{base}"/>{anim}</linearGradient>')


def count_up(x: float, y: float, n: int, attrs: str, begin: float, dur: float = 1.0,
             frames: int = 18, suffix: str = "") -> str:
    """Number counting 0 -> n: one <text> per frame toggled by SMIL <set> (CSS can't change text)."""
    final = f'<text x="{x}" y="{y}" {attrs}>{n}{esc(suffix)}</text>'
    if STATIC or n <= 1:
        return final
    step = dur / frames
    out = []
    shown = set()
    for i in range(frames):
        t = (i + 1) / frames
        v = round(n * (1 - (1 - t) ** 3))  # ease-out
        if v >= n or v in shown:
            continue
        shown.add(v)
        out.append(f'<text x="{x}" y="{y}" {attrs} visibility="hidden">{v}{esc(suffix)}'
                   f'<set attributeName="visibility" to="visible" begin="{begin + i * step:.3f}s" '
                   f'dur="{step:.3f}s"/></text>')
    hide = (f'<set attributeName="visibility" to="hidden" begin="0s" '
            f'dur="{begin + dur - step:.3f}s"/>')
    return "".join(out) + final.replace("</text>", hide + "</text>")


# ---- cards -----------------------------------------------------------------
def hero() -> str:
    W, H = 880, 432
    name = PROFILE["name"].split()
    first, rest = name[0], " ".join(name[1:]) + "."
    role = f'{PROFILE["role"]} at {PROFILE["company"]}'
    bio = wrap(PROFILE["bio"], "sans", 15.5, 400, 3)
    label = f'{PROFILE["name"]}. {role}. {PROFILE["bio"]}'

    b = [card_bg(W, H)]
    b.append(f'<text class="f" {d(.05)} x="48" y="66" font-family="{MONO}" font-size="12" '
             f'letter-spacing="1.6" fill="{MUTED}">HELLO, I\'M</text>')
    b.append(f'<text class="r" {d(.15)} x="44" y="158" font-family="{SERIF}" font-size="104" '
             f'fill="{INK}" letter-spacing="-1.5">{esc(first)}</text>')
    b.append(f'<text class="r" {d(.3)} x="46" y="250" font-family="{SERIF}" font-style="italic" '
             f'font-size="104" fill="url(#shine)" letter-spacing="-1">{esc(rest)}</text>')
    b.append(f'<g class="r" {d(.5)}><circle class="dot" cx="54" cy="285" r="5" fill="{BLUE}"/>'
             f'<text x="68" y="290.5" font-family="{SANS}" font-weight="600" font-size="17" '
             f'fill="{INK}">{esc(role)}</text></g>')
    for i, line in enumerate(bio):
        b.append(f'<text class="r" {d(.6 + i * .07)} x="48" y="{320 + i * 21}" font-family="{SANS}" '
                 f'font-size="15.5" fill="{BODY}">{esc(line)}</text>')
    b.append(f'<text class="f" {d(.95)} x="48" y="{H - 30}" font-family="{MONO}" font-size="11.5" '
             f'letter-spacing=".6" fill="{MUTED}">{esc(PROFILE["location"].upper())}  ·  '
             f'<tspan fill="{BLUE}">GENAI · BACKEND · SECURITY</tspan></text>')

    # ASCII portrait, printed row by row.
    rows = (ROOT / "data" / "ascii.txt").read_text(encoding="utf-8").rstrip().splitlines()
    cols = max(len(r) for r in rows)
    box_x, box_y, box_w, box_h = 480, 30, 370, H - 60
    lh = min(box_h / len(rows), box_w / (cols * 0.6))
    fs = round(lh, 3)
    px = box_x + (box_w - cols * 0.6 * lh) / 2
    py = box_y + (box_h - len(rows) * lh) / 2 + lh * 0.8
    # Browsers disagree on xml:space / white-space in SVG, so never rely on spaces:
    # leading spaces become an x offset, inner spaces become no-break spaces.
    b.append(f'<g font-family="{MONO}" font-size="{fs}" fill="{INK}">')
    cw = 0.6 * lh
    for i, row in enumerate(rows):
        body = row.strip()
        if body:
            indent = len(row) - len(row.lstrip())
            b.append(f'<text class="t" {d(.35 + i * .018)} x="{px + indent * cw:.1f}" '
                     f'y="{py + i * lh:.2f}">{esc(body).replace(" ", chr(0xA0))}</text>')
    b.append("</g>")

    defs = shine_gradient("shine", INK, BLUE, 420, begin=1.6)
    return svg(W, H, label, "".join(b), ("serif", "serif-i", "sans", "sans-b", "mono"), defs=defs)


def heat_level(c: int, peak: int) -> int:
    if c <= 0:
        return 0
    return min(5, 1 + int(4 * (c / max(peak, 1)) ** 0.5))


def heatmap() -> str:
    days = DATA["days"]
    weeks: list[list[dict]] = []
    for day in days:
        if day["weekday"] == 0 or not weeks:
            weeks.append([])
        weeks[-1].append(day)
    weeks = weeks[-53:]
    cell, gap = 11.5, 3
    W = 880
    grid_w = len(weeks) * (cell + gap) - gap
    x0, y0 = (W - grid_w) / 2, 92
    H = int(y0 + 7 * (cell + gap) + 40)
    peak = sorted((d["count"] for d in days), reverse=True)[min(3, len(days) - 1)] or 1
    first, last = days[0]["date"], days[-1]["date"]
    span = f'{date.fromisoformat(first):%b %Y} → {date.fromisoformat(last):%b %Y}'
    label = f'{DATA["total"]} GitHub contributions, {span}'

    b = [card_bg(W, H)]
    b.append(f'<text class="r" {d(1.2)} x="{x0}" y="58" font-family="{SERIF}" font-size="32" '
             f'fill="{INK}">{DATA["total"]:,} <tspan font-style="italic" fill="{BLUE}">contributions</tspan>'
             f'<tspan font-family="{SANS}" font-size="14" fill="{MUTED}" dx="10">in the last year</tspan></text>')
    b.append(f'<text class="f" {d(1.3)} x="{W - x0}" y="58" text-anchor="end" font-family="{MONO}" '
             f'font-size="11" letter-spacing=".6" fill="{MUTED}">{esc(span.upper())}</text>')
    last_month = None
    for wi, week in enumerate(weeks):
        x = x0 + wi * (cell + gap)
        m = week[0]["date"][:7]
        if m != last_month and week[0]["date"][8:] <= "07" and wi < len(weeks) - 2:
            b.append(f'<text x="{x:.1f}" y="{y0 - 8}" font-family="{MONO}" font-size="9.5" '
                     f'fill="{MUTED}">{date.fromisoformat(week[0]["date"]):%b}</text>')
        last_month = m
        for day in week:
            y = y0 + day["weekday"] * (cell + gap)
            lvl = heat_level(day["count"], peak)
            cls = f'class="p" {d(1.35 + wi * .014 + day["weekday"] * .01)} ' if lvl else ""
            b.append(f'<rect {cls}x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2.5" '
                     f'fill="{HEAT[lvl]}"><title>{day["date"]}: {day["count"]}</title></rect>')
    # legend
    lx = W - x0 - 5 * (cell + gap) + gap
    ly = H - 24
    b.append(f'<text x="{lx - 8}" y="{ly + 9.5}" text-anchor="end" font-family="{MONO}" font-size="9.5" '
             f'fill="{MUTED}">less</text>')
    for i, c in enumerate(HEAT[:5]):
        b.append(f'<rect x="{lx + i * (cell + gap):.1f}" y="{ly}" width="{cell}" height="{cell}" rx="2.5" fill="{c}"/>')
    b.append(f'<text x="{lx + 5 * (cell + gap) + 4:.1f}" y="{ly + 9.5}" font-family="{MONO}" font-size="9.5" '
             f'fill="{MUTED}">more</text>')
    b.append(f'<text x="{x0}" y="{ly + 9.5}" font-family="{MONO}" font-size="9.5" fill="{MUTED}">'
             f'@{esc(DATA["username"])} · updated every 2h</text>')
    return svg(W, H, label, "".join(b), ("serif", "serif-i", "sans", "mono"))


ACTIVITY_WEEKS = 8
NUMBER_WORDS = {6: "Six", 8: "Eight", 10: "Ten", 12: "Twelve"}


def weekly_totals(days: list[dict], n: int = ACTIVITY_WEEKS) -> list[dict]:
    """Last n calendar weeks (Sunday start, like the heatmap) as {"start", "count"}."""
    today = date.today().isoformat()
    weeks: list[dict] = []
    for day in sorted(days, key=lambda x: x["date"]):
        if day["date"] > today:
            break
        if day["weekday"] == 0 or not weeks:
            weeks.append({"start": day["date"], "count": 0})
        weeks[-1]["count"] += day["count"]
    return weeks[-n:]


def activity() -> str:
    W, H = 880, 300
    weeks = weekly_totals(DATA["days"])
    n = len(weeks)
    peak = max((w["count"] for w in weeks), default=0) or 1
    best = max(range(n), key=lambda i: weeks[i]["count"]) if n else -1
    busiest = DATA["busiest_day"]
    total = sum(w["count"] for w in weeks)
    label = (f'Weekly contributions for the last {n} weeks ({total} in total). Current streak '
             f'{DATA["current_streak"]} days, {DATA["active_days"]} active days, '
             f'busiest day {busiest["count"]} contributions.')

    b = [card_bg(W, H)]
    b.append(f'<text class="f" {d(2.0)} x="48" y="52" font-family="{MONO}" font-size="12" '
             f'letter-spacing="1.6" fill="{MUTED}">ACTIVITY · {total:,} IN {n} WEEKS</text>')
    b.append(f'<text class="r" {d(2.05)} x="48" y="88" font-family="{SERIF}" font-size="32" fill="{INK}">'
             f'{NUMBER_WORDS.get(n, n)} weeks, <tspan font-style="italic">one bar each</tspan></text>')
    # Bars fill the 528px left of the stats column whatever n is.
    base_y, max_h, bx, span = 252, 120, 48, 528
    bgap = 16
    bw = (span - (n - 1) * bgap) / max(n, 1)
    for i, w in enumerate(weeks):
        x = bx + i * (bw + bgap)
        h = max(3, max_h * w["count"] / peak)
        col = BLUE if i == best and w["count"] else (INK if w["count"] else LINE)
        b.append(f'<rect class="g" {d(2.2 + i * .07)} x="{x:.1f}" y="{base_y - h:.1f}" width="{bw:.1f}" '
                 f'height="{h:.1f}" rx="4" fill="{col}"><title>Week of {w["start"]}: {w["count"]}</title></rect>')
        b.append(f'<text x="{x + bw / 2:.1f}" y="{base_y + 20}" text-anchor="middle" font-family="{MONO}" '
                 f'font-size="10.5" fill="{BLUE if i == best else MUTED}">'
                 f'{date.fromisoformat(w["start"]):%b %d}</text>')
        if w["count"]:  # every non-empty week gets its count; the best one in blue
            b.append(f'<text class="p" {d(2.2 + n * .07 + .3 + i * .04)} x="{x + bw / 2:.1f}" '
                     f'y="{base_y - h - 9:.1f}" text-anchor="middle" font-family="{SANS}" font-weight="600" '
                     f'font-size="13" fill="{BLUE if i == best else INK}">{w["count"]}</text>')
    # stats column
    sx = 600
    b.append(f'<line x1="{sx - 24}" y1="40" x2="{sx - 24}" y2="{H - 40}" stroke="{LINE}"/>')
    stats = [
        (f'{DATA["current_streak"]}', "day streak", f'longest {DATA["longest_streak"]}'),
        (f'{DATA["active_days"]}', "active days", "in the last year"),
        (f'{busiest["count"]}', "busiest day", f'{date.fromisoformat(busiest["date"]):%d %b %Y}'),
    ]
    for i, (num, lab, sub) in enumerate(stats):
        y = 92 + i * 74
        nw = measure(num, "serif", 46)
        b.append(f'<g class="r" {d(2.4 + i * .12)}>'
                 f'<text x="{sx}" y="{y}" font-family="{SERIF}" font-size="46" fill="{INK}">{num}</text>'
                 f'<text x="{sx + nw + 10:.1f}" y="{y - 18}" font-family="{SANS}" font-weight="600" '
                 f'font-size="14" fill="{INK}">{lab}</text>'
                 f'<text x="{sx + nw + 10:.1f}" y="{y - 1}" font-family="{MONO}" font-size="10.5" '
                 f'fill="{MUTED}">{esc(sub)}</text></g>')
    return svg(W, H, label, "".join(b), ("serif", "serif-i", "sans", "sans-b", "mono"))


OPEN_SOURCE_HEADLINE_AT = 5


def pr_tile(prs: dict) -> tuple[int, str, str]:
    """(value, unit, line) for the PR tile. Open source takes the headline once it's substantial."""
    merged = int(prs.get("merged") or 0)
    ext = int(prs.get("external_merged") or 0)
    repos = int(prs.get("repos") or 0)
    if ext >= OPEN_SOURCE_HEADLINE_AT:
        orgs = int(prs.get("external_orgs") or 0)
        return ext, "open-source PRs merged", f"{orgs} orgs · {merged} PRs merged in total"
    line = f"across {repos} repo{'s' if repos != 1 else ''}"
    if ext:
        line += f" · {ext} open-source"
    return merged, "PRs merged", line


def tile(t: dict, idx: int) -> str:
    W = H = 290
    PAD = 5
    bg, fg, soft = TILE[t["color"]]
    start = 2.9 + idx * .18
    if "headline" in t:  # words instead of a number, e.g. a contact tile
        words = t["headline"].split()
        lines = [t["headline"]] if measure(t["headline"], "serif", 64) <= W - 48 else \
            [" ".join(words[:len(words) // 2 or 1]), " ".join(words[len(words) // 2 or 1:])]
        size = min(64, min((W - 48) / max(measure(ln, "serif", 1) for ln in lines), 64))
        main = "".join(
            f'<text class="r" {d(start + .35 + i * .12)} x="22" y="{170 - (len(lines) - 1 - i) * size * .92:.1f}" '
            f'font-family="{SERIF}" font-size="{size:.1f}" fill="{fg}"'
            f'{" font-style=\"italic\"" if i == len(lines) - 1 and len(lines) > 1 else ""}>{esc(ln)}</text>'
            for i, ln in enumerate(lines))
        label = f'{t["label"]}: {t["headline"]}. {t["unit"]}, {t["line"]}'
    else:
        if t["value"] == "auto:prs":
            value, unit, line = pr_tile(DATA.get("prs") or {})
            t = {**t, "unit": unit, "line": line}
        elif t["value"] == "auto:public_repos":
            value = DATA["public_repos"]
        else:
            value = int(t["value"])
        label = f'{t["label"]}: {value}{t.get("suffix", "")} {t["unit"]}. {t["line"]}'
        num_attrs = f'font-family="{SERIF}" font-size="112" fill="{fg}" letter-spacing="-2"'
        main = count_up(20, 170, value, num_attrs, begin=start + .35, suffix=t.get("suffix", ""))

    body = [f'<clipPath id="c{idx}"><rect width="{W}" height="{H}" rx="20"/></clipPath>']
    g = [f'<rect width="{W}" height="{H}" rx="20" fill="{bg}"/>',
         f'<circle class="ring" style="animation-delay:{start + 1.2:.2f}s" cx="{W - 26}" cy="26" r="40" '
         f'fill="none" stroke="{fg}" stroke-width="1.5"/>',
         f'<text x="24" y="40" font-family="{MONO}" font-size="12.5" letter-spacing="2.4" fill="{fg}">'
         f'{esc(t["label"])}</text>',
         f'<g class="nudge"><path d="M{W - 34} 38 L{W - 20} 24 M{W - 31} 24 H{W - 20} V35" '
         f'stroke="{fg}" stroke-width="2" fill="none" stroke-linecap="round"/></g>',
         main,
         f'<text x="24" y="204" font-family="{SANS}" font-weight="600" font-size="17" fill="{fg}">'
         f'{esc(t["unit"])}</text>',
         f'<text x="24" y="228" font-family="{SANS}" font-size="13" fill="{soft}">'
         f'{esc(fit(t["line"], "sans", 13, W - 48))}</text>',
         f'<line x1="24" y1="248" x2="{W - 24}" y2="248" stroke="{soft}" stroke-opacity=".5"/>',
         f'<text x="24" y="270" font-family="{MONO}" font-size="11.5" letter-spacing=".6" fill="{fg}">'
         f'→ {esc(t["cta"])}</text>']
    if not STATIC:  # glint: sweeps across in the first 25% of a 6s cycle, then rests off-tile
        g.append(f'<g transform="rotate(20)"><rect x="-170" y="-80" width="70" height="{H + 160}" '
                 f'fill="#fff" opacity=".16"><animateTransform attributeName="transform" type="translate" '
                 f'values="0 0;{W + 280} 0;{W + 280} 0" keyTimes="0;.25;1" calcMode="spline" '
                 f'keySplines=".4 0 .2 1;0 0 1 1" begin="{start + 1.6 + idx * .4:.2f}s" dur="6s" '
                 f'repeatCount="indefinite"/></rect></g>')
    body.append(f'<g transform="translate({PAD} {PAD})"><g class="s" {d(start)} clip-path="url(#c{idx})">'
                f'{"".join(g)}</g></g>')
    return svg(W + 2 * PAD, H + 2 * PAD, label, "".join(body), ("serif", "sans", "sans-b", "mono"))


def title() -> str:
    """Section header on its own paper card, so it reads on any page background
    (GitHub light/dark, or a browser extension that darkens the page)."""
    W, H = 880, 96
    label = "What I'm coding"
    x0, base = 48, 62
    caret_x = x0 + measure("What I’m ", "serif", 40) + measure("coding", "serif-i", 40) + 6
    b = [f'<g class="f" {d(3.5)}>{card_bg(W, H)}</g>',
         f'<text class="r" {d(3.6)} x="{x0}" y="{base}" font-family="{SERIF}" font-size="40" fill="{INK}">'
         f'What I’m <tspan font-style="italic" fill="{BLUE}">coding</tspan></text>',
         f'<g class="f" {d(3.9)}><rect class="caret" x="{caret_x:.1f}" y="{base - 30}" width="3" '
         f'height="34" fill="{INK}"/></g>',
         f'<text class="f" {d(3.8)} x="{W - x0}" y="{base - 2}" text-anchor="end" font-family="{MONO}" '
         f'font-size="11.5" letter-spacing="1" fill="{MUTED}">FEATURED REPOS ↓</text>']
    return svg(W, H, label, "".join(b), ("serif", "serif-i", "mono"))


def repo_card(r: dict, idx: int) -> str:
    W, H = 290, 188
    PAD = 5
    titles = PROFILE.get("repo_titles", {})
    name = titles.get(r["name"], r["name"])
    desc = PROFILE.get("repo_descriptions", {}).get(r["name"]) or r["description"] or next(
        (p["description"] for p in PROFILE.get("projects", []) if p["url"].rstrip("/").lower() == r["url"].lower()),
        "")
    lines = wrap(desc, "sans", 13, W - 48, 3)
    start = 4.0 + idx * .15
    label = f'{name}: {desc}'
    b = [f'<g class="f" {d(start - .15)}>{card_bg(W, H)}</g>']
    b.append(f'<g class="r" {d(start)}>'
             f'<text x="24" y="38" font-family="{MONO}" font-size="11" letter-spacing="1.4" fill="{MUTED}">'
             f'REPO · {idx + 1:02d}</text>'
             f'<g class="nudge"><path d="M{W - 36} 36 L{W - 24} 24 M{W - 33} 24 H{W - 24} V33" '
             f'stroke="{INK}" stroke-width="1.7" fill="none" stroke-linecap="round"/></g>'
             f'<text x="22" y="74" font-family="{SERIF}" font-size="28" fill="{INK}">'
             f'{esc(fit(name, "serif", 28, W - 46))}</text></g>')
    for i, line in enumerate(lines):
        b.append(f'<text class="r" {d(start + .1 + i * .05)} x="24" y="{102 + i * 19}" '
                 f'font-family="{SANS}" font-size="13" fill="{BODY}">{esc(line)}</text>')
    lang = r["language"] or "Code"
    b.append(f'<g class="f" {d(start + .35)}>'
             f'<line x1="24" y1="{H - 42}" x2="{W - 24}" y2="{H - 42}" stroke="{LINE}"/>'
             f'<circle cx="29" cy="{H - 21}" r="5" fill="{LANG.get(lang, BLUE)}"/>'
             f'<text x="41" y="{H - 17}" font-family="{MONO}" font-size="11" fill="{BODY}">{esc(lang)}</text>'
             f'</g>')  # no star count: every featured repo is at 0 for now
    inner = f'<g transform="translate({PAD} {PAD})">{"".join(b)}</g>'
    return svg(W + 2 * PAD, H + 2 * PAD, label, inner, ("serif", "sans", "mono"))


# ---- tech stack marquee ----------------------------------------------------
ICON, PITCH = 44, 80          # icon size and centre-to-centre spacing, px
MARQUEE_SPEED = 40            # px per second
MIN_CONTRAST = 1.6            # below this vs PAPER, an icon gets an INK backplate


def _luminance(hex_: str) -> float:
    h = hex_.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio between two hex colours."""
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def needs_plate(icon: dict) -> bool:
    return contrast(icon["hex"], PAPER) < MIN_CONTRAST


def icon_symbol(slug: str, icon: dict) -> str:
    """<symbol> in the icons' native 24x24 grid, brand colour baked in."""
    path = f'fill="{icon["hex"]}" fill-rule="{icon["rule"]}" d="{icon["path"]}"'
    if needs_plate(icon):
        # Full-bleed logos (the JS square) sit flush on the plate so its cut-out letters
        # read as ink, exactly like the official mark; others get an inset.
        full = icon["path"].startswith("M0 0h24v24H0")
        inner = f'<path {path}/>' if full else f'<path transform="translate(4.5 4.5) scale(.625)" {path}/>'
        return (f'<symbol id="i-{slug}" viewBox="0 0 24 24"><rect width="24" height="24" '
                f'rx="{0 if full else 5}" fill="{INK}"/>{inner}</symbol>')
    return f'<symbol id="i-{slug}" viewBox="0 0 24 24"><path {path}/></symbol>'


def marquee_rows() -> list[dict]:
    """Row geometry, shared by the renderer and the tests."""
    stack = PROFILE["tech_stack"]
    rows = []
    for i, (key, direction) in enumerate((("top", "right"), ("bottom", "left"))):
        slugs = stack[key]
        width = len(slugs) * PITCH
        rows.append({"id": f"mq{i + 1}", "slugs": slugs, "width": width, "direction": direction,
                     "duration": round(width / MARQUEE_SPEED, 2)})
    return rows


def tech_stack() -> str:
    W, H = 880, 268
    icons = json.loads((ROOT / "data" / "icons.json").read_text(encoding="utf-8"))
    rows = marquee_rows()
    slugs = list(dict.fromkeys(s for r in rows for s in r["slugs"]))
    titles = [icons[s]["title"] for s in slugs]
    label = f'Tech stack: {", ".join(titles)}.'

    defs = ["".join(icon_symbol(s, icons[s]) for s in slugs)]
    css = []
    for r in rows:
        x0 = (PITCH - ICON) / 2
        defs.append(f'<g id="{r["id"]}-set">' + "".join(
            f'<use href="#i-{s}" x="{x0 + i * PITCH:g}" y="0" width="{ICON}" height="{ICON}"/>'
            for i, s in enumerate(r["slugs"])) + "</g>")
        frm, to = (f'-{r["width"]}px', "0px") if r["direction"] == "right" else ("0px", f'-{r["width"]}px')
        css.append(f'@keyframes {r["id"]}{{from{{transform:translateX({frm})}}to{{transform:translateX({to})}}}}'
                   f'.{r["id"]}{{animation:{r["id"]} {r["duration"]}s linear infinite}}')
    # Fade icons in/out at the card edges; clip to the rounded card.
    edge = 72 / W
    defs.append(f'<linearGradient id="edge" x1="0" x2="1" y1="0" y2="0">'
                f'<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                f'<stop offset="{edge:.3f}" stop-color="#fff"/><stop offset="{1 - edge:.3f}" stop-color="#fff"/>'
                f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                f'<mask id="fade"><rect width="{W}" height="{H}" fill="url(#edge)"/></mask>'
                f'<clipPath id="card"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="17"/></clipPath>')

    b = [card_bg(W, H)]
    b.append(f'<text class="f" {d(3.3)} x="48" y="52" font-family="{MONO}" font-size="12" '
             f'letter-spacing="1.6" fill="{MUTED}">TECH STACK · {len(slugs)} TOOLS</text>')
    b.append(f'<text class="r" {d(3.35)} x="48" y="88" font-family="{SERIF}" font-size="32" fill="{INK}">'
             f'The stack, <tspan font-style="italic">end to end</tspan></text>')
    b.append(f'<text class="f" {d(3.4)} x="{W - 48}" y="52" text-anchor="end" font-family="{MONO}" '
             f'font-size="11" letter-spacing=".6" fill="{MUTED}">VERIFIED FROM MY REPOS</text>')
    rows_svg = "".join(
        f'<g transform="translate(0 {116 + i * 76})"><g class="{r["id"]}">'
        f'<use href="#{r["id"]}-set"/><use href="#{r["id"]}-set" x="{r["width"]}"/></g></g>'
        for i, r in enumerate(rows))
    b.append(f'<g class="f" {d(3.45)} clip-path="url(#card)"><g mask="url(#fade)">{rows_svg}</g></g>')
    return svg(W, H, label, "".join(b), ("serif", "serif-i", "mono"), css="".join(css), defs="".join(defs))


def link_pill(link: dict, idx: int) -> str:
    """Small footer button: mono label + arrow, same paper style as the repo cards."""
    W, H, PAD = 200, 52, 4
    start = 4.6 + idx * .08
    text = link["label"].upper()
    tw = measure(text, "mono", 12) + 1.6 * (len(text) - 1)  # include letter-spacing
    x0 = (W - tw - 22) / 2
    b = [card_bg(W, H),
         f'<text x="{x0:.1f}" y="{H / 2 + 4.5}" font-family="{MONO}" font-size="12" letter-spacing="1.6" '
         f'fill="{INK}">{esc(text)}</text>',
         f'<g class="nudge"><path d="M{x0 + tw + 12:.1f} {H / 2 + 5} l9 -9 m-7 0 h7 v7" stroke="{BLUE}" '
         f'stroke-width="1.7" fill="none" stroke-linecap="round"/></g>']
    inner = f'<g class="f" {d(start)} transform="translate({PAD} {PAD})">{"".join(b)}</g>'
    return svg(W + 2 * PAD, H + 2 * PAD, link["label"], inner, ("mono",))


def slug(name: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")[:40]


def main() -> None:
    CARDS.mkdir(exist_ok=True)
    out = {"hero.svg": hero(), "heatmap.svg": heatmap(), "activity.svg": activity(),
           "title-coding.svg": title(), "tech-stack.svg": tech_stack()}
    for i, t in enumerate(PROFILE["tiles"]):
        out[f'{t["id"]}.svg'] = tile(t, i)
    for i, r in enumerate(DATA["repos"]):
        out[f'repo-{slug(r["name"])}.svg'] = repo_card(r, i)
    for i, link in enumerate(PROFILE.get("links", [])):
        out[f'link-{slug(link["label"])}.svg'] = link_pill(link, i)
    stale = {p.name for p in CARDS.glob("*.svg")} - set(out)
    for name in stale:
        (CARDS / name).unlink()
    for name, content in out.items():
        (CARDS / name).write_text(content, encoding="utf-8", newline="\n")
        print(f"{name:42s} {len(content.encode()) / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
