#!/usr/bin/env python3
"""
VACHAN.EXE — Cyberpunk Engineering Command Center Generator
Target Canvas: 1536 x 1024
Strictly aligned with the visual reference design.
Generates:
  - assets/dossier.svg   (Full cinematic cyberpunk command center dashboard)
  - assets/telemetry.svg (Dedicated real-time telemetry HUD card)
  - README.md            (Cinematic markdown dossier with functional links)
"""

import json
import os
import sys
import html
import base64
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
THUMBS_DIR = ASSETS_DIR / "thumbnails"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
THUMBS_DIR.mkdir(parents=True, exist_ok=True)

# Standard typography stacks for SVG rendering across all client platforms
FONT_MONO = "ui-monospace, 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'SF Mono', Monaco, Consolas, monospace"
FONT_SANS = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

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

def fetch_real_contributions(username):
    """Fetch verified real contributions history from public GitHub contributions API."""
    url = f"https://github-contributions-api.jogruber.de/v4/{username}?y=last"
    headers = {"User-Agent": "Cyberpunk-Dossier-Generator/4.2"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except Exception as exc:
        print(f"[WARN] Could not fetch live contributions API ({exc}).")
        return None

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

def img_b64(path):
    """Return base64 data URI for an image on disk."""
    p = Path(path)
    if p.exists():
        mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode('utf-8')}"
    return ""

def panel_chamfer(x, y, w, h, notch=18):
    """Generate chamfered path matching the reference image containers."""
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

def panel_container(x, y, w, h, border="#FF168A", bg="#060A16", notch=18, glow=True):
    """Generate chamfered HUD panel box."""
    path_d = panel_chamfer(x, y, w, h, notch=notch)
    elements = []
    if glow:
        elements.append(f'<path d="{path_d}" fill="{bg}" stroke="{border}" stroke-width="1.8" opacity="0.95"/>')
    else:
        elements.append(f'<path d="{path_d}" fill="{bg}" stroke="{border}" stroke-width="1.2"/>')
    return "".join(elements)

# ==============================================================================
# MAIN COMMAND CENTER GENERATOR (1536 x 1024)
# ==============================================================================

def generate_dossier_svg(user, repos, stars, languages, contrib_info, stamp):
    """Generate master cinematic cyberpunk engineering command center (1536x1024)."""
    public_repos_cnt = user.get("public_repos", len(repos))
    followers_cnt = user.get("followers", 0)
    following_cnt = user.get("following", 0)
    total_contribs = contrib_info.get("total", 251)
    current_streak = contrib_info.get("current_streak", 3)
    calendar_days = contrib_info.get("days", [])

    # Load base64 image assets
    portrait_b64 = img_b64(ASSETS_DIR / "portrait.png")
    logo_b64 = img_b64(ASSETS_DIR / "logo_v.png")

    p_thumbs = [
        img_b64(THUMBS_DIR / "p1_rover.png"),
        img_b64(THUMBS_DIR / "p2_bank.png"),
        img_b64(THUMBS_DIR / "p3_book.png"),
        img_b64(THUMBS_DIR / "p4_radar.png"),
        img_b64(THUMBS_DIR / "p5_cards.png"),
        img_b64(THUMBS_DIR / "p6_resume.png")
    ]

    svg = []
    svg.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1536" height="1024" viewBox="0 0 1536 1024">')
    svg.append('''<defs>
<linearGradient id="canvas-bg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0%" stop-color="#04060E"/>
  <stop offset="50%" stop-color="#070C18"/>
  <stop offset="100%" stop-color="#03050A"/>
</linearGradient>
<linearGradient id="neon-cyan" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%" stop-color="#00E5FF"/>
  <stop offset="100%" stop-color="#0088FF"/>
</linearGradient>
<linearGradient id="neon-magenta" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%" stop-color="#FF168A"/>
  <stop offset="100%" stop-color="#8B35FF"/>
</linearGradient>
<linearGradient id="duo-border" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0%" stop-color="#FF168A"/>
  <stop offset="50%" stop-color="#8B35FF"/>
  <stop offset="100%" stop-color="#00E5FF"/>
</linearGradient>
<pattern id="grid-dots" width="24" height="24" patternUnits="userSpaceOnUse">
  <circle cx="12" cy="12" r="0.8" fill="#132338" opacity="0.6"/>
</pattern>
</defs>''')

    # Canvas Background
    svg.append('<rect width="1536" height="1024" fill="url(#canvas-bg)"/>')
    svg.append('<rect width="1536" height="1024" fill="url(#grid-dots)"/>')
    svg.append('<rect x="10" y="8" width="1516" height="1008" rx="14" fill="none" stroke="url(#duo-border)" stroke-width="1.8" opacity="0.85"/>')

    # Top-Right Header Decor: // DEVELOPER COMMAND CENTER //
    svg.append(f'<path d="M 1120 22 L 1134 36 M 1134 22 L 1148 36 M 1148 22 L 1162 36" stroke="#FF168A" stroke-width="2"/>')
    svg.append(f'<text x="1490" y="34" fill="#FF168A" font-size="13" font-family="{FONT_MONO}" font-weight="900" text-anchor="end" letter-spacing="1.5">// DEVELOPER COMMAND CENTER //</text>')

    # ==========================================================================
    # 1. TOP-LEFT: OPERATOR IDENTITY (x = 22, y = 18, w = 456, h = 338)
    # ==========================================================================
    p1_x, p1_y, p1_w, p1_h = 22, 18, 456, 338
    svg.append(panel_container(p1_x, p1_y, p1_w, p1_h, border="#FF168A", bg="#060A16", notch=18))

    # V-Emblem Logo
    if logo_b64:
        svg.append(f'<image href="{logo_b64}" x="{p1_x+20}" y="{p1_y+16}" width="46" height="36" preserveAspectRatio="none"/>')
    else:
        svg.append(f'<polygon points="{p1_x+24},{p1_y+18} {p1_x+64},{p1_y+18} {p1_x+44},{p1_y+50}" fill="#0A1628" stroke="#00E5FF" stroke-width="1.5"/>')
        svg.append(f'<text x="{p1_x+44}" y="{p1_y+36}" fill="#FF168A" font-size="14" font-weight="900" font-family="{FONT_MONO}" text-anchor="middle">V</text>')

    # VACHAN.EXE & ENGINEERING DIVISION
    svg.append(f'<text x="{p1_x+74}" y="{p1_y+32}" fill="#FFFFFF" font-size="22" font-weight="900" font-family="{FONT_SANS}" letter-spacing="1.2">VACHAN.EXE</text>')
    svg.append(f'<text x="{p1_x+74}" y="{p1_y+48}" fill="#00E5FF" font-size="11" font-weight="800" font-family="{FONT_MONO}" letter-spacing="1.8">ENGINEERING DIVISION</text>')

    # Large Name
    svg.append(f'<text x="{p1_x+20}" y="{p1_y+100}" fill="#FFFFFF" font-size="36" font-weight="900" font-family="{FONT_SANS}" letter-spacing="0.8">VACHAN U S</text>')

    # Pill: SOFTWARE ENGINEER // AI SYSTEMS // CLOUD
    pill_w = p1_w - 40
    svg.append(f'<rect x="{p1_x+20}" y="{p1_y+114}" width="{pill_w}" height="30" rx="5" fill="#0A1828" stroke="#00E5FF" stroke-width="1.2"/>')
    svg.append(f'<text x="{p1_x+20+pill_w//2}" y="{p1_y+134}" fill="#00E5FF" font-size="11.5" font-weight="800" font-family="{FONT_MONO}" text-anchor="middle" letter-spacing="1.2">SOFTWARE ENGINEER  //  AI SYSTEMS  //  CLOUD</text>')

    # Bio block
    svg.append(f'<text x="{p1_x+20}" y="{p1_y+168}" fill="#FF168A" font-size="14" font-weight="900" font-family="{FONT_MONO}">&gt;</text>')
    bio_text_lines = [
        "Building intelligent applications,",
        "engineering reliable systems, and",
        "exploring the next generation of software."
    ]
    for b_idx, b_line in enumerate(bio_text_lines):
        svg.append(f'<text x="{p1_x+36}" y="{p1_y+168 + b_idx*18}" fill="#FFFFFF" font-size="12.5" font-family="{FONT_SANS}">{esc(b_line)}</text>')

    # 3 Metadata Rows (ROLE, LOCATION, EDUCATION)
    meta_rows = [
        ("ROLE", "Software Engineer @ Synapx"),
        ("LOCATION", "Bangalore, India"),
        ("EDUCATION", "B.Tech CSE (2022 – 2026)")
    ]
    meta_icons = ["💼", "📍", "🎓"]
    for m_idx, (m_lbl, m_val) in enumerate(meta_rows):
        my = p1_y + 236 + m_idx * 28
        svg.append(f'<text x="{p1_x+20}" y="{my+12}" fill="#00E5FF" font-size="13">{meta_icons[m_idx]}</text>')
        svg.append(f'<text x="{p1_x+42}" y="{my+12}" fill="#00E5FF" font-size="11" font-weight="800" font-family="{FONT_MONO}">{m_lbl}</text>')
        svg.append(f'<text x="{p1_x+120}" y="{my+12}" fill="#00E5FF" font-size="11" font-weight="800" font-family="{FONT_MONO}">:</text>')
        svg.append(f'<text x="{p1_x+134}" y="{my+12}" fill="#FFFFFF" font-size="12" font-weight="700" font-family="{FONT_SANS}">{esc(m_val)}</text>')

    # ==========================================================================
    # 2. CENTER: CYBERPUNK CHARACTER PORTRAIT (x = 432, y = 18, w = 444, h = 339)
    # ==========================================================================
    if portrait_b64:
        svg.append(f'<image href="{portrait_b64}" x="432" y="18" width="444" height="339" preserveAspectRatio="none"/>')

    # ==========================================================================
    # 3. TOP-RIGHT: CORE SKILLS (x = 868, y = 68, w = 296, h = 288)
    # ==========================================================================
    p3_x, p3_y, p3_w, p3_h = 868, 68, 296, 288
    svg.append(panel_container(p3_x, p3_y, p3_w, p3_h, border="#FF168A", bg="#060A16", notch=16))

    # Header
    svg.append(f'<text x="{p3_x+20}" y="{p3_y+26}" fill="#00E5FF" font-size="14" font-weight="900" font-family="{FONT_MONO}" letter-spacing="1">🧠 CORE SKILLS</text>')

    # 6 Skill Rows with 4 Neon Magenta Slash Indicators (////)
    skills = [
        ("AI / ML", "🧠"),
        ("Backend", "🗄️"),
        ("Full-Stack", "{/}"),
        ("Cloud / DevOps", "☁️"),
        ("Cybersecurity", "🛡️"),
        ("System Design", "🕸️")
    ]
    for s_i, (s_name, s_icon) in enumerate(skills):
        sy = p3_y + 42 + s_i * 38
        # Icon
        svg.append(f'<text x="{p3_x+20}" y="{sy+18}" fill="#00E5FF" font-size="12">{s_icon}</text>')
        # Name
        svg.append(f'<text x="{p3_x+44}" y="{sy+18}" fill="#FFFFFF" font-size="12.5" font-weight="700" font-family="{FONT_SANS}">{s_name}</text>')
        # 4 Angled Neon Magenta Slashes (////)
        slash_start_x = p3_x + p3_w - 76
        for sl_i in range(4):
            slx = slash_start_x + sl_i * 13
            sly = sy + 8
            svg.append(f'<polygon points="{slx+6},{sly} {slx+12},{sly} {slx+6},{sly+14} {slx},{sly+14}" fill="#FF168A"/>')

    # ==========================================================================
    # 4. FAR-TOP-RIGHT: TECHNOLOGY LOADOUT (x = 1176, y = 68, w = 338, h = 288)
    # ==========================================================================
    p4_x, p4_y, p4_w, p4_h = 1176, 68, 338, 288
    svg.append(panel_container(p4_x, p4_y, p4_w, p4_h, border="#00E5FF", bg="#060A16", notch=16))

    # Header
    svg.append(f'<text x="{p4_x+20}" y="{p4_y+26}" fill="#00E5FF" font-size="14" font-weight="900" font-family="{FONT_MONO}" letter-spacing="1">💻 TECHNOLOGY LOADOUT</text>')

    # 3 Rows x 5 Columns = 15 Technology Tiles
    tiles = [
        # Row 1
        ("Python", "#3776AB", "#0A1728"),
        ("Java", "#ED8B00", "#1E1408"),
        ("JS", "#F7DF1E", "#222008"),
        ("TS", "#3178C6", "#0A182A"),
        ("HTML5", "#E34F26", "#200C06"),
        # Row 2
        ("dj", "#092E20", "#081E16"),
        ("React", "#61DAFB", "#081C26"),
        ("Node", "#339933", "#081E0C"),
        ("Tailwind", "#06B6D4", "#061A22"),
        ("Git", "#F05032", "#200B06"),
        # Row 3
        ("aws", "#FF9900", "#221606"),
        ("Docker", "#2496ED", "#08182A"),
        ("k8s", "#326CE5", "#08142A"),
        ("GitHub", "#FFFFFF", "#12141A"),
        ("VS Code", "#007ACC", "#061528")
    ]
    tile_w = 54
    tile_h = 46
    gap_x = 9
    gap_y = 9
    grid_start_x = p4_x + 18
    grid_start_y = p4_y + 44

    for t_i, (t_label, t_accent, t_bg) in enumerate(tiles):
        t_col = t_i % 5
        t_row = t_i // 5
        tx = grid_start_x + t_col * (tile_w + gap_x)
        ty = grid_start_y + t_row * (tile_h + gap_y)

        svg.append(f'<rect x="{tx}" y="{ty}" width="{tile_w}" height="{tile_h}" rx="6" fill="{t_bg}" stroke="{t_accent}" stroke-width="1.2"/>')
        svg.append(f'<text x="{tx+tile_w//2}" y="{ty+tile_h//2+5}" fill="{t_accent}" font-size="11" font-weight="800" font-family="{FONT_MONO}" text-anchor="middle">{t_label}</text>')

    # Bottom subtext pill for AI frameworks
    svg.append(f'<rect x="{p4_x+16}" y="{p4_y+222}" width="{p4_w-32}" height="28" rx="6" fill="#0A1828" stroke="#1D3852" stroke-width="1"/>')
    svg.append(f'<text x="{p4_x+p4_w//2}" y="{p4_y+240}" fill="#00E5FF" font-size="10.5" font-family="{FONT_MONO}" font-weight="800" text-anchor="middle">+ OpenAI · Claude · Gemini · LangChain · CrewAI</text>')

    # ==========================================================================
    # 5. MIDDLE-LEFT: MISSION TIMELINE (x = 22, y = 370, w = 328, h = 440)
    # ==========================================================================
    p5_x, p5_y, p5_w, p5_h = 22, 370, 328, 440
    svg.append(panel_container(p5_x, p5_y, p5_w, p5_h, border="#FF168A", bg="#060A16", notch=18))

    # Header
    svg.append(f'<text x="{p5_x+20}" y="{p5_y+28}" fill="#FF168A" font-size="14" font-weight="900" font-family="{FONT_MONO}" letter-spacing="1">🎯 MISSION TIMELINE</text>')

    # Vertical glowing bus line
    line_x = p5_x + 36
    svg.append(f'<line x1="{line_x}" y1="{p5_y+54}" x2="{line_x}" y2="{p5_y+p5_h-36}" stroke="#1E2B3E" stroke-width="2"/>')
    svg.append(f'<line x1="{line_x}" y1="{p5_y+54}" x2="{line_x}" y2="{p5_y+p5_h-36}" stroke="url(#neon-magenta)" stroke-width="1.4"/>')

    timeline_data = [
        ("2026 – Present", "Software Engineer @ Synapx", "Building and shipping software solutions.", "💼"),
        ("Feb – May 2026", "Dhee Coding Lab", "Python Full Stack with Generative AI.", "{/}"),
        ("Aug 2024 – Jan 2025", "Internship Studio", "Ethical Hacking Intern", "🛡️"),
        ("2022 – 2026", "B.Tech – CSE", "Dr. Ambedkar Institute of Technology.", "🎓")
    ]
    for t_idx, (period, role, desc, icon) in enumerate(timeline_data):
        ty = p5_y + 54 + t_idx * 90
        # Node circle
        svg.append(f'<circle cx="{line_x}" cy="{ty+8}" r="7" fill="#060A16" stroke="#FF168A" stroke-width="2"/>')
        svg.append(f'<circle cx="{line_x}" cy="{ty+8}" r="3" fill="#00E5FF"/>')
        # Content
        svg.append(f'<text x="{line_x+18}" y="{ty}" fill="#00E5FF" font-size="11.5" font-weight="800" font-family="{FONT_MONO}">{period}</text>')
        svg.append(f'<text x="{line_x+18}" y="{ty+18}" fill="#FFFFFF" font-size="13" font-weight="800" font-family="{FONT_SANS}">{role}</text>')
        svg.append(f'<text x="{line_x+18}" y="{ty+34}" fill="#8CA4B8" font-size="10.5" font-weight="600" font-family="{FONT_SANS}">{desc}</text>')

    # ==========================================================================
    # 6. CENTER-MIDDLE: FEATURED PROJECTS (x = 362, y = 370, w = 768, h = 440)
    # ==========================================================================
    p6_x, p6_y, p6_w, p6_h = 362, 370, 768, 440
    svg.append(panel_container(p6_x, p6_y, p6_w, p6_h, border="#FF168A", bg="#060A16", notch=18))

    # Header
    svg.append(f'<text x="{p6_x+20}" y="{p6_y+28}" fill="#FF168A" font-size="14" font-weight="900" font-family="{FONT_MONO}" letter-spacing="1">🚀 FEATURED PROJECTS</text>')

    projects_meta = [
        ("AI PESTICIDE SPRAYING ROBOT", "Autonomous robot for plant disease detection and precision spraying.", ["Python", "YOLOv8", "OpenCV"], "https://github.com/vachan18/AI-POWERED-PESTICIDE-SPRAYING-ROBOT-WITH-DISEASE-DETECTION"),
        ("GENAI BANKING AGENT", "Conversational AI assistant for intelligent banking interactions.", ["Python", "LLMs", "APIs"], "https://github.com/vachan18/Gen-AI-banking-agent"),
        ("STUDYMIND", "AI-powered learning platform for personalized study assistance.", ["Python", "GenAI", "JS"], "https://github.com/vachan18/StudyMind"),
        ("HIRELENS AI", "Multi-agent job rejection analyzer with actionable insights.", ["Python", "Streamlit", "CrewAI"], "https://github.com/vachan18/HirelensAi"),
        ("LUMIQ", "Convert study materials into summaries, flashcards and mind maps.", ["AI", "Python", "JS"], "https://github.com/vachan18/Lumiq---Smart-Learning-Platforms"),
        ("AI RESUME ANALYZER", "Automated resume analysis and workflow automation.", ["n8n", "LLMs", "Automation"], "https://github.com/vachan18/ai-resume-analyzer-n8n")
    ]

    card_w = 236
    card_h = 186
    gap_x = 12
    gap_y = 12

    for p_idx, (p_title, p_desc, p_tags, p_url) in enumerate(projects_meta):
        col_i = p_idx % 3
        row_i = p_idx // 3
        cx = p6_x + 18 + col_i * (card_w + gap_x)
        cy = p6_y + 42 + row_i * (card_h + gap_y)

        svg.append(f'<a href="{esc(p_url)}" target="_blank">')
        # Card container
        svg.append(f'<rect x="{cx}" y="{cy}" width="{card_w}" height="{card_h}" rx="8" fill="#070E1B" stroke="#182E45" stroke-width="1.2"/>')

        # Thumbnail Image (from reference image crop)
        thumb_img = p_thumbs[p_idx] if p_idx < len(p_thumbs) else ""
        if thumb_img:
            svg.append(f'<image href="{thumb_img}" x="{cx+6}" y="{cy+6}" width="{card_w-12}" height="82" preserveAspectRatio="none"/>')
        else:
            svg.append(f'<rect x="{cx+6}" y="{cy+6}" width="{card_w-12}" height="82" rx="4" fill="#0C1A30"/>')

        # Badge P1-P6 in top right of thumbnail
        svg.append(f'<rect x="{cx+card_w-38}" y="{cy+10}" width="28" height="18" rx="4" fill="#FF168A"/>')
        svg.append(f'<text x="{cx+card_w-24}" y="{cy+23}" fill="#FFFFFF" font-size="10.5" font-weight="900" font-family="{FONT_MONO}" text-anchor="middle">P{p_idx+1}</text>')

        # Project Title (crisp & readable)
        title_lines = wrap_text(p_title, 22)
        for t_li, t_line in enumerate(title_lines[:2]):
            svg.append(f'<text x="{cx+8}" y="{cy+104 + t_li*14}" fill="#FFFFFF" font-size="12.5" font-weight="800" font-family="{FONT_SANS}">{esc(t_line)}</text>')

        # Project Description
        desc_lines = wrap_text(p_desc, 28)
        desc_start_y = cy + 128 if len(title_lines) == 1 else cy + 134
        for d_li, d_line in enumerate(desc_lines[:2]):
            svg.append(f'<text x="{cx+8}" y="{desc_start_y + d_li*12}" fill="#8EA6BD" font-size="10" font-family="{FONT_SANS}">{esc(d_line)}</text>')

        # Tech Tags (cyan border pills)
        tag_start_x = cx + 8
        for tg_i, tg in enumerate(p_tags[:3]):
            tg_w = len(tg) * 7 + 12
            svg.append(f'<rect x="{tag_start_x}" y="{cy+card_h-24}" width="{tg_w}" height="16" rx="4" fill="#071524" stroke="#00E5FF" stroke-width="0.8"/>')
            svg.append(f'<text x="{tag_start_x+tg_w//2}" y="{cy+card_h-12}" fill="#00E5FF" font-size="9.5" font-weight="700" font-family="{FONT_MONO}" text-anchor="middle">{esc(tg)}</text>')
            tag_start_x += tg_w + 6

        svg.append('</a>')

    # ==========================================================================
    # 7. RIGHT-MIDDLE: GITHUB TELEMETRY (x = 1144, y = 370, w = 370, h = 440)
    # ==========================================================================
    p7_x, p7_y, p7_w, p7_h = 1144, 370, 370, 440
    svg.append(panel_container(p7_x, p7_y, p7_w, p7_h, border="#FF168A", bg="#060A16", notch=18))

    # Header
    svg.append(f'<text x="{p7_x+20}" y="{p7_y+28}" fill="#FF168A" font-size="14" font-weight="900" font-family="{FONT_MONO}" letter-spacing="1">🐱 GITHUB TELEMETRY</text>')

    # 4 Stat Tiles in a row
    stat_items = [
        ("&lt;/&gt;", "REPOS", public_repos_cnt),
        ("★", "STARS", stars),
        ("👥", "FOLLOWERS", followers_cnt),
        ("🔀", "FOLLOWING", following_cnt)
    ]
    tile_box_w = 76
    tile_box_h = 62
    for s_idx, (s_ic, s_lbl, s_val) in enumerate(stat_items):
        stx = p7_x + 18 + s_idx * (tile_box_w + 10)
        sty = p7_y + 44
        svg.append(f'<rect x="{stx}" y="{sty}" width="{tile_box_w}" height="{tile_box_h}" rx="6" fill="#091526" stroke="#00E5FF" stroke-width="1.2"/>')
        svg.append(f'<text x="{stx+tile_box_w//2}" y="{sty+20}" fill="#00E5FF" font-size="15" font-weight="800" font-family="{FONT_MONO}" text-anchor="middle">{s_ic}</text>')
        svg.append(f'<text x="{stx+tile_box_w//2}" y="{sty+38}" fill="#FFFFFF" font-size="16" font-weight="900" font-family="{FONT_MONO}" text-anchor="middle">{s_val}</text>')
        svg.append(f'<text x="{stx+tile_box_w//2}" y="{sty+53}" fill="#7A96AD" font-size="9.5" font-weight="800" font-family="{FONT_MONO}" text-anchor="middle">{s_lbl}</text>')

    # Language Distribution Sub-panel
    svg.append(f'<text x="{p7_x+20}" y="{p7_y+134}" fill="#FF168A" font-size="12" font-weight="900" font-family="{FONT_MONO}" letter-spacing="1">LANGUAGE DISTRIBUTION</text>')

    # Progress bars for top languages
    total_bytes = sum(languages.values()) if languages else 1
    top_langs = list(languages.items())[:5] if languages else [("Python", 55), ("JavaScript", 25), ("HTML", 12), ("CSS", 5), ("Other", 3)]
    bar_colors = ["url(#neon-magenta)", "#00E5FF", "#8B35FF", "#FF168A", "#00E5FF"]

    for l_idx, (lang, b_cnt) in enumerate(top_langs):
        ly = p7_y + 154 + l_idx * 34
        pct = (b_cnt / total_bytes) * 100 if total_bytes > 0 else 0
        bar_len = max(int(140 * (pct / 100)), 8)
        svg.append(f'<text x="{p7_x+20}" y="{ly+11}" fill="#FFFFFF" font-size="11.5" font-weight="700" font-family="{FONT_SANS}">{esc(lang)}</text>')
        # Bar track
        svg.append(f'<rect x="{p7_x+104}" y="{ly}" width="140" height="14" rx="5" fill="#0E1B2C"/>')
        # Fill bar
        svg.append(f'<rect x="{p7_x+104}" y="{ly}" width="{bar_len}" height="14" rx="5" fill="{bar_colors[l_idx % len(bar_colors)]}"/>')

    # Donut Chart with GitHub Octocat in center (Right of language bars)
    donut_cx = p7_x + 300
    donut_cy = p7_y + 224
    # Outer glowing donut ring
    svg.append(f'<circle cx="{donut_cx}" cy="{donut_cy}" r="46" fill="none" stroke="#FF168A" stroke-width="14" stroke-dasharray="140 290"/>')
    svg.append(f'<circle cx="{donut_cx}" cy="{donut_cy}" r="46" fill="none" stroke="#00E5FF" stroke-width="14" stroke-dasharray="80 290" stroke-dashoffset="-140"/>')
    svg.append(f'<circle cx="{donut_cx}" cy="{donut_cy}" r="46" fill="none" stroke="#8B35FF" stroke-width="14" stroke-dasharray="60 290" stroke-dashoffset="-220"/>')
    # Inner center hole
    svg.append(f'<circle cx="{donut_cx}" cy="{donut_cy}" r="34" fill="#060A16"/>')
    # Center Octocat icon
    svg.append(f'<text x="{donut_cx}" y="{donut_cy+7}" fill="#FFFFFF" font-size="22" text-anchor="middle">🐱</text>')

    # Active Streak badge below donut
    svg.append(f'<rect x="{p7_x+246}" y="{p7_y+304}" width="110" height="24" rx="4" fill="#09182A" stroke="#00FF9D" stroke-width="1"/>')
    svg.append(f'<text x="{p7_x+301}" y="{p7_y+320}" fill="#00FF9D" font-size="10.5" font-weight="900" font-family="{FONT_MONO}" text-anchor="middle">STREAK: {current_streak} DAYS</text>')

    # ==========================================================================
    # 8. BOTTOM-LEFT: ENGINEERING PHILOSOPHY (x = 22, y = 826, w = 328, h = 176)
    # ==========================================================================
    p8_x, p8_y, p8_w, p8_h = 22, 826, 328, 176
    svg.append(panel_container(p8_x, p8_y, p8_w, p8_h, border="#FF168A", bg="#060A16", notch=18))

    # Quotation marks
    svg.append(f'<text x="{p8_x+18}" y="{p8_y+42}" fill="#FF168A" font-size="36" font-family="{FONT_MONO}" font-weight="900">“</text>')
    svg.append(f'<text x="{p8_x+p8_w-34}" y="{p8_y+p8_h-16}" fill="#FF168A" font-size="36" font-family="{FONT_MONO}" font-weight="900">”</text>')

    # 3 Italic bold lines
    svg.append(f'<text x="{p8_x+42}" y="{p8_y+64}" fill="#FFFFFF" font-size="15.5" font-weight="900" font-family="{FONT_SANS}" font-style="italic" letter-spacing="1">THINK DIFFERENTLY.</text>')
    svg.append(f'<text x="{p8_x+42}" y="{p8_y+96}" fill="#FFFFFF" font-size="15.5" font-weight="900" font-family="{FONT_SANS}" font-style="italic" letter-spacing="1">BUILD INTELLIGENTLY.</text>')
    svg.append(f'<text x="{p8_x+42}" y="{p8_y+128}" fill="#FFFFFF" font-size="15.5" font-weight="900" font-family="{FONT_SANS}" font-style="italic" letter-spacing="1">ENGINEER RELIABLY.</text>')

    # ==========================================================================
    # 9. BOTTOM-CENTER: CONTRIBUTION MATRIX (x = 362, y = 826, w = 768, h = 176)
    # ==========================================================================
    p9_x, p9_y, p9_w, p9_h = 362, 826, 768, 176
    svg.append(panel_container(p9_x, p9_y, p9_w, p9_h, border="#00E5FF", bg="#060A16", notch=18))

    # Header
    svg.append(f'<text x="{p9_x+20}" y="{p9_y+26}" fill="#00E5FF" font-size="14" font-weight="900" font-family="{FONT_MONO}" letter-spacing="1">▦ CONTRIBUTION MATRIX</text>')

    # Contribution Heatmap Grid
    grid_start_x = p9_x + 24
    grid_start_y = p9_y + 44
    cell_w = 11.2
    cell_gap = 2.4

    level_colors = {
        0: "#0D1726",
        1: "#43144A",
        2: "#7B2CBF",
        3: "#FF168A",
        4: "#00E5FF"
    }

    if calendar_days and len(calendar_days) >= 350:
        last_days = calendar_days[-364:]
        for day_idx, d in enumerate(last_days):
            col_i = day_idx // 7
            row_i = day_idx % 7
            cx = grid_start_x + col_i * (cell_w + cell_gap)
            cy = grid_start_y + row_i * (cell_w + cell_gap)
            lvl = d.get("level", 0)
            fill_col = level_colors.get(lvl, "#0D1726")
            svg.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell_w}" height="{cell_w}" rx="2" fill="{fill_col}"/>')
    else:
        for col_i in range(52):
            for row_i in range(7):
                cx = grid_start_x + col_i * (cell_w + cell_gap)
                cy = grid_start_y + row_i * (cell_w + cell_gap)
                lvl = (col_i + row_i) % 5 if (col_i * 7 + row_i) % 4 == 0 else 0
                fill_col = level_colors.get(lvl, "#0D1726")
                svg.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell_w}" height="{cell_w}" rx="2" fill="{fill_col}"/>')

    # Footer metrics bar inside Heatmap panel
    foot_y = p9_y + p9_h - 18
    svg.append(f'<text x="{p9_x+24}" y="{foot_y}" fill="#00E5FF" font-size="11" font-family="{FONT_MONO}" font-weight="800">TOTAL COMMITS (1Y): {total_contribs}</text>')
    svg.append(f'<text x="{p9_x+240}" y="{foot_y}" fill="#FF168A" font-size="11" font-family="{FONT_MONO}" font-weight="800">CURRENT STREAK: {current_streak} DAYS</text>')
    svg.append(f'<text x="{p9_x+470}" y="{foot_y}" fill="#00FF9D" font-size="11" font-family="{FONT_MONO}" font-weight="800">LIVE SYNC: {esc(stamp)} UTC</text>')

    # ==========================================================================
    # 10. BOTTOM-RIGHT: ESTABLISH CONNECTION (x = 1144, y = 826, w = 370, h = 176)
    # ==========================================================================
    p10_x, p10_y, p10_w, p10_h = 1144, 826, 370, 176
    svg.append(panel_container(p10_x, p10_y, p10_w, p10_h, border="#00E5FF", bg="#060A16", notch=18))

    # Header
    svg.append(f'<text x="{p10_x+20}" y="{p10_y+26}" fill="#00E5FF" font-size="14" font-weight="900" font-family="{FONT_MONO}" letter-spacing="1">🔗 ESTABLISH CONNECTION</text>')

    # 5 Colored Icon Square Buttons
    social_buttons = [
        ("GitHub", "🐱", "#10141D", "#FFFFFF", f"https://github.com/{USER}"),
        ("LinkedIn", "in", "#0077B5", "#FFFFFF", DATA.get("linkedin", "https://linkedin.com")),
        ("Devfolio", "D", "#3770FF", "#FFFFFF", DATA.get("devfolio", "https://devfolio.co")),
        ("Portfolio", "🔗", "#0E1C30", "#00E5FF", DATA.get("portfolio", "https://vachanmyportfolio.netlify.app")),
        ("Email", "✉️", "#8B35FF", "#FFFFFF", f"mailto:{DATA.get('email', 'vachan.us@gmail.com')}")
    ]
    btn_w = 56
    btn_h = 56
    btn_gap = 14
    btn_start_x = p10_x + 16
    btn_start_y = p10_y + 48

    for b_idx, (b_name, b_sym, b_bg, b_fg, b_url) in enumerate(social_buttons):
        bx = btn_start_x + b_idx * (btn_w + btn_gap)
        by = btn_start_y
        svg.append(f'<a href="{esc(b_url)}" target="_blank">')
        svg.append(f'<rect x="{bx}" y="{by}" width="{btn_w}" height="{btn_h}" rx="8" fill="{b_bg}" stroke="{b_fg}" stroke-width="1.2"/>')
        svg.append(f'<text x="{bx+btn_w//2}" y="{by+btn_h//2+6}" fill="{b_fg}" font-size="20" font-weight="900" font-family="{FONT_MONO}" text-anchor="middle">{b_sym}</text>')
        svg.append(f'<text x="{bx+btn_w//2}" y="{by+btn_h+20}" fill="#8EA4B8" font-size="10" font-family="{FONT_MONO}" font-weight="700" text-anchor="middle">{b_name}</text>')
        svg.append('</a>')

    # Close SVG
    svg.append('</svg>')
    out_svg = "\n".join(svg)

    # Validate XML strictly
    ET.fromstring(out_svg)

    # Write output
    dossier_path = ASSETS_DIR / "dossier.svg"
    dossier_path.write_text(out_svg, encoding="utf-8")
    print(f"[OK] Master Command Center generated at {dossier_path} ({len(out_svg)} bytes, 1536x1024)")

def generate_telemetry_svg(user, repos, stars, languages, contrib_info, stamp):
    """Generate dedicated assets/telemetry.svg (800x420 standalone HUD)."""
    public_repos_cnt = user.get("public_repos", len(repos))
    followers_cnt = user.get("followers", 0)
    following_cnt = user.get("following", 0)
    total_contribs = contrib_info.get("total", 251)
    current_streak = contrib_info.get("current_streak", 3)
    total_bytes = sum(languages.values()) if languages else 0
    top_langs = list(languages.items())[:5] if languages else []

    svg = []
    svg.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="420" viewBox="0 0 800 420">')
    svg.append('''<defs>
<linearGradient id="t-bg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0%" stop-color="#050814"/>
  <stop offset="100%" stop-color="#0A1224"/>
</linearGradient>
<linearGradient id="t-cyan" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%" stop-color="#00E5FF"/>
  <stop offset="100%" stop-color="#0088FF"/>
</linearGradient>
<linearGradient id="t-magenta" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%" stop-color="#FF168A"/>
  <stop offset="100%" stop-color="#8B35FF"/>
</linearGradient>
</defs>''')
    svg.append('<rect width="800" height="420" fill="url(#t-bg)" rx="12" stroke="#00E5FF" stroke-width="1.8"/>')
    svg.append(f'<text x="24" y="32" fill="#00E5FF" font-size="13" font-weight="800" font-family="{FONT_MONO}" letter-spacing="1.5">TELEMETRY // GITHUB LIVE METRICS HUD</text>')
    svg.append(f'<text x="776" y="32" fill="#FF168A" font-size="11" font-weight="700" font-family="{FONT_MONO}" text-anchor="end">SYNC: {esc(stamp)} UTC</text>')
    svg.append('<path d="M 24 44 H 776" stroke="#1E364C" stroke-width="1"/>')

    # 4 HUD Stat blocks
    stats = [
        ("PUBLIC REPOS", public_repos_cnt, "#00E5FF"),
        ("TOTAL STARS", stars, "#FF168A"),
        ("CONTRIBUTIONS", total_contribs, "#00FF9D"),
        ("ACTIVE STREAK", f"{current_streak}D", "#FF168A")
    ]
    box_w = 176
    gap = 16
    for idx, (label, val, col) in enumerate(stats):
        bx = 24 + idx * (box_w + gap)
        by = 60
        svg.append(f'<rect x="{bx}" y="{by}" width="{box_w}" height="74" rx="6" fill="#091222" stroke="#1C354E" stroke-width="1"/>')
        svg.append(f'<text x="{bx+14}" y="{by+22}" fill="#7898B0" font-size="10" font-weight="700" font-family="{FONT_MONO}">{label}</text>')
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
            svg.append(f'<text x="190" y="{ly+14}" fill="#00E5FF" font-size="11" font-weight="700" font-family="{FONT_MONO}" text-anchor="end">{pct:.1f}%</text>')
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

def generate_readme(user, repos, stars, contrib_info, stamp):
    """Generate concise, cyberpunk engineering README.md."""
    proj_rows = []
    for idx, p in enumerate(DATA.get("projects", [])):
        name = esc(p.get("name", ""))
        cat = esc(p.get("category", ""))
        url = esc(p.get("url", ""))
        repo_slug = url.replace("https://github.com/", "")
        stack_str = " · ".join(f"`{esc(s)}`" for s in p.get("stack", [])[:3])
        proj_rows.append(
            f"| **P{idx+1}** | **{name}**<br/><sub>{cat}</sub> | {stack_str} | [`{repo_slug} ↗`]({url}) |"
        )

    exp_md = []
    for e in DATA.get("experience", []):
        period = esc(e.get("period", ""))
        title = esc(e.get("title", ""))
        org = esc(e.get("organization", ""))
        detail = esc(e.get("detail", ""))
        exp_md.append(f"- **{title}** · {org} _({period})_{' — ' + detail if detail else ''}")

    additional_md = "\n".join(f"- {esc(item)}" for item in DATA.get("additional", []))

    content = f"""<div align="center">

<!-- VACHAN.EXE — CYBERPUNK ENGINEERING COMMAND CENTER -->
<img src="./assets/dossier.svg" width="100%" alt="VACHAN.EXE — Cyberpunk Engineering Command Center"/>

<br/>

<!-- SECURE CONNECTION CHANNELS -->
<a href="https://github.com/{USER}"><strong>GITHUB</strong></a> ·
<a href="{DATA.get('linkedin', '')}"><strong>LINKEDIN</strong></a> ·
<a href="{DATA.get('portfolio', '')}"><strong>PORTFOLIO</strong></a> ·
<a href="{DATA.get('devfolio', '')}"><strong>DEVFOLIO</strong></a> ·
<a href="mailto:{DATA.get('email', '')}"><strong>EMAIL</strong></a>

</div>

## 🛰️ OPERATOR BRIEFING

**{DATA.get('name', 'Vachan U S')} — {DATA.get('role', 'Software Engineer')} @ {DATA.get('company', 'Synapx')}**

{DATA.get('bio', '')}

- 📍 **Location:** {DATA.get('location', 'Bangalore, India')} [12.9716° N, 77.5946° E]
- 🎓 **Education:** {DATA.get('education', '')}
- ⚡ **Focus Areas:** Generative AI &amp; Multi-Agent Systems · Cloud &amp; Distributed Backend Engineering · Security &amp; Automation Pipelines

---

## 📂 REPOSITORY LINKS

Direct access to the six intelligence builds featured in the Cyberpunk Command Center:

| ID | SYSTEM BUILD | CORE STACK | REPOSITORY SOURCE |
|:---:|:---|:---|:---|
{chr(10).join(proj_rows)}

---

## 🎖️ CAREER &amp; CREDENTIALS

{chr(10).join(exp_md)}

**Credentials &amp; Leadership:**
{additional_md}

---

## ⚡ CONTRIBUTION ACTIVITY

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/{USER}/{USER}/output/github-contribution-grid-snake-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/{USER}/{USER}/output/github-contribution-grid-snake.svg">
  <img alt="GitHub Contribution Snake" src="https://raw.githubusercontent.com/{USER}/{USER}/output/github-contribution-grid-snake-dark.svg" width="100%"/>
</picture>

<br/>

**THINK DIFFERENTLY. BUILD INTELLIGENTLY. ENGINEER RELIABLY.**

<img src="https://komarev.com/ghpvc/?username={USER}&style=flat-square&color=FF168A&label=PROFILE+VISITS"/>

<sub>VACHAN.EXE // CYBERPUNK COMMAND CENTER · AUTOMATED TELEMETRY REFRESH EVERY 6 HOURS</sub>

</div>
"""
    readme_path = ROOT / "README.md"
    readme_path.write_text(content, encoding="utf-8")
    print(f"[OK] Generated {readme_path}")

def main():
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    print(f"[*] Initializing Cyberpunk Command Center Redesign for '{USER}' at {stamp} UTC...")

    # Fetch User & Repos
    try:
        user = github_api_get(f"/users/{USER}")
        repos = github_api_get(f"/users/{USER}/repos?per_page=100&sort=updated&type=owner")
    except Exception as exc:
        print(f"[FATAL] Unable to fetch user/repos from GitHub API: {exc}")
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

    # Fetch Real Contributions
    print("[*] Fetching verified GitHub contribution calendar & streak telemetry...")
    contrib_data = fetch_real_contributions(USER)
    contrib_info = {
        "total": 251,
        "current_streak": 3,
        "longest_streak": 3,
        "days": []
    }

    if contrib_data:
        days = contrib_data.get("contributions", [])
        if days:
            contrib_info["days"] = days
            contrib_info["total"] = sum(d.get("count", 0) for d in days)

            c_streak = 0
            for d in reversed(days):
                if d.get("count", 0) > 0:
                    c_streak += 1
                else:
                    if c_streak == 0:
                        continue
                    break
            contrib_info["current_streak"] = c_streak

            l_streak = 0
            curr = 0
            for d in days:
                if d.get("count", 0) > 0:
                    curr += 1
                    if curr > l_streak:
                        l_streak = curr
                else:
                    curr = 0
            contrib_info["longest_streak"] = l_streak

    print(f"[+] User: {USER}, Repos: {len(repos)}, Stars: {stars}, Contributions: {contrib_info['total']}, Streak: {contrib_info['current_streak']}D")

    # Generate master outputs
    generate_dossier_svg(user, repos, stars, languages, contrib_info, stamp)
    generate_telemetry_svg(user, repos, stars, languages, contrib_info, stamp)
    generate_readme(user, repos, stars, contrib_info, stamp)

    print("[SUCCESS] VACHAN.EXE Cyberpunk Command Center fully generated and validated.")

if __name__ == "__main__":
    main()
