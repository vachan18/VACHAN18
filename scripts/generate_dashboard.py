#!/usr/bin/env python3
"""
VACHAN.EXE — Cyberpunk GitHub Profile Dashboard Generator
Generates:
  - assets/dossier.svg   (Full cyberpunk intelligence engineering dossier)
  - assets/telemetry.svg (Dedicated real-time telemetry HUD card)
  - README.md            (Concise cyberpunk markdown dossier with functional links)
"""

import json
import os
import sys
import html
import urllib.request
import urllib.error
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

# Resolve repository paths
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "scripts" else SCRIPT_DIR
PROFILE_DATA_PATH = ROOT / "profile-data.json"
ASSETS_DIR = ROOT / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Standard typography stacks for SVG rendering across all client platforms
FONT_MONO = "ui-monospace, 'SF Mono', Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace"
FONT_SANS = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

# Load profile data
if not PROFILE_DATA_PATH.exists():
    raise FileNotFoundError(f"Missing required profile data at {PROFILE_DATA_PATH}")

DATA = json.loads(PROFILE_DATA_PATH.read_text(encoding="utf-8"))
USER = DATA.get("username", "vachan18")

def get_auth_token():
    """Resolve token from GITHUB_TOKEN env var, or local gh CLI if available."""
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token and shutil.which("gh"):
        try:
            token = subprocess.check_output(
                ["gh", "auth", "token"],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
        except Exception:
            token = ""
    return token

TOKEN = get_auth_token()

def github_api_get(endpoint):
    """Query the GitHub REST API with timeout, rate-limit awareness, and auth."""
    url = endpoint if endpoint.startswith("http") else f"https://api.github.com{endpoint}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": f"Cyberpunk-Dashboard-Generator/{USER}"
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data)
    except urllib.error.HTTPError as err:
        remaining = err.headers.get("x-ratelimit-remaining", "unknown")
        print(f"[WARN] GitHub API HTTP {err.code} on {url}. Rate limit remaining: {remaining}")
        raise
    except Exception as exc:
        print(f"[ERROR] Failed fetching {url}: {exc}")
        raise

def esc(s):
    """Escape text for XML / SVG."""
    return html.escape(str(s), quote=True)

def wrap_text(text, max_chars):
    """Split text cleanly into lines respecting word boundaries."""
    words = str(text).split()
    lines = []
    current_line = []
    current_len = 0
    for w in words:
        if current_len + len(w) + (1 if current_line else 0) <= max_chars:
            current_line.append(w)
            current_len += len(w) + (1 if current_line else 0)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [w]
            current_len = len(w)
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def panel_path(x, y, w, h, notch=18):
    """Generate an asymmetric cyberpunk chamfered polygon path."""
    return (
        f"M {x + notch} {y} "
        f"H {x + w - notch} "
        f"L {x + w} {y + notch} "
        f"V {y + h - notch} "
        f"L {x + w - notch} {y + h} "
        f"H {x + notch} "
        f"L {x} {y + h - notch} "
        f"V {y + notch} "
        f"Z"
    )

def panel_hud(x, y, w, h, title, accent="#FF168A", tag="SEC-SYS // CLASSIFIED"):
    """Render a cyberpunk HUD panel frame with title bar, coordinates, and corner brackets."""
    p_path = panel_path(x, y, w, h, notch=18)
    corner_decor = [
        f'<path d="{p_path}" fill="#080D17" stroke="{accent}" stroke-width="1.6" opacity="0.95"/>',
        f'<path d="M {x+2} {y+32} H {x+w-2}" stroke="{accent}" stroke-width="0.8" opacity="0.4"/>',
        # Top-left bracket
        f'<path d="M {x+6} {y+16} L {x+16} {y+6}" stroke="#20E8FF" stroke-width="2" fill="none"/>',
        # Bottom-right bracket
        f'<path d="M {x+w-16} {y+h-6} L {x+w-6} {y+h-16}" stroke="#20E8FF" stroke-width="2" fill="none"/>',
        # Title
        f'<text x="{x+24}" y="{y+23}" fill="{accent}" font-size="14" font-weight="700" font-family="{FONT_MONO}" letter-spacing="1.5">{esc(title)}</text>',
        # Tag
        f'<text x="{x+w-24}" y="{y+23}" fill="#6C879B" font-size="11" font-weight="600" font-family="{FONT_MONO}" text-anchor="end" letter-spacing="1">{esc(tag)}</text>',
    ]
    return "".join(corner_decor)

def generate_dossier_svg(user, repos, stars, languages, stamp):
    """Generate comprehensive assets/dossier.svg (1500x1040)."""
    public_repos_cnt = user.get("public_repos", len(repos))
    followers_cnt = user.get("followers", 0)
    following_cnt = user.get("following", 0)

    svg = []
    svg.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1040" viewBox="0 0 1500 1040">')
    svg.append('''<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0%" stop-color="#050811"/>
  <stop offset="45%" stop-color="#0A1021"/>
  <stop offset="100%" stop-color="#04060D"/>
</linearGradient>
<linearGradient id="glow-cyan" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%" stop-color="#00F0FF"/>
  <stop offset="100%" stop-color="#0080FF"/>
</linearGradient>
<linearGradient id="glow-magenta" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%" stop-color="#FF168A"/>
  <stop offset="100%" stop-color="#9A00FF"/>
</linearGradient>
<linearGradient id="glow-duo" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0%" stop-color="#FF168A"/>
  <stop offset="50%" stop-color="#7B2CBF"/>
  <stop offset="100%" stop-color="#20E8FF"/>
</linearGradient>
<pattern id="cyber-grid" width="32" height="32" patternUnits="userSpaceOnUse">
  <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#162A3E" stroke-width="0.8" opacity="0.32"/>
</pattern>
<filter id="neon-glow" x="-20%" y="-20%" width="140%" height="140%">
  <feGaussianBlur stdDeviation="3" result="blur"/>
  <feComposite in="SourceGraphic" in2="blur" operator="over"/>
</filter>
</defs>''')

    # Main canvas & borders
    svg.append('<rect width="1500" height="1040" fill="url(#bg)"/>')
    svg.append('<rect width="1500" height="1040" fill="url(#cyber-grid)"/>')
    svg.append('<rect x="12" y="12" width="1476" height="1016" rx="10" fill="none" stroke="url(#glow-duo)" stroke-width="1.8" opacity="0.85"/>')

    # Global decorative HUD header line
    svg.append(f'<text x="36" y="22" fill="#5F7D95" font-size="10" font-family="{FONT_MONO}" letter-spacing="2">SYS-ID: VACHAN-18 // PROTOCOL: CYBER-ENG // NODE: BANGALORE-IN</text>')
    svg.append(f'<text x="1464" y="22" fill="#5F7D95" font-size="10" font-family="{FONT_MONO}" letter-spacing="2" text-anchor="end">STATUS: OPERATIONAL // SYNC: {esc(stamp)} UTC</text>')

    # ==========================================
    # PANEL 01 — OPERATOR IDENTITY (Top-Left)
    # ==========================================
    p1_x, p1_y, p1_w, p1_h = 28, 36, 700, 344
    svg.append(panel_hud(p1_x, p1_y, p1_w, p1_h, "PANEL 01 // OPERATOR IDENTITY", "#FF168A", "CLEARANCE: LVL-4"))

    # Operator Avatar / Cyber ID Box
    svg.append(f'<rect x="{p1_x+24}" y="{p1_y+48}" width="88" height="88" rx="8" fill="#0C1524" stroke="#20E8FF" stroke-width="1.4"/>')
    svg.append(f'<text x="{p1_x+68}" y="{p1_y+94}" fill="#20E8FF" font-size="34" font-weight="700" font-family="{FONT_MONO}" text-anchor="middle">V</text>')
    svg.append(f'<text x="{p1_x+68}" y="{p1_y+122}" fill="#FF168A" font-size="10" font-weight="700" font-family="{FONT_MONO}" text-anchor="middle">EXE.01</text>')

    # Name and Title
    svg.append(f'<text x="{p1_x+128}" y="{p1_y+76}" fill="#FFFFFF" font-size="30" font-weight="800" font-family="{FONT_SANS}" letter-spacing="0.5">{esc(DATA["name"])}</text>')
    svg.append(f'<text x="{p1_x+128}" y="{p1_y+102}" fill="#20E8FF" font-size="13" font-weight="700" font-family="{FONT_MONO}" letter-spacing="1">{esc(DATA["role"].upper())} @ {esc(DATA["company"].upper())}</text>')
    svg.append(f'<text x="{p1_x+128}" y="{p1_y+124}" fill="#FF4BA8" font-size="11.5" font-family="{FONT_MONO}">Bangalore, India · Computer Science &amp; Engineering</text>')

    # Bio block
    bio_lines = wrap_text(DATA["bio"], 66)
    for idx, bline in enumerate(bio_lines[:2]):
        svg.append(f'<text x="{p1_x+24}" y="{p1_y+162 + idx*20}" fill="#D5E5F2" font-size="13" font-family="{FONT_SANS}">{esc(bline)}</text>')

    # Metadata Grid Boxes (2x2)
    meta_items = [
        ("ORGANIZATION", DATA.get("company", "Synapx"), "#20E8FF"),
        ("LOCATION", DATA.get("location", "Bangalore, India"), "#FF4BA8"),
        ("EDUCATION", "Dr. Ambedkar Inst. of Tech (2022-26)", "#20E8FF"),
        ("SYSTEM STATUS", "ACTIVE // DEPLOYED IN PROD", "#00FF9D")
    ]
    for idx, (lbl, val, col) in enumerate(meta_items):
        mx = p1_x + 24 + (idx % 2) * 332
        my = p1_y + 208 + (idx // 2) * 48
        svg.append(f'<rect x="{mx}" y="{my}" width="316" height="40" rx="4" fill="#0C1524" stroke="#1F3347" stroke-width="1"/>')
        svg.append(f'<text x="{mx+12}" y="{my+16}" fill="#7693A8" font-size="10" font-family="{FONT_MONO}" font-weight="600">{esc(lbl)}</text>')
        svg.append(f'<text x="{mx+12}" y="{my+31}" fill="{col}" font-size="11.5" font-family="{FONT_MONO}" font-weight="700">{esc(val)}</text>')

    # Bottom status badge
    svg.append(f'<text x="{p1_x+24}" y="{p1_y+326}" fill="#5F7D95" font-size="10.5" font-family="{FONT_MONO}" letter-spacing="1">CORE FOCUS: AI SYSTEMS · BACKEND INFRASTRUCTURE · CLOUD &amp; DATA PIPELINES</text>')

    # ==========================================
    # PANEL 02 — TECHNOLOGY MATRIX (Top-Right)
    # ==========================================
    p2_x, p2_y, p2_w, p2_h = 756, 36, 716, 344
    svg.append(panel_hud(p2_x, p2_y, p2_w, p2_h, "PANEL 02 // TECHNOLOGY CAPABILITY MATRIX", "#20E8FF", "CAP-MATRIX.SYS"))

    skills = DATA.get("skills", {})
    skill_rows = [
        ("LANGUAGES", skills.get("Languages", []), "#FF168A"),
        ("FRAMEWORKS", skills.get("Frameworks", []), "#20E8FF"),
        ("AI & MACHINE LEARNING", skills.get("AI & ML", []), "#00FF9D"),
        ("CLOUD & DATA", skills.get("Cloud & Data", []), "#20E8FF"),
        ("ENGINEERING & DEVOPS", skills.get("Engineering", []), "#FF4BA8")
    ]

    for idx, (cat, items, cat_col) in enumerate(skill_rows):
        ry = p2_y + 50 + idx * 56
        svg.append(f'<text x="{p2_x+24}" y="{ry+12}" fill="{cat_col}" font-size="11.5" font-weight="700" font-family="{FONT_MONO}" letter-spacing="1">{esc(cat)}</text>')
        tx = p2_x + 24
        ty = ry + 28
        items_str = "  ·  ".join(items[:6])
        svg.append(f'<text x="{tx}" y="{ty+4}" fill="#E2F0FB" font-size="11.5" font-family="{FONT_MONO}">{esc(items_str)}</text>')
        if idx < len(skill_rows) - 1:
            svg.append(f'<path d="M {p2_x+24} {ry+44} H {p2_x+p2_w-24}" stroke="#1A2D3E" stroke-width="0.8"/>')

    # ==========================================
    # PANEL 03 — PROJECT ARCHIVE (Bottom-Left)
    # ==========================================
    p3_x, p3_y, p3_w, p3_h = 28, 396, 936, 616
    svg.append(panel_hud(p3_x, p3_y, p3_w, p3_h, "PANEL 03 // CLASSIFIED PROJECT ARCHIVE", "#FF168A", "6 CORE BUILDS"))

    projects = DATA.get("projects", [])[:6]
    card_w = 286
    card_h = 265
    card_gap_x = 15
    card_gap_y = 16

    for idx, proj in enumerate(projects):
        col = idx % 3
        row = idx // 3
        cx = p3_x + 24 + col * (card_w + card_gap_x)
        cy = p3_y + 46 + row * (card_h + card_gap_y)

        # Card container
        svg.append(f'<rect x="{cx}" y="{cy}" width="{card_w}" height="{card_h}" rx="6" fill="#0C1524" stroke="#22394F" stroke-width="1.2"/>')
        # Accent top bar
        bar_col = "#FF168A" if row == 0 else "#20E8FF"
        svg.append(f'<rect x="{cx}" y="{cy}" width="{card_w}" height="3" rx="1.5" fill="{bar_col}"/>')

        # Build ID & Category
        svg.append(f'<text x="{cx+14}" y="{cy+24}" fill="#20E8FF" font-size="11" font-weight="700" font-family="{FONT_MONO}">SYS-{idx+1:02d}</text>')
        cat_text = esc(proj.get("category",""))
        svg.append(f'<text x="{cx+card_w-14}" y="{cy+24}" fill="#FF4BA8" font-size="9.5" font-weight="700" font-family="{FONT_MONO}" text-anchor="end">{cat_text}</text>')

        # Project Name (wrapped)
        name_lines = wrap_text(proj.get("name", ""), 22)
        for n_i, n_line in enumerate(name_lines[:2]):
            svg.append(f'<text x="{cx+14}" y="{cy+50 + n_i*19}" fill="#FFFFFF" font-size="14.5" font-weight="700" font-family="{FONT_SANS}">{esc(n_line)}</text>')

        # Project Description (wrapped)
        desc_lines = wrap_text(proj.get("description", ""), 32)
        desc_start_y = cy + 94
        for d_i, d_line in enumerate(desc_lines[:3]):
            svg.append(f'<text x="{cx+14}" y="{desc_start_y + d_i*17}" fill="#A6BFD2" font-size="11.5" font-family="{FONT_SANS}">{esc(d_line)}</text>')

        # Stack pills
        stack = proj.get("stack", [])
        stack_text = " · ".join(stack[:3])
        if len(stack_text) > 34:
            stack_text = stack_text[:31] + "..."
        svg.append(f'<rect x="{cx+12}" y="{cy+card_h-54}" width="{card_w-24}" height="22" rx="4" fill="#132032" stroke="#1F364E" stroke-width="0.8"/>')
        svg.append(f'<text x="{cx+18}" y="{cy+card_h-39}" fill="#20E8FF" font-size="10" font-weight="600" font-family="{FONT_MONO}">{esc(stack_text)}</text>')

        # Link button
        svg.append(f'<text x="{cx+14}" y="{cy+card_h-14}" fill="#FF168A" font-size="11" font-weight="700" font-family="{FONT_MONO}" letter-spacing="0.5">OPEN REPOSITORY ↗</text>')

    # ==========================================
    # PANEL 04 — GITHUB TELEMETRY (Bottom-Right)
    # ==========================================
    p4_x, p4_y, p4_w, p4_h = 988, 396, 484, 616
    svg.append(panel_hud(p4_x, p4_y, p4_w, p4_h, "PANEL 04 // GITHUB TELEMETRY", "#20E8FF", "LIVE METRICS"))

    # 4 Stat HUD Cards
    stats = [
        ("PUBLIC REPOS", public_repos_cnt, "#20E8FF"),
        ("TOTAL STARS", stars, "#FF168A"),
        ("FOLLOWERS", followers_cnt, "#20E8FF"),
        ("FOLLOWING", following_cnt, "#00FF9D"),
    ]
    stat_box_w = 206
    stat_box_h = 76
    for idx, (label, val, col) in enumerate(stats):
        col_idx = idx % 2
        row_idx = idx // 2
        sx = p4_x + 24 + col_idx * (stat_box_w + 24)
        sy = p4_y + 46 + row_idx * (stat_box_h + 14)

        svg.append(f'<rect x="{sx}" y="{sy}" width="{stat_box_w}" height="{stat_box_h}" rx="6" fill="#0C1524" stroke="#1F3347" stroke-width="1.2"/>')
        svg.append(f'<text x="{sx+14}" y="{sy+22}" fill="#7B9BB2" font-size="10" font-weight="700" font-family="{FONT_MONO}">{esc(label)}</text>')
        svg.append(f'<text x="{sx+14}" y="{sy+58}" fill="{col}" font-size="28" font-weight="800" font-family="{FONT_MONO}">{esc(val)}</text>')

    # Language breakdown header
    svg.append(f'<text x="{p4_x+24}" y="{p4_y+242}" fill="#FF168A" font-size="12.5" font-weight="700" font-family="{FONT_MONO}" letter-spacing="1">CODEBASE LANGUAGE DISTRIBUTION</text>')

    total_bytes = sum(languages.values()) if languages else 0
    top_langs = list(languages.items())[:6] if languages else []

    if top_langs and total_bytes > 0:
        bar_max_w = 230
        for l_idx, (lang, b_cnt) in enumerate(top_langs):
            ly = p4_y + 274 + l_idx * 41
            pct = (b_cnt / total_bytes) * 100
            bar_w = max(int(bar_max_w * (b_cnt / total_bytes)), 6)
            display_lang = lang if len(lang) <= 17 else lang[:15] + "…"

            # Lang name
            svg.append(f'<text x="{p4_x+24}" y="{ly+12}" fill="#FFFFFF" font-size="11.5" font-weight="600" font-family="{FONT_SANS}">{esc(display_lang)}</text>')
            # Pct
            svg.append(f'<text x="{p4_x+192}" y="{ly+12}" fill="#20E8FF" font-size="11" font-weight="700" font-family="{FONT_MONO}" text-anchor="end">{pct:.1f}%</text>')
            # Track
            svg.append(f'<rect x="{p4_x+206}" y="{ly+2}" width="{bar_max_w}" height="10" rx="5" fill="#142132"/>')
            # Fill bar
            grad = "url(#glow-magenta)" if l_idx % 2 == 0 else "url(#glow-cyan)"
            svg.append(f'<rect x="{p4_x+206}" y="{ly+2}" width="{bar_w}" height="10" rx="5" fill="{grad}"/>')
    else:
        svg.append(f'<text x="{p4_x+24}" y="{p4_y+290}" fill="#8CA7BC" font-size="12" font-family="{FONT_MONO}">Language distribution syncing...</text>')

    # Diagnostics Box at bottom
    diag_y = p4_y + 534
    svg.append(f'<rect x="{p4_x+24}" y="{diag_y}" width="{p4_w-48}" height="62" rx="4" fill="#0C1524" stroke="#1F3347" stroke-width="1"/>')
    svg.append(f'<text x="{p4_x+36}" y="{diag_y+19}" fill="#00FF9D" font-size="10" font-weight="700" font-family="{FONT_MONO}">● NODE STATUS: ONLINE [200 OK]</text>')
    svg.append(f'<text x="{p4_x+36}" y="{diag_y+36}" fill="#7B9BB2" font-size="10" font-family="{FONT_MONO}">ENGINE: PYTHON 3.12 // GITHUB ACTIONS</text>')
    svg.append(f'<text x="{p4_x+36}" y="{diag_y+51}" fill="#7B9BB2" font-size="10" font-family="{FONT_MONO}">SYNC: {esc(stamp)} UTC</text>')

    svg.append('</svg>')
    out_svg = "\n".join(svg)

    # Validate XML
    ET.fromstring(out_svg)

    # Safe write
    dossier_path = ASSETS_DIR / "dossier.svg"
    dossier_path.write_text(out_svg, encoding="utf-8")
    print(f"[OK] Generated {dossier_path} ({len(out_svg)} bytes)")

def generate_telemetry_svg(user, repos, stars, languages, stamp):
    """Generate dedicated assets/telemetry.svg (800x420 standalone HUD)."""
    public_repos_cnt = user.get("public_repos", len(repos))
    followers_cnt = user.get("followers", 0)
    following_cnt = user.get("following", 0)
    total_bytes = sum(languages.values()) if languages else 0
    top_langs = list(languages.items())[:5] if languages else []

    svg = []
    svg.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="420" viewBox="0 0 800 420">')
    svg.append('''<defs>
<linearGradient id="t-bg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0%" stop-color="#060913"/>
  <stop offset="100%" stop-color="#0C1425"/>
</linearGradient>
<linearGradient id="t-cyan" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%" stop-color="#00F0FF"/>
  <stop offset="100%" stop-color="#0080FF"/>
</linearGradient>
<linearGradient id="t-magenta" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%" stop-color="#FF168A"/>
  <stop offset="100%" stop-color="#7B2CBF"/>
</linearGradient>
</defs>''')
    svg.append('<rect width="800" height="420" fill="url(#t-bg)" rx="12" stroke="#20E8FF" stroke-width="1.8"/>')
    svg.append(f'<text x="24" y="32" fill="#20E8FF" font-size="13" font-weight="700" font-family="{FONT_MONO}" letter-spacing="1.5">TELEMETRY // GITHUB LIVE METRICS</text>')
    svg.append(f'<text x="776" y="32" fill="#FF168A" font-size="11" font-weight="700" font-family="{FONT_MONO}" text-anchor="end">SYNC: {esc(stamp)} UTC</text>')
    svg.append('<path d="M 24 44 H 776" stroke="#1E364C" stroke-width="1"/>')

    # 4 HUD Stat blocks
    stats = [
        ("PUBLIC REPOS", public_repos_cnt, "#20E8FF"),
        ("TOTAL STARS", stars, "#FF168A"),
        ("FOLLOWERS", followers_cnt, "#20E8FF"),
        ("FOLLOWING", following_cnt, "#00FF9D")
    ]
    box_w = 176
    gap = 16
    for idx, (label, val, col) in enumerate(stats):
        bx = 24 + idx * (box_w + gap)
        by = 60
        svg.append(f'<rect x="{bx}" y="{by}" width="{box_w}" height="74" rx="6" fill="#0E192B" stroke="#1F364E" stroke-width="1"/>')
        svg.append(f'<text x="{bx+14}" y="{by+22}" fill="#7898B0" font-size="10" font-weight="700" font-family="{FONT_MONO}">{esc(label)}</text>')
        svg.append(f'<text x="{bx+14}" y="{by+56}" fill="{col}" font-size="28" font-weight="800" font-family="{FONT_MONO}">{esc(val)}</text>')

    # Language Distribution
    svg.append(f'<text x="24" y="168" fill="#FF168A" font-size="12.5" font-weight="700" font-family="{FONT_MONO}" letter-spacing="1">LANGUAGE VOLUME DISTRIBUTION</text>')

    if top_langs and total_bytes > 0:
        bar_max_w = 560
        for l_idx, (lang, b_cnt) in enumerate(top_langs):
            ly = 192 + l_idx * 38
            pct = (b_cnt / total_bytes) * 100
            bar_w = max(int(bar_max_w * (b_cnt / total_bytes)), 8)
            display_lang = lang if len(lang) <= 18 else lang[:16] + "…"
            svg.append(f'<text x="24" y="{ly+14}" fill="#FFFFFF" font-size="12" font-weight="600" font-family="{FONT_SANS}">{esc(display_lang)}</text>')
            svg.append(f'<text x="190" y="{ly+14}" fill="#20E8FF" font-size="11" font-weight="700" font-family="{FONT_MONO}" text-anchor="end">{pct:.1f}%</text>')
            svg.append(f'<rect x="204" y="{ly+4}" width="{bar_max_w}" height="10" rx="5" fill="#142234"/>')
            grad = "url(#t-magenta)" if l_idx % 2 == 0 else "url(#t-cyan)"
            svg.append(f'<rect x="204" y="{ly+4}" width="{bar_w}" height="10" rx="5" fill="{grad}"/>')

    # Footer note
    svg.append(f'<text x="24" y="398" fill="#5F7D95" font-size="10" font-family="{FONT_MONO}">DATA REFRESHED AUTOMATICALLY VIA GITHUB ACTIONS // API.GITHUB.COM</text>')
    svg.append('</svg>')

    out_svg = "\n".join(svg)
    ET.fromstring(out_svg)
    telemetry_path = ASSETS_DIR / "telemetry.svg"
    telemetry_path.write_text(out_svg, encoding="utf-8")
    print(f"[OK] Generated {telemetry_path} ({len(out_svg)} bytes)")

def generate_readme(user, repos, stars, stamp):
    """Generate concise, cyberpunk engineering README.md."""
    # Build project rows
    proj_rows = []
    for p in DATA.get("projects", []):
        name = esc(p.get("name", ""))
        cat = esc(p.get("category", ""))
        url = esc(p.get("url", ""))
        repo_slug = url.replace("https://github.com/", "")
        proj_rows.append(
            f"| **{name}** | {cat} | [`{repo_slug} ↗`]({url}) |"
        )

    # Build career entries
    exp_md = []
    for e in DATA.get("experience", []):
        period = esc(e.get("period", ""))
        title = esc(e.get("title", ""))
        org = esc(e.get("organization", ""))
        detail = esc(e.get("detail", ""))
        exp_md.append(f"- **{title}** · {org} _({period})_{' — ' + detail if detail else ''}")

    additional_md = "\n".join(f"- {esc(item)}" for item in DATA.get("additional", []))

    content = f"""<div align="center">

<img src="./assets/dossier.svg" width="100%" alt="Vachan U S — Cyberpunk Engineering Dossier"/>

<a href="https://github.com/{USER}"><strong>GITHUB</strong></a> ·
<a href="{DATA.get('linkedin', '')}"><strong>LINKEDIN</strong></a> ·
<a href="{DATA.get('portfolio', '')}"><strong>PORTFOLIO</strong></a> ·
<a href="{DATA.get('devfolio', '')}"><strong>DEVFOLIO</strong></a> ·
<a href="mailto:{DATA.get('email', '')}"><strong>EMAIL</strong></a>

</div>

## 🛰️ OPERATOR BRIEFING

**{DATA.get('name', 'Vachan U S')} — {DATA.get('role', 'Software Engineer')} @ {DATA.get('company', 'Synapx')}**

{DATA.get('bio', '')}

- 📍 **Location:** {DATA.get('location', 'Bangalore, India')}
- 🎓 **Education:** {DATA.get('education', '')}
- ⚡ **Focus:** AI Systems · Distributed Backend Infrastructure · Cloud & Data Pipelines

---

## 📂 PROJECT REPOSITORIES

Direct source links for systems featured in the Cyberpunk Dossier:

| SYSTEM | SPECIALIZATION | REPOSITORY |
|---|---|---|
{chr(10).join(proj_rows)}

---

## 🎖️ CAREER & CREDENTIALS

{chr(10).join(exp_md)}

**Technical Certifications & Activities:**
{additional_md}

---

## ⚡ TELEMETRY & CONTRIBUTION NETWORK

<div align="center">
  <img src="./assets/telemetry.svg" width="100%" alt="Vachan U S — Live GitHub Telemetry HUD"/>
</div>

<br/>

<div align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/{USER}/{USER}/output/github-contribution-grid-snake-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/{USER}/{USER}/output/github-contribution-grid-snake.svg">
  <img alt="GitHub Contribution Snake" src="https://raw.githubusercontent.com/{USER}/{USER}/output/github-contribution-grid-snake-dark.svg" width="100%"/>
</picture>
</div>

---

<div align="center">

**THINK DIFFERENTLY. BUILD INTELLIGENTLY. ENGINEER RELIABLY.**

<img src="https://komarev.com/ghpvc/?username={USER}&style=flat-square&color=FF168A&label=PROFILE+VISITS"/>

<sub>VACHAN U S · NEON DISTRICT · AUTOMATED TELEMETRY REFRESH EVERY 6 HOURS</sub>

</div>
"""
    readme_path = ROOT / "README.md"
    readme_path.write_text(content, encoding="utf-8")
    print(f"[OK] Generated {readme_path}")

def main():
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    print(f"[*] Starting Cyberpunk Dossier Generation for user '{USER}' at {stamp} UTC...")

    # Fetch User & Repos
    try:
        user = github_api_get(f"/users/{USER}")
        repos = github_api_get(f"/users/{USER}/repos?per_page=100&sort=updated&type=owner")
    except Exception as exc:
        print(f"[FATAL] Unable to fetch user/repos from GitHub API: {exc}")
        print("[!] Preserving existing assets without overwriting corrupted data.")
        sys.exit(1)

    stars = sum(r.get("stargazers_count", 0) for r in repos)

    # Collect Language data
    languages = {}
    print(f"[*] Aggregating language telemetry across {len(repos)} repositories...")
    for r in repos:
        r_name = r.get("name")
        lang_url = r.get("languages_url")
        if not lang_url:
            continue
        try:
            repo_langs = github_api_get(lang_url)
            for l_name, b_count in repo_langs.items():
                languages[l_name] = languages.get(l_name, 0) + b_count
        except Exception as e:
            print(f"[WARN] Skipping language stats for {r_name}: {e}")

    # Fallback to primary repo languages if languages_url was empty
    if not languages:
        for r in repos:
            pl = r.get("language")
            if pl:
                languages[pl] = languages.get(pl, 0) + 1

    languages = dict(sorted(languages.items(), key=lambda item: item[1], reverse=True))

    print(f"[+] Total repositories: {len(repos)}, Total stars: {stars}, Languages detected: {len(languages)}")

    # Generate outputs
    generate_dossier_svg(user, repos, stars, languages, stamp)
    generate_telemetry_svg(user, repos, stars, languages, stamp)
    generate_readme(user, repos, stars, stamp)

    print("[SUCCESS] All Cyberpunk Dossier assets successfully generated.")

if __name__ == "__main__":
    main()
