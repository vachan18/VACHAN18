# Profile cards: how this works

The README is a column of animated SVG images. Each SVG embeds its own fonts (base64 WOFF)
and animates with inline CSS keyframes and SMIL, the only techniques that survive GitHub's
`<img>` sandbox (no scripts, no external requests). The layout lives in `README.md`.

| Path | What |
|---|---|
| `profile-data.json` | Your text: name, role, bio, tiles, featured repos |
| `scripts/fetch_contributions.py` | GitHub API to `data/contributions.json` (calendar, streaks, repo stats) |
| `scripts/render_readme_cards.py` | Draws every card into `cards/` |
| `scripts/make_ascii.py` | `source-photo.png` to `data/ascii.txt` (hero portrait) |
| `scripts/subset_fonts.py` | One-off: rebuilds `fonts/*.woff` subsets |
| `.github/workflows/update-profile-art.yml` | Daily: fetch, render, commit |
| `legacy/` | The previous cyberpunk README, kept for reference |

## Common tasks

```bash
pip install -r scripts/requirements.txt
python scripts/fetch_contributions.py           # uses GITHUB_TOKEN or `gh auth token`
python scripts/render_readme_cards.py           # animated cards
STATIC=1 python scripts/render_readme_cards.py  # end-state cards, for screenshots
python -m unittest discover -s tests -v
```

**Change your photo:** save it as `source-photo.png` in the repo root, then run
`python scripts/make_ascii.py` and render again. A plain light background and a front-facing
face work best. Tune with `--cols 100 --contrast 1.8 --threshold 225`.

**Change tiles or featured repos:** edit `tiles` / `featured_repos` in `profile-data.json`,
then fetch and render. If a repo card file name changes, update its `<img>` in `README.md`.
The tests fail if the README points at a card that doesn't exist.

**Gotcha:** keep the `<div align="center">` block in README.md free of blank lines, and keep
each row of three cards on a single line with no spaces between tags.
