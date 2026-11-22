# VACHAN.EXE — Cyberpunk GitHub Profile Dashboard

Automated, code-generated Cyberpunk Engineering Dossier for GitHub Profile.

## 1. Directory Structure

```text
vachan18/
├── .github/
│   └── workflows/
│       ├── refresh-dashboard.yml    # Auto-refreshes SVG dossier and README every 6 hours
│       └── snake.yml                # Generates contribution snake animation to 'output' branch
├── assets/
│   ├── dossier.svg                  # Primary 1500x1040 Cyberpunk Engineering Dossier
│   └── telemetry.svg                # Standalone 800x420 Live GitHub Telemetry HUD
├── scripts/
│   └── generate_dashboard.py        # Python SVG/Markdown generator with GitHub API integration
├── profile-data.json                # Single source of truth for operator details & projects
├── README.md                        # Rendered GitHub profile page
├── SETUP.md                         # Architecture, automation, and operational guide
└── .gitignore                       # Standard Python and environment ignore rules
```

---

## 2. Automated Telemetry Updates

The GitHub Actions workflow (`.github/workflows/refresh-dashboard.yml`) executes:
- **Scheduled:** Automatically every 6 hours (`17 */6 * * *`).
- **Push Trigger:** On any commit modifying `profile-data.json`, `scripts/**`, or `.github/workflows/refresh-dashboard.yml` on the `main` branch.
- **Manual Trigger:** On-demand via `workflow_dispatch` in the GitHub Actions console.

### Permissions
The workflow uses the standard built-in `GITHUB_TOKEN` with:
```yaml
permissions:
  contents: write
```
No external or personal access tokens (PAT) are required.

---

## 3. Local Testing & Verification

To run and verify the generator locally:

```bash
# Make sure you are in the repository root
cd C:\Users\vacha\vachan18

# Execute the generator
python scripts/generate_dashboard.py
```

The generator will:
1. Connect to GitHub API (utilizing `gh auth token` or unauthenticated public rate limits).
2. Query user profile telemetry and compute star totals.
3. Query language byte weights across all public repositories.
4. Render `assets/dossier.svg` and `assets/telemetry.svg` as valid XML.
5. Generate `README.md` with links and updated timestamps.

---

## 4. Customization Guide

- **Profile & Projects:** Edit `profile-data.json` to update your role, bio, location, education, skills, career history, or featured projects.
- **Visual Design:** Edit `scripts/generate_dashboard.py` to customize the cyberpunk HUD colors, panel layouts, or typographic elements.
- **Automatic vs Manual:**
  - **Automatic (GitHub API):** Public repositories, followers, following, stars, and language distribution.
  - **Manual (`profile-data.json`):** Operator bio, role, company, education, skill matrices, and project descriptions.
