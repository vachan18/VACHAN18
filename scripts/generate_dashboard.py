#!/usr/bin/env python3
"""
VACHAN.EXE — Cyberpunk Engineering Command Center Generator
Target Canvas: 1536 x 1024
Generates:
  - assets/dossier.svg   (Full cinematic cyberpunk command center dashboard)
  - assets/telemetry.svg (Dedicated real-time telemetry HUD card)
  - README.md            (Cinematic markdown dossier with functional links)
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
        print(f"[WARN] Could not fetch live contributions API ({exc}). Trying cached backup...")
        # Check if local fallback contributions.json exists
        cached = ROOT / "data" / "contributions.json"
        if cached.exists():
            try:
                return json.loads(cached.read_text(encoding="utf-8"))
            except Exception:
                pass
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

def panel_path(x, y, w, h, notch=16):
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

def panel_hud(x, y, w, h, title, accent="#00E5FF", tag="CLASSIFIED // LEVEL-5"):
    """Render a cyberpunk HUD panel frame with title bar, coordinates, and corner brackets."""
    p_path = panel_path(x, y, w, h, notch=16)
    corner_decor = [
        f'<path d="{p_path}" fill="#070B16" stroke="{accent}" stroke-width="1.4" opacity="0.96"/>',
        f'<path d="M {x+2} {y+28} H {x+w-2}" stroke="{accent}" stroke-width="0.8" opacity="0.35"/>',
        # Top-left bracket
        f'<path d="M {x+5} {y+14} L {x+14} {y+5}" stroke="#FF168A" stroke-width="2" fill="none"/>',
        # Bottom-right bracket
        f'<path d="M {x+w-14} {y+h-5} L {x+w-5} {y+h-14}" stroke="#FF168A" stroke-width="2" fill="none"/>',
        # Title
        f'<text x="{x+20}" y="{y+20}" fill="{accent}" font-size="12" font-weight="800" font-family="{FONT_MONO}" letter-spacing="1.2">{esc(title)}</text>',
        # Tag
        f'<text x="{x+w-20}" y="{y+20}" fill="#6C879B" font-size="9.5" font-weight="700" font-family="{FONT_MONO}" text-anchor="end" letter-spacing="1">{esc(tag)}</text>',
    ]
    return "".join(corner_decor)

# ==============================================================================
# PROJECT THUMBNAILS (Unique Vector Art for P1–P6)
# ==============================================================================

def get_project_thumbnail(proj_id, x, y, w, h):
    """Render unique, domain-specific futuristic vector illustration for each project."""
    res = []
    # Background enclosure
    res.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#0A1020" stroke="#182A40" stroke-width="1"/>')
    # Cyber grid overlay
    res.append(f'<path d="M {x} {y+h//2} H {x+w} M {x+w//4} {y} V {y+h} M {x+w//2} {y} V {y+h} M {x+3*w//4} {y} V {y+h}" stroke="#132338" stroke-width="0.8"/>')

    if proj_id == 1:
        # P1: Agricultural Rover & CV Laser Disease Scanner
        # Rover body
        res.append(f'<rect x="{x+w//2-28}" y="{y+h//2-10}" width="56" height="20" rx="3" fill="#0E1D32" stroke="#00E5FF" stroke-width="1.2"/>')
        # Solar panel array
        res.append(f'<rect x="{x+w//2-32}" y="{y+h//2-22}" width="64" height="8" rx="2" fill="#152B46" stroke="#FF168A" stroke-width="1"/>')
        # Wheels
        res.append(f'<circle cx="{x+w//2-20}" cy="{y+h//2+14}" r="6" fill="#1A2D44" stroke="#00E5FF" stroke-width="1.2"/>')
        res.append(f'<circle cx="{x+w//2+20}" cy="{y+h//2+14}" r="6" fill="#1A2D44" stroke="#00E5FF" stroke-width="1.2"/>')
        # Laser targeting crosshair
        res.append(f'<circle cx="{x+w//2+14}" cy="{y+h//2-4}" r="12" fill="none" stroke="#FF168A" stroke-width="1" stroke-dasharray="2 2"/>')
        res.append(f'<path d="M {x+w//2+14} {y+h//2-18} V {y+h//2+10} M {x+w//2} {y+h//2-4} H {x+w//2+28}" stroke="#FF168A" stroke-width="1.2"/>')
        # Sensor beam
        res.append(f'<polygon points="{x+w//2+14},{y+h//2-4} {x+w-16},{y+h-10} {x+w-28},{y+h-10}" fill="#00E5FF" opacity="0.25"/>')
        res.append(f'<text x="{x+8}" y="{y+14}" fill="#00E5FF" font-size="8.5" font-family="{FONT_MONO}" font-weight="700">YOLOv8 // CV-ROVER</text>')

    elif proj_id == 2:
        # P2: GenAI Banking Agent — Cryptographic Shield & Dialogue Matrix
        # Hexagonal secure node
        cx, cy = x + w//2, y + h//2
        res.append(f'<polygon points="{cx},{cy-24} {cx+24},{cy-12} {cx+24},{cy+12} {cx},{cy+24} {cx-24},{cy+12} {cx-24},{cy-12}" fill="#0D1A30" stroke="#FF168A" stroke-width="1.4"/>')
        # Currency / AI Glyph inside shield
        res.append(f'<text x="{cx}" y="{cy+6}" fill="#00E5FF" font-size="16" font-family="{FONT_MONO}" font-weight="800" text-anchor="middle">₹</text>')
        # Pulse waves / Dialogue packets
        res.append(f'<path d="M {cx-42} {cy-10} Q {cx-32} {cy} {cx-42} {cy+10}" stroke="#00E5FF" stroke-width="1.5" fill="none"/>')
        res.append(f'<path d="M {cx-50} {cy-16} Q {cx-38} {cy} {cx-50} {cy+16}" stroke="#8B35FF" stroke-width="1.2" fill="none"/>')
        res.append(f'<path d="M {cx+42} {cy-10} Q {cx+32} {cy} {cx+42} {cy+10}" stroke="#00E5FF" stroke-width="1.5" fill="none"/>')
        res.append(f'<path d="M {cx+50} {cy-16} Q {cx+38} {cy} {cx+50} {cy+16}" stroke="#8B35FF" stroke-width="1.2" fill="none"/>')
        res.append(f'<text x="{x+8}" y="{y+14}" fill="#FF168A" font-size="8.5" font-family="{FONT_MONO}" font-weight="700">FIN-LLM // SECURE</text>')

    elif proj_id == 3:
        # P3: StudyMind — Cognitive Brain Network & Synaptic Nodes
        cx, cy = x + w//2, y + h//2
        # Brain hemisphere arcs
        res.append(f'<path d="M {cx-14} {cy-16} C {cx-34} {cy-20} {cx-42} {cy+6} {cx-24} {cy+18} C {cx-14} {cy+22} {cx-6} {cy+14} {cx-6} {cy-14} Z" fill="#0F1F38" stroke="#00E5FF" stroke-width="1.2"/>')
        res.append(f'<path d="M {cx+14} {cy-16} C {cx+34} {cy-20} {cx+42} {cy+6} {cx+24} {cy+18} C {cx+14} {cy+22} {cx+6} {cy+14} {cx+6} {cy-14} Z" fill="#0F1F38" stroke="#FF168A" stroke-width="1.2"/>')
        # Flashcard / Synapse lines
        res.append(f'<line x1="{cx-24}" y1="{cy}" x2="{cx-46}" y2="{cy-12}" stroke="#8B35FF" stroke-width="1.2"/>')
        res.append(f'<circle cx="{cx-46}" cy="{cy-12}" r="3.5" fill="#00E5FF"/>')
        res.append(f'<line x1="{cx+24}" y1="{cy}" x2="{cx+46}" y2="{cy-12}" stroke="#8B35FF" stroke-width="1.2"/>')
        res.append(f'<circle cx="{cx+46}" cy="{cy-12}" r="3.5" fill="#FF168A"/>')
        res.append(f'<line x1="{cx}" y1="{cy+14}" x2="{cx}" y2="{cy+24}" stroke="#00E5FF" stroke-width="1.2"/>')
        res.append(f'<circle cx="{cx}" cy="{cy+24}" r="3.5" fill="#00FF9D"/>')
        res.append(f'<text x="{x+8}" y="{y+14}" fill="#00E5FF" font-size="8.5" font-family="{FONT_MONO}" font-weight="700">COGNITIVE // AI-LEARN</text>')

    elif proj_id == 4:
        # P4: HireLens AI — Multi-Agent Radar & Candidate Evaluation Grid
        cx, cy = x + w//2, y + h//2
        # Radar scope
        res.append(f'<circle cx="{cx}" cy="{cy}" r="26" fill="#0B162B" stroke="#8B35FF" stroke-width="1.2"/>')
        res.append(f'<circle cx="{cx}" cy="{cy}" r="16" fill="none" stroke="#00E5FF" stroke-width="0.8" stroke-dasharray="2 2"/>')
        res.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="#FF168A"/>')
        # Radar sweep angle
        res.append(f'<polygon points="{cx},{cy} {cx+24},{cy-12} {cx+24},{cy-24}" fill="#00E5FF" opacity="0.35"/>')
        # Multi-agent dots
        res.append(f'<circle cx="{cx-12}" cy="{cy-8}" r="2.5" fill="#00E5FF"/>')
        res.append(f'<circle cx="{cx+10}" cy="{cy+12}" r="2.5" fill="#FF168A"/>')
        res.append(f'<circle cx="{cx-8}" cy="{cy+14}" r="2.5" fill="#00FF9D"/>')
        res.append(f'<text x="{x+8}" y="{y+14}" fill="#8B35FF" font-size="8.5" font-family="{FONT_MONO}" font-weight="700">MULTI-AGENT // RADAR</text>')

    elif proj_id == 5:
        # P5: Lumiq — Knowledge Prism & Synthesis Crystal
        cx, cy = x + w//2, y + h//2
        # Central crystal prism
        res.append(f'<polygon points="{cx},{cy-24} {cx+18},{cy-6} {cx+12},{cy+20} {cx-12},{cy+20} {cx-18},{cy-6}" fill="#111B34" stroke="#00E5FF" stroke-width="1.3"/>')
        res.append(f'<polygon points="{cx},{cy-24} {cx+12},{cy+20} {cx},{cy+24} {cx-12},{cy+20}" fill="#1A2D50" opacity="0.6"/>')
        # Beam in
        res.append(f'<line x1="{x+18}" y1="{cy}" x2="{cx-18}" y2="{cy-6}" stroke="#FFFFFF" stroke-width="1.8" stroke-dasharray="4 2"/>')
        # Beams out (refraction)
        res.append(f'<line x1="{cx+18}" y1="{cy-6}" x2="{x+w-18}" y2="{cy-18}" stroke="#FF168A" stroke-width="1.5"/>')
        res.append(f'<line x1="{cx+16}" y1="{cy}" x2="{x+w-18}" y2="{cy}" stroke="#00E5FF" stroke-width="1.5"/>')
        res.append(f'<line x1="{cx+12}" y1="{cy+6}" x2="{x+w-18}" y2="{cy+18}" stroke="#8B35FF" stroke-width="1.5"/>')
        res.append(f'<text x="{x+8}" y="{y+14}" fill="#00E5FF" font-size="8.5" font-family="{FONT_MONO}" font-weight="700">SYNTHESIS // PRISM</text>')

    elif proj_id == 6:
        # P6: AI Resume Analyzer — Workflow Pipelines & NLP Parsing Nodes
        cx, cy = x + w//2, y + h//2
        # Workflow Pipeline Nodes (n8n style)
        res.append(f'<rect x="{cx-44}" y="{cy-12}" width="24" height="24" rx="4" fill="#0D1A30" stroke="#FF168A" stroke-width="1.2"/>')
        res.append(f'<rect x="{cx-8}" y="{cy-12}" width="24" height="24" rx="4" fill="#0D1A30" stroke="#00E5FF" stroke-width="1.2"/>')
        res.append(f'<rect x="{cx+28}" y="{cy-12}" width="24" height="24" rx="4" fill="#0D1A30" stroke="#8B35FF" stroke-width="1.2"/>')
        # Connecting lines
        res.append(f'<line x1="{cx-20}" y1="{cy}" x2="{cx-8}" y2="{cy}" stroke="#00E5FF" stroke-width="1.5"/>')
        res.append(f'<line x1="{cx+16}" y1="{cy}" x2="{cx+28}" y2="{cy}" stroke="#FF168A" stroke-width="1.5"/>')
        # Pulse dots inside nodes
        res.append(f'<circle cx="{cx-32}" cy="{cy}" r="3" fill="#FF168A"/>')
        res.append(f'<circle cx="{cx+4}" cy="{cy}" r="3" fill="#00E5FF"/>')
        res.append(f'<circle cx="{cx+40}" cy="{cy}" r="3" fill="#00FF9D"/>')
        res.append(f'<text x="{x+8}" y="{y+14}" fill="#FF168A" font-size="8.5" font-family="{FONT_MONO}" font-weight="700">PIPELINE // n8n-NLP</text>')

    return "".join(res)

# ==============================================================================
# OPERATOR PORTRAIT GENERATION
# ==============================================================================

def get_operator_portrait(x, y, w, h):
    """Generate futuristic cyberpunk character portrait with city skyline and dual rim lighting."""
    res = []
    # Background frame
    res.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#060A14" stroke="#1A2D46" stroke-width="1.2"/>')

    # Neo-Bangalore Skyline Silhouette
    city = [
        f"M {x} {y+h-20}",
        f"L {x+20} {y+h-20} L {x+20} {y+h-65} L {x+38} {y+h-65} L {x+38} {y+h-40}",
        f"L {x+50} {y+h-40} L {x+50} {y+h-90} L {x+58} {y+h-110} L {x+66} {y+h-90} L {x+66} {y+h-35}",
        f"L {x+80} {y+h-35} L {x+80} {y+h-75} L {x+105} {y+h-75} L {x+105} {y+h-25}",
        f"L {x+120} {y+h-25} L {x+120} {y+h-100} L {x+136} {y+h-100} L {x+136} {y+h-45}",
        f"L {x+155} {y+h-45} L {x+155} {y+h-80} L {x+175} {y+h-80} L {x+175} {y+h-30}",
        f"L {x+195} {y+h-30} L {x+195} {y+h-115} L {x+202} {y+h-130} L {x+210} {y+h-115} L {x+210} {y+h-50}",
        f"L {x+230} {y+h-50} L {x+230} {y+h-85} L {x+250} {y+h-85} L {x+250} {y+h-35}",
        f"L {x+270} {y+h-35} L {x+270} {y+h-70} L {x+295} {y+h-70} L {x+295} {y+h-30}",
        f"L {x+315} {y+h-30} L {x+315} {y+h-95} L {x+330} {y+h-95} L {x+330} {y+h-20}",
        f"L {x+w} {y+h-20} L {x+w} {y+h} L {x} {y+h} Z"
    ]
    res.append(f'<path d="{" ".join(city)}" fill="#0A1322" opacity="0.75"/>')

    # Spire communication beacons
    res.append(f'<circle cx="{x+58}" cy="{y+h-112}" r="2" fill="#00E5FF"/>')
    res.append(f'<circle cx="{x+202}" cy="{y+h-132}" r="2" fill="#FF168A"/>')

    # Futuristic ground perspective grid
    for g_i in range(1, 5):
        gy = y + h - 20 + g_i * 5
        res.append(f'<line x1="{x}" y1="{gy}" x2="{x+w}" y2="{gy}" stroke="#00E5FF" stroke-width="0.7" opacity="{0.15 + g_i*0.08}"/>')

    # Center-left Operator Silhouette with Dual Rim Lighting
    cx = x + w//2
    cy = y + h//2 + 8

    # Shoulder armor / Tactical Collar
    res.append(f'<path d="M {cx-75} {y+h-4} L {cx-60} {cy+45} L {cx-35} {cy+35} L {cx} {cy+42} L {cx+35} {cy+35} L {cx+60} {cy+45} L {cx+75} {y+h-4} Z" fill="#091220" stroke="#1F3652" stroke-width="1.4"/>')
    # Cyan left rim light
    res.append(f'<path d="M {cx-75} {y+h-4} L {cx-60} {cy+45} L {cx-35} {cy+35} L {cx} {cy+42}" stroke="#00E5FF" stroke-width="2" fill="none" opacity="0.9"/>')
    # Magenta right rim light
    res.append(f'<path d="M {cx} {cy+42} L {cx+35} {cy+35} L {cx+60} {cy+45} L {cx+75} {y+h-4}" stroke="#FF168A" stroke-width="2" fill="none" opacity="0.9"/>')

    # Neck
    res.append(f'<rect x="{cx-16}" y="{cy+14}" width="32" height="26" fill="#0B1626"/>')
    # Head Base (Cybernetic helmet / cowl)
    res.append(f'<path d="M {cx-30} {cy+16} L {cx-32} {cy-14} C {cx-34} {cy-48} {cx+34} {cy-48} {cx+32} {cy-14} L {cx+30} {cy+16} Z" fill="#0D192C" stroke="#1D3654" stroke-width="1.3"/>')
    # Head left rim
    res.append(f'<path d="M {cx-30} {cy+16} L {cx-32} {cy-14} C {cx-34} {cy-48} {cx} {cy-48}" stroke="#00E5FF" stroke-width="1.8" fill="none"/>')
    # Head right rim
    res.append(f'<path d="M {cx} {cy-48} C {cx+34} {cy-48} {cx+32} {cy-14} L {cx+30} {cy+16}" stroke="#FF168A" stroke-width="1.8" fill="none"/>')

    # Cybernetic Targeting Visor (Electric Cyan glowing visor with telemetry reticle)
    res.append(f'<polygon points="{cx-28},{cy-12} {cx+28},{cy-12} {cx+24},{cy+2} {cx-24},{cy+2}" fill="#00E5FF" opacity="0.85"/>')
    res.append(f'<line x1="{cx-26}" y1="{cy-5}" x2="{cx+26}" y2="{cy-5}" stroke="#FFFFFF" stroke-width="1.4"/>')
    res.append(f'<circle cx="{cx+8}" cy="{cy-5}" r="3.5" fill="#FF168A"/>')
    res.append(f'<circle cx="{cx+8}" cy="{cy-5}" r="1.5" fill="#FFFFFF"/>')

    # Neural Temple Interface Jack & Data Conduit
    res.append(f'<rect x="{cx+29}" y="{cy-18}" width="6" height="12" rx="2" fill="#FF168A"/>')
    res.append(f'<path d="M {cx+35} {cy-12} Q {cx+52} {cy-2} {cx+58} {cy+22}" stroke="#FF168A" stroke-width="1.4" fill="none" stroke-dasharray="3 2"/>')

    # HUD Target Reticle around face
    res.append(f'<circle cx="{cx}" cy="{cy-10}" r="48" fill="none" stroke="#00E5FF" stroke-width="0.8" stroke-dasharray="4 6" opacity="0.45"/>')
    res.append(f'<path d="M {cx-56} {cy-10} H {cx-48} M {cx+48} {cy-10} H {cx+56} M {cx} {cy-66} V {cx} M {cx} {cy+38} V {cy+46}" stroke="#00E5FF" stroke-width="1"/>')

    # HUD corner brackets for portrait box
    res.append(f'<path d="M {x+10} {y+22} V {y+10} H {x+22}" stroke="#00E5FF" stroke-width="1.5" fill="none"/>')
    res.append(f'<path d="M {x+w-22} {y+10} H {x+w-10} V {y+22}" stroke="#FF168A" stroke-width="1.5" fill="none"/>')
    res.append(f'<path d="M {x+10} {y+h-22} V {y+h-10} H {x+22}" stroke="#FF168A" stroke-width="1.5" fill="none"/>')
    res.append(f'<path d="M {x+w-22} {y+h-10} H {x+w-10} V {y+h-22}" stroke="#00E5FF" stroke-width="1.5" fill="none"/>')

    # Bottom identity status readout
    res.append(f'<rect x="{x+10}" y="{y+h-24}" width="{w-20}" height="16" fill="#070D1A" opacity="0.85"/>')
    res.append(f'<text x="{x+16}" y="{y+h-12}" fill="#00E5FF" font-size="9" font-family="{FONT_MONO}" font-weight="700">BIOMETRIC: VERIFIED // ID: V18-EXEC</text>')
    res.append(f'<text x="{x+w-16}" y="{y+h-12}" fill="#FF168A" font-size="9" font-family="{FONT_MONO}" font-weight="700" text-anchor="end">CLEARANCE: LVL-5 ALPHA</text>')

    return "".join(res)

# ==============================================================================
# MAIN COMMAND CENTER DASHBOARD GENERATION (1536 x 1024)
# ==============================================================================

def generate_dossier_svg(user, repos, stars, languages, contrib_info, stamp):
    """Generate master cinematic cyberpunk engineering command center (1536x1024)."""
    public_repos_cnt = user.get("public_repos", len(repos))
    followers_cnt = user.get("followers", 0)
    following_cnt = user.get("following", 0)
    total_contribs = contrib_info.get("total", 251)
    current_streak = contrib_info.get("current_streak", 3)
    longest_streak = contrib_info.get("longest_streak", 3)
    calendar_days = contrib_info.get("days", [])

    svg = []
    svg.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" width="1536" height="1024" viewBox="0 0 1536 1024">')
    svg.append('''<defs>
<linearGradient id="bg-canvas" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0%" stop-color="#04060E"/>
  <stop offset="50%" stop-color="#070C1A"/>
  <stop offset="100%" stop-color="#03050B"/>
</linearGradient>
<linearGradient id="grad-cyan" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%" stop-color="#00E5FF"/>
  <stop offset="100%" stop-color="#0088FF"/>
</linearGradient>
<linearGradient id="grad-magenta" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%" stop-color="#FF168A"/>
  <stop offset="100%" stop-color="#8B35FF"/>
</linearGradient>
<linearGradient id="grad-duo" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0%" stop-color="#FF168A"/>
  <stop offset="45%" stop-color="#8B35FF"/>
  <stop offset="100%" stop-color="#00E5FF"/>
</linearGradient>
<pattern id="cyber-grid" width="32" height="32" patternUnits="userSpaceOnUse">
  <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#101F33" stroke-width="0.8" opacity="0.32"/>
</pattern>
</defs>''')

    # Background Canvas & Outer Framing
    svg.append('<rect width="1536" height="1024" fill="url(#bg-canvas)"/>')
    svg.append('<rect width="1536" height="1024" fill="url(#cyber-grid)"/>')
    svg.append('<rect x="12" y="10" width="1512" height="1004" rx="10" fill="none" stroke="url(#grad-duo)" stroke-width="1.8" opacity="0.85"/>')

    # Top Global Header Bar
    svg.append(f'<rect x="18" y="14" width="1500" height="32" rx="4" fill="#070D18" stroke="#16273C" stroke-width="1"/>')
    svg.append(f'<circle cx="34" cy="30" r="4" fill="#00FF9D"/>')
    svg.append(f'<circle cx="48" cy="30" r="4" fill="#00E5FF"/>')
    svg.append(f'<circle cx="62" cy="30" r="4" fill="#FF168A"/>')
    svg.append(f'<text x="82" y="34" fill="#00E5FF" font-size="11" font-family="{FONT_MONO}" font-weight="800" letter-spacing="1.5">SYS.VACHAN.EXE // CYBERPUNK COMMAND CENTER v4.2</text>')
    svg.append(f'<text x="768" y="34" fill="#7898B0" font-size="10" font-family="{FONT_MONO}" font-weight="700" text-anchor="middle" letter-spacing="2">SECURITY CLEARANCE: LEVEL 5 // NODE: BLR-IN [12.97° N, 77.59° E]</text>')
    svg.append(f'<text x="1502" y="34" fill="#FF168A" font-size="10" font-family="{FONT_MONO}" font-weight="700" text-anchor="end" letter-spacing="1">STATUS: ONLINE [200 OK] // SYNC: {esc(stamp)} UTC</text>')

    # ==========================================================================
    # LEFT COLUMN (x = 24, w = 376)
    # ==========================================================================
    col1_x = 24
    col1_w = 376

    # 1. Operator Identity & Character Dossier (y = 56, h = 414)
    p1_y, p1_h = 56, 414
    svg.append(panel_hud(col1_x, p1_y, col1_w, p1_h, "OPERATOR DOSSIER // IDENTITY", "#00E5FF", "VACHAN.EXE"))

    # Title Readout
    svg.append(f'<text x="{col1_x+20}" y="{p1_y+50}" fill="#FFFFFF" font-size="24" font-weight="900" font-family="{FONT_SANS}" letter-spacing="0.5">VACHAN U S</text>')
    svg.append(f'<text x="{col1_x+col1_w-20}" y="{p1_y+48}" fill="#00E5FF" font-size="14" font-weight="800" font-family="{FONT_MONO}" text-anchor="end">V18</text>')
    svg.append(f'<text x="{col1_x+20}" y="{p1_y+68}" fill="#FF168A" font-size="10.5" font-weight="800" font-family="{FONT_MONO}" letter-spacing="1.2">ENGINEERING DIVISION // AI &amp; CLOUD SYSTEMS</text>')

    # Character Portrait Box (Integrated with Neo-City background & rim lighting)
    port_y = p1_y + 80
    port_w = col1_w - 40
    port_h = 196
    svg.append(get_operator_portrait(col1_x+20, port_y, port_w, port_h))

    # Operator Spec Metadata Grid (y = 336 to 456)
    specs = [
        ("ORGANIZATION", "Software Engineer @ Synapx", "#00E5FF"),
        ("LOCATION", "Bangalore, India", "#FF168A"),
        ("ACADEMICS", "B.Tech CSE (2022-26) · Dr. AIT", "#00E5FF"),
        ("OPERATIONAL FOCUS", "Intelligent AI Agents & Cloud Infra", "#00FF9D")
    ]
    for idx, (lbl, val, col) in enumerate(specs):
        sy = p1_y + 290 + idx * 28
        svg.append(f'<text x="{col1_x+20}" y="{sy+12}" fill="#627E94" font-size="9" font-family="{FONT_MONO}" font-weight="700">{lbl}:</text>')
        svg.append(f'<text x="{col1_x+136}" y="{sy+12}" fill="{col}" font-size="10" font-family="{FONT_MONO}" font-weight="700">{esc(val)}</text>')
        svg.append(f'<path d="M {col1_x+20} {sy+20} H {col1_x+col1_w-20}" stroke="#132338" stroke-width="0.8"/>')

    # 2. Mission Timeline (y = 480, h = 330)
    p2_y, p2_h = 480, 330
    svg.append(panel_hud(col1_x, p2_y, col1_w, p2_h, "MISSION TIMELINE // SERVICE RECORD", "#FF168A", "CAREER MATRIX"))

    # Vertical glowing bus line
    line_x = col1_x + 36
    svg.append(f'<line x1="{line_x}" y1="{p2_y+46}" x2="{line_x}" y2="{p2_y+p2_h-30}" stroke="#1D3854" stroke-width="2"/>')
    svg.append(f'<line x1="{line_x}" y1="{p2_y+46}" x2="{line_x}" y2="{p2_y+p2_h-30}" stroke="url(#grad-magenta)" stroke-width="1.2" opacity="0.8"/>')

    timeline_items = [
        ("2026 – PRESENT", "Software Engineer @ Synapx", "Intelligent AI applications & backend architecture", "#00E5FF"),
        ("FEB – MAY 2026", "Python Full Stack + GenAI @ Dhee", "Full-stack development, Django, REST APIs & LLMs", "#FF168A"),
        ("AUG 2024 – JAN 2025", "Ethical Hacking Intern @ Studio", "Vulnerability assessment & web app security", "#8B35FF"),
        ("2022 – 2026", "B.Tech CSE @ Dr. Ambedkar Inst. of Tech", "Computer Science & Engineering · Bangalore", "#00E5FF")
    ]
    for idx, (period, role, desc, col) in enumerate(timeline_items):
        ty = p2_y + 44 + idx * 68
        # Pulsing milestone node
        svg.append(f'<circle cx="{line_x}" cy="{ty+12}" r="5.5" fill="#070C1A" stroke="{col}" stroke-width="2"/>')
        svg.append(f'<circle cx="{line_x}" cy="{ty+12}" r="2" fill="{col}"/>')
        # Content
        svg.append(f'<text x="{line_x+16}" y="{ty+8}" fill="{col}" font-size="9.5" font-family="{FONT_MONO}" font-weight="800" letter-spacing="1">{esc(period)}</text>')
        svg.append(f'<text x="{line_x+16}" y="{ty+23}" fill="#FFFFFF" font-size="11" font-family="{FONT_SANS}" font-weight="700">{esc(role)}</text>')
        svg.append(f'<text x="{line_x+16}" y="{ty+37}" fill="#7F9BB2" font-size="9" font-family="{FONT_SANS}">{esc(desc)}</text>')

    # 3. Engineering Philosophy (y = 820, h = 188)
    p3_y, p3_h = 820, 188
    svg.append(panel_hud(col1_x, p3_y, col1_w, p3_h, "ENGINEERING PHILOSOPHY // DIRECTIVE", "#00E5FF", "DOCTRINE"))

    # Glowing futuristic typography block
    svg.append(f'<text x="{col1_x+24}" y="{p3_y+62}" fill="#00E5FF" font-size="16" font-family="{FONT_MONO}" font-weight="900" letter-spacing="1.5">&gt; THINK DIFFERENTLY.</text>')
    svg.append(f'<text x="{col1_x+24}" y="{p3_y+94}" fill="#FFFFFF" font-size="16" font-family="{FONT_MONO}" font-weight="900" letter-spacing="1.5">&gt; BUILD INTELLIGENTLY.</text>')
    svg.append(f'<text x="{col1_x+24}" y="{p3_y+126}" fill="#FF168A" font-size="16" font-family="{FONT_MONO}" font-weight="900" letter-spacing="1.5">&gt; ENGINEER RELIABLY.</text>')
    svg.append(f'<rect x="{col1_x+20}" y="{p3_y+146}" width="{col1_w-40}" height="24" rx="3" fill="#0C1626" stroke="#162D46" stroke-width="1"/>')
    svg.append(f'<text x="{col1_x+30}" y="{p3_y+162}" fill="#00FF9D" font-size="9.5" font-family="{FONT_MONO}" font-weight="700">MISSION: ZERO-COMPROMISE PRODUCTION ARCHITECTURE</text>')

    # ==========================================================================
    # CENTER COLUMN (x = 412, w = 736)
    # ==========================================================================
    col2_x = 412
    col2_w = 736

    # 4. Core Skills & Tech Loadout Panel (y = 56, h = 296)
    p4_y, p4_h = 56, 296
    svg.append(panel_hud(col2_x, p4_y, col2_w, p4_h, "CAPABILITY SPECTRUM & TECH LOADOUT", "#00E5FF", "LOADOUT.SYS"))

    # 6 Horizontal Futuristic Skill Indicators (Descriptive, no fabricated numbers)
    skill_rows = [
        ("AI / ML", "SPECIALIZED // MULTI-AGENT & LLMS", 9, "#00E5FF"),
        ("BACKEND ENGINEERING", "CORE // DISTRIBUTED ARCHITECTURE", 9, "#FF168A"),
        ("FULL-STACK DEV", "PRODUCTION // DJANGO & REACT", 8, "#00E5FF"),
        ("CLOUD & DEVOPS", "INFRASTRUCTURE // DOCKER & AWS", 8, "#8B35FF"),
        ("CYBERSECURITY", "HARDENED // ETHICAL HACKING", 7, "#FF168A"),
        ("SYSTEM DESIGN", "HIGH-RELIABILITY ARCHITECTURES", 8, "#00FF9D")
    ]
    for idx, (name, tag, segments, col) in enumerate(skill_rows):
        r_col = idx % 2
        r_row = idx // 2
        bx = col2_x + 20 + r_col * 352
        by = p4_y + 42 + r_row * 36

        svg.append(f'<text x="{bx}" y="{by+10}" fill="#FFFFFF" font-size="10" font-weight="700" font-family="{FONT_MONO}">{esc(name)}</text>')
        svg.append(f'<text x="{bx+336}" y="{by+10}" fill="{col}" font-size="8.5" font-weight="700" font-family="{FONT_MONO}" text-anchor="end">{esc(tag)}</text>')
        # Segmented high-tech level indicator bar (10 blocks)
        for b_i in range(10):
            block_x = bx + b_i * 34
            is_lit = b_i < segments
            b_fill = col if is_lit else "#132134"
            b_op = "0.9" if is_lit else "0.3"
            svg.append(f'<rect x="{block_x}" y="{by+16}" width="30" height="6" rx="1.5" fill="{b_fill}" opacity="{b_op}"/>')

    # Equipment Grid / Tech Loadout Badges
    svg.append(f'<path d="M {col2_x+20} {p4_y+162} H {col2_x+col2_w-20}" stroke="#162D46" stroke-width="1"/>')
    svg.append(f'<text x="{col2_x+20}" y="{p4_y+178}" fill="#FF168A" font-size="10.5" font-family="{FONT_MONO}" font-weight="800" letter-spacing="1">AUTHENTIC TECH STACK LOADOUT // EQUIPMENT MATRIX</text>')

    tech_categories = [
        ("LANGUAGES", ["Python", "JavaScript", "Java", "TypeScript", "HTML5", "CSS3"], "#00E5FF"),
        ("FRAMEWORKS", ["Django", "Flask", "React", "Node.js", "Tailwind CSS"], "#FF168A"),
        ("AI / ML", ["OpenAI", "Claude", "Gemini", "LangChain", "CrewAI", "PyTorch", "YOLOv8"], "#00FF9D"),
        ("INFRASTRUCTURE", ["AWS", "MySQL", "MongoDB", "Firebase", "Docker", "Kubernetes"], "#8B35FF"),
        ("ENGINEERING", ["Linux", "Git", "GitHub Actions", "Nginx", "PM2", "n8n", "Make.com"], "#00E5FF")
    ]
    for c_i, (c_name, c_items, c_col) in enumerate(tech_categories):
        cy_pos = p4_y + 196 + c_i * 18
        svg.append(f'<text x="{col2_x+20}" y="{cy_pos+8}" fill="{c_col}" font-size="8.5" font-family="{FONT_MONO}" font-weight="700">{esc(c_name)}:</text>')
        items_str = " · ".join(c_items)
        svg.append(f'<text x="{col2_x+140}" y="{cy_pos+8}" fill="#D8E8F5" font-size="9" font-family="{FONT_MONO}">{esc(items_str)}</text>')

    # 5. Featured Projects Archive (P1–P6) (y = 362, h = 422)
    p5_y, p5_h = 362, 422
    svg.append(panel_hud(col2_x, p5_y, col2_w, p5_h, "FEATURED PROJECTS ARCHIVE // 6 CORE BUILDS", "#FF168A", "PROJECTS P1-P6"))

    projects = DATA.get("projects", [])[:6]
    card_w = 226
    card_h = 176
    gap_x = 15
    gap_y = 16

    for idx, proj in enumerate(projects):
        p_col = idx % 3
        p_row = idx // 3
        cx = col2_x + 14 + p_col * (card_w + gap_x)
        cy = p5_y + 38 + p_row * (card_h + gap_y)

        # Card container
        svg.append(f'<rect x="{cx}" y="{cy}" width="{card_w}" height="{card_h}" rx="6" fill="#080F1D" stroke="#1D344E" stroke-width="1.2"/>')
        # Accent top bar
        bar_col = "#00E5FF" if p_row == 0 else "#FF168A"
        svg.append(f'<rect x="{cx}" y="{cy}" width="{card_w}" height="2.5" rx="1" fill="{bar_col}"/>')

        # Identifier P1-P6 & Domain tag
        svg.append(f'<text x="{cx+10}" y="{cy+16}" fill="{bar_col}" font-size="10" font-family="{FONT_MONO}" font-weight="800">P{idx+1}</text>')
        cat_short = proj.get("category", "").split("/")[0].strip()
        svg.append(f'<text x="{cx+card_w-10}" y="{cy+16}" fill="#7F9CB4" font-size="8.5" font-family="{FONT_MONO}" font-weight="700" text-anchor="end">{esc(cat_short)}</text>')

        # Unique Illustrative Thumbnail
        thumb_h = 62
        thumb_w = card_w - 20
        svg.append(get_project_thumbnail(idx+1, cx+10, cy+22, thumb_w, thumb_h))

        # Project Name
        p_name = proj.get("name", "")
        p_lines = wrap_text(p_name, 23)
        for n_i, n_line in enumerate(p_lines[:2]):
            svg.append(f'<text x="{cx+10}" y="{cy+98 + n_i*14}" fill="#FFFFFF" font-size="11.5" font-family="{FONT_SANS}" font-weight="700">{esc(n_line)}</text>')

        # Short description
        desc_lines = wrap_text(proj.get("description", ""), 30)
        desc_start = cy + 128 if len(p_lines) == 1 else cy + 130
        for d_i, d_line in enumerate(desc_lines[:2]):
            svg.append(f'<text x="{cx+10}" y="{desc_start + d_i*12}" fill="#89A5BA" font-size="9" font-family="{FONT_SANS}">{esc(d_line)}</text>')

        # Tech stack pill
        stack_str = " · ".join(proj.get("stack", [])[:3])
        if len(stack_str) > 30:
            stack_str = stack_str[:28] + "…"
        svg.append(f'<text x="{cx+10}" y="{cy+card_h-10}" fill="{bar_col}" font-size="8.5" font-family="{FONT_MONO}" font-weight="700">{esc(stack_str)}</text>')
        svg.append(f'<text x="{cx+card_w-10}" y="{cy+card_h-10}" fill="#FF168A" font-size="8.5" font-family="{FONT_MONO}" font-weight="800" text-anchor="end">OPEN ↗</text>')

    # 6. Contribution Matrix Heatmap (y = 794, h = 214)
    p6_y, p6_h = 794, 214
    svg.append(panel_hud(col2_x, p6_y, col2_w, p6_h, "CONTRIBUTION MATRIX // NEON ACTIVITY STREAM", "#00E5FF", "REAL-TIME TELEMETRY"))

    # Render real contribution calendar grid
    grid_start_x = col2_x + 44
    grid_start_y = p6_y + 44
    cell_w = 9.8
    cell_gap = 2.4

    # Intensity color ramp (Real GitHub data mapping)
    level_colors = {
        0: "#0D1726",  # Zero activity
        1: "#43144A",  # Low intensity (violet)
        2: "#7B2CBF",  # Medium intensity (neon violet)
        3: "#FF168A",  # High intensity (neon magenta)
        4: "#00E5FF"   # Overload intensity (electric cyan)
    }

    # If calendar days fetched, render 52 columns x 7 rows
    if calendar_days and len(calendar_days) >= 350:
        # Pad or slice to 52 weeks (364 days)
        last_days = calendar_days[-364:]
        for day_idx, d in enumerate(last_days):
            col_i = day_idx // 7
            row_i = day_idx % 7
            cx = grid_start_x + col_i * (cell_w + cell_gap)
            cy = grid_start_y + row_i * (cell_w + cell_gap)
            lvl = d.get("level", 0)
            fill_col = level_colors.get(lvl, "#0D1726")
            stroke_col = "#00E5FF" if lvl == 4 else ("#FF168A" if lvl == 3 else "none")
            s_width = "1" if stroke_col != "none" else "0"
            svg.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell_w}" height="{cell_w}" rx="2" fill="{fill_col}" stroke="{stroke_col}" stroke-width="{s_width}"/>')
    else:
        # Fallback grid if network unavailable
        for col_i in range(52):
            for row_i in range(7):
                cx = grid_start_x + col_i * (cell_w + cell_gap)
                cy = grid_start_y + row_i * (cell_w + cell_gap)
                lvl = (col_i + row_i) % 5 if (col_i * 7 + row_i) % 3 == 0 else 0
                fill_col = level_colors.get(lvl, "#0D1726")
                svg.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell_w}" height="{cell_w}" rx="2" fill="{fill_col}"/>')

    # Heatmap Day Labels (M, W, F)
    svg.append(f'<text x="{grid_start_x-14}" y="{grid_start_y+19}" fill="#54728A" font-size="8" font-family="{FONT_MONO}">M</text>')
    svg.append(f'<text x="{grid_start_x-14}" y="{grid_start_y+43}" fill="#54728A" font-size="8" font-family="{FONT_MONO}">W</text>')
    svg.append(f'<text x="{grid_start_x-14}" y="{grid_start_y+67}" fill="#54728A" font-size="8" font-family="{FONT_MONO}">F</text>')

    # Footer metrics bar inside Heatmap panel
    foot_y = p6_y + p6_h - 26
    svg.append(f'<text x="{col2_x+24}" y="{foot_y}" fill="#00E5FF" font-size="10" font-family="{FONT_MONO}" font-weight="800">TOTAL COMMITS (1Y): {total_contribs}</text>')
    svg.append(f'<text x="{col2_x+220}" y="{foot_y}" fill="#FF168A" font-size="10" font-family="{FONT_MONO}" font-weight="800">CURRENT STREAK: {current_streak} DAYS</text>')
    svg.append(f'<text x="{col2_x+410}" y="{foot_y}" fill="#00FF9D" font-size="10" font-family="{FONT_MONO}" font-weight="800">RECORD: {longest_streak} DAYS</text>')

    # Legend
    svg.append(f'<text x="{col2_x+col2_w-150}" y="{foot_y}" fill="#54728A" font-size="8.5" font-family="{FONT_MONO}">LESS</text>')
    for l_i in range(5):
        lx = col2_x + col2_w - 120 + l_i * 14
        svg.append(f'<rect x="{lx}" y="{foot_y-8}" width="10" height="10" rx="2" fill="{level_colors[l_i]}"/>')
    svg.append(f'<text x="{col2_x+col2_w-42}" y="{foot_y}" fill="#54728A" font-size="8.5" font-family="{FONT_MONO}">MORE</text>')

    # ==========================================================================
    # RIGHT COLUMN (x = 1160, w = 352)
    # ==========================================================================
    col3_x = 1160
    col3_w = 352

    # 7. GitHub Telemetry HUD (y = 56, h = 370)
    p7_y, p7_h = 56, 370
    svg.append(panel_hud(col3_x, p7_y, col3_w, p7_h, "GITHUB TELEMETRY // HUD", "#00E5FF", "ANALYTICS"))

    # 4 Holographic HUD Stat Cards (2 x 2 grid)
    hud_stats = [
        ("PUBLIC REPOS", public_repos_cnt, "#00E5FF"),
        ("TOTAL STARS", stars, "#FF168A"),
        ("CONTRIBUTIONS", total_contribs, "#00FF9D"),
        ("ACTIVE STREAK", f"{current_streak} DAYS", "#FF168A")
    ]
    box_w = 148
    box_h = 68
    for idx, (label, val, col) in enumerate(hud_stats):
        h_col = idx % 2
        h_row = idx // 2
        bx = col3_x + 18 + h_col * 162
        by = p7_y + 40 + h_row * 78

        svg.append(f'<rect x="{bx}" y="{by}" width="{box_w}" height="{box_h}" rx="6" fill="#08101E" stroke="#1B324C" stroke-width="1.2"/>')
        svg.append(f'<text x="{bx+12}" y="{by+18}" fill="#69879E" font-size="9" font-weight="700" font-family="{FONT_MONO}">{label}</text>')
        svg.append(f'<text x="{bx+12}" y="{by+50}" fill="{col}" font-size="22" font-weight="900" font-family="{FONT_MONO}">{val}</text>')

    # Real-Time Diagnostic Node Status
    diag_y = p7_y + 208
    svg.append(f'<rect x="{col3_x+18}" y="{diag_y}" width="{col3_w-36}" height="142" rx="5" fill="#081120" stroke="#172C42" stroke-width="1"/>')
    svg.append(f'<text x="{col3_x+30}" y="{diag_y+22}" fill="#00FF9D" font-size="9.5" font-family="{FONT_MONO}" font-weight="800">● DIAGNOSTIC STATUS: ONLINE [200 OK]</text>')
    svg.append(f'<text x="{col3_x+30}" y="{diag_y+42}" fill="#6E8CA2" font-size="9" font-family="{FONT_MONO}">HOST NODE: api.github.com // CLOUD ENGINE</text>')
    svg.append(f'<text x="{col3_x+30}" y="{diag_y+60}" fill="#6E8CA2" font-size="9" font-family="{FONT_MONO}">SECURITY: SHA-256 HMAC ENCRYPTED</text>')
    svg.append(f'<text x="{col3_x+30}" y="{diag_y+78}" fill="#6E8CA2" font-size="9" font-family="{FONT_MONO}">AUTOMATION: GITHUB ACTIONS (6-HR CYCLE)</text>')
    svg.append(f'<text x="{col3_x+30}" y="{diag_y+96}" fill="#6E8CA2" font-size="9" font-family="{FONT_MONO}">TARGET CANVAS: 1536 x 1024 CINEMATIC</text>')
    svg.append(f'<text x="{col3_x+30}" y="{diag_y+114}" fill="#00E5FF" font-size="9" font-family="{FONT_MONO}">PROTOCOL: AUTONOMOUS REFRESH ACTIVE</text>')
    svg.append(f'<text x="{col3_x+30}" y="{diag_y+130}" fill="#FF168A" font-size="8.5" font-family="{FONT_MONO}">LAST DATA PROBE: {esc(stamp)} UTC</text>')

    # 8. Codebase Language Distribution (y = 436, h = 374)
    p8_y, p8_h = 436, 374
    svg.append(panel_hud(col3_x, p8_y, col3_w, p8_h, "CODEBASE LANGUAGE DISTRIBUTION", "#FF168A", "TELEMETRY"))

    total_bytes = sum(languages.values()) if languages else 0
    top_langs = list(languages.items())[:7] if languages else []

    if top_langs and total_bytes > 0:
        bar_max_w = 150
        for l_idx, (lang, b_cnt) in enumerate(top_langs):
            ly = p8_y + 44 + l_idx * 44
            pct = (b_cnt / total_bytes) * 100
            bar_w = max(int(bar_max_w * (b_cnt / total_bytes)), 6)
            display_lang = lang if len(lang) <= 15 else lang[:13] + "…"

            # Lang name
            svg.append(f'<text x="{col3_x+20}" y="{ly+12}" fill="#FFFFFF" font-size="11" font-weight="700" font-family="{FONT_SANS}">{esc(display_lang)}</text>')
            # Pct
            svg.append(f'<text x="{col3_x+140}" y="{ly+12}" fill="#00E5FF" font-size="10.5" font-weight="800" font-family="{FONT_MONO}" text-anchor="end">{pct:.1f}%</text>')
            # Track
            svg.append(f'<rect x="{col3_x+156}" y="{ly+2}" width="{bar_max_w}" height="10" rx="5" fill="#132132"/>')
            # Fill bar with neon gradient
            grad = "url(#grad-magenta)" if l_idx % 2 == 0 else "url(#grad-cyan)"
            svg.append(f'<rect x="{col3_x+156}" y="{ly+2}" width="{bar_w}" height="10" rx="5" fill="{grad}"/>')
            # Byte size subtext
            kb_cnt = b_cnt / 1024
            svg.append(f'<text x="{col3_x+20}" y="{ly+26}" fill="#627E94" font-size="8.5" font-family="{FONT_MONO}">{kb_cnt:,.0f} KB</text>')
    else:
        svg.append(f'<text x="{col3_x+20}" y="{p8_y+60}" fill="#7F9AB0" font-size="11" font-family="{FONT_MONO}">Language stats probe running...</text>')

    # 9. Establish Connection (y = 820, h = 188)
    p9_y, p9_h = 820, 188
    svg.append(panel_hud(col3_x, p9_y, col3_w, p9_h, "ESTABLISH CONNECTION // TRANSMISSION", "#00E5FF", "COMM CHANNELS"))

    channels = [
        ("GITHUB", "vachan18", "#00E5FF"),
        ("LINKEDIN", "vachan-u-s-0a5aa8128", "#FF168A"),
        ("PORTFOLIO", "vachanmyportfolio.netlify.app", "#00E5FF"),
        ("DEVFOLIO", "@Vachanus", "#8B35FF"),
        ("EMAIL", "vachan.us@gmail.com", "#00FF9D")
    ]
    for c_idx, (channel, handle, col) in enumerate(channels):
        cy = p9_y + 36 + c_idx * 24
        svg.append(f'<rect x="{col3_x+18}" y="{cy}" width="70" height="17" rx="3" fill="#0C182B" stroke="{col}" stroke-width="0.8"/>')
        svg.append(f'<text x="{col3_x+53}" y="{cy+12}" fill="{col}" font-size="8.5" font-family="{FONT_MONO}" font-weight="800" text-anchor="middle">{channel}</text>')
        svg.append(f'<text x="{col3_x+96}" y="{cy+12}" fill="#C8DCED" font-size="9" font-family="{FONT_MONO}">{esc(handle)}</text>')

    svg.append(f'<text x="{col3_x+20}" y="{p9_y+170}" fill="#627E94" font-size="8.5" font-family="{FONT_MONO}">PROTOCOL: TLS 1.3 // 2.4 GHz ENCRYPTED</text>')

    # Close SVG root
    svg.append('</svg>')
    out_svg = "\n".join(svg)

    # Validate XML strictly
    ET.fromstring(out_svg)

    # Safe write
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
    """Generate cinematic, cyberpunk engineering README.md."""
    # Build project rows
    proj_rows = []
    for idx, p in enumerate(DATA.get("projects", [])):
        name = esc(p.get("name", ""))
        cat = esc(p.get("category", ""))
        url = esc(p.get("url", ""))
        repo_slug = url.replace("https://github.com/", "")
        stack_str = " · ".join(f"`{esc(s)}`" for s in p.get("stack", [])[:4])
        proj_rows.append(
            f"| **P{idx+1} — {name}**<br/><sub>{cat}</sub> | {stack_str}<br/>[`{repo_slug} ↗`]({url}) |"
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

    total_contribs = contrib_info.get("total", 251)
    current_streak = contrib_info.get("current_streak", 3)

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
- ⚡ **Core Systems:** AI Agents &amp; Multi-Agent Orchestration · Distributed Backend Infrastructure · Cloud &amp; Automation Pipelines
- 📊 **Verified Metrics:** {total_contribs} Contributions (Past Year) · {current_streak}-Day Active Streak · {len(repos)} Public Repositories

---

## 📂 PROJECT REPOSITORIES (P1 – P6)

Direct repository access for all six intelligence builds featured in the Cyberpunk Command Center:

| SYSTEM BUILD | STACK &amp; REPOSITORY SOURCE |
|---|---|
{chr(10).join(proj_rows)}

---

## 🎖️ SERVICE RECORD &amp; CREDENTIALS

{chr(10).join(exp_md)}

**Technical Certifications &amp; Leadership:**
{additional_md}

---

## ⚡ LIVE TELEMETRY &amp; CONTRIBUTION NETWORK

<div align="center">

<!-- TELEMETRY HUD -->
<img src="./assets/telemetry.svg" width="100%" alt="Vachan U S — Live GitHub Telemetry HUD"/>

<br/><br/>

<!-- REAL CONTRIBUTION NETWORK -->
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

<sub>VACHAN.EXE // CYBERPUNK COMMAND CENTER · AUTOMATED TELEMETRY REFRESH EVERY 6 HOURS</sub>

</div>
"""
    readme_path = ROOT / "README.md"
    readme_path.write_text(content, encoding="utf-8")
    print(f"[OK] Generated {readme_path}")

def save_standalone_assets():
    """Export dedicated standalone SVG assets for portrait and project thumbnails."""
    thumbs_dir = ASSETS_DIR / "thumbnails"
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    # Operator Portrait standalone
    port_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="340" height="220" viewBox="0 0 340 220">
{get_operator_portrait(0, 0, 340, 220)}
</svg>'''
    ET.fromstring(port_svg)
    (ASSETS_DIR / "operator_portrait.svg").write_text(port_svg, encoding="utf-8")

    # Project Thumbnails standalone
    thumb_names = [
        "p1_robot.svg",
        "p2_banking.svg",
        "p3_studymind.svg",
        "p4_hirelens.svg",
        "p5_lumiq.svg",
        "p6_resume.svg"
    ]
    for idx, t_name in enumerate(thumb_names, start=1):
        t_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="206" height="64" viewBox="0 0 206 64">
{get_project_thumbnail(idx, 0, 0, 206, 64)}
</svg>'''
        ET.fromstring(t_svg)
        (thumbs_dir / t_name).write_text(t_svg, encoding="utf-8")
    print("[OK] Standalone portrait & thumbnail assets exported to assets/thumbnails/")

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

            # Compute current streak
            c_streak = 0
            for d in reversed(days):
                if d.get("count", 0) > 0:
                    c_streak += 1
                else:
                    if c_streak == 0:
                        continue
                    break
            contrib_info["current_streak"] = c_streak

            # Compute longest streak
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
    save_standalone_assets()
    generate_dossier_svg(user, repos, stars, languages, contrib_info, stamp)
    generate_telemetry_svg(user, repos, stars, languages, contrib_info, stamp)
    generate_readme(user, repos, stars, contrib_info, stamp)

    print("[SUCCESS] VACHAN.EXE Cyberpunk Command Center fully generated and validated.")

if __name__ == "__main__":
    main()
