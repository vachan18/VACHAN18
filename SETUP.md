# VACHAN.EXE — Cyberpunk GitHub Profile Dashboard

## Install

1. Download and unzip this package.
2. Open your profile repository: https://github.com/vachan18/vachan18
3. Copy the contents of this folder into the repository root, preserving `.github/workflows`.
4. Commit and push to the `main` branch.
5. Open the repository's **Actions** tab and run **Refresh Cyberpunk Engineering Dossier** once with **Run workflow** if it has not run automatically.
6. Check that `assets/dossier.svg` and `README.md` are updated by the workflow.

## Automatic updates

The workflow runs every six hours and when `profile-data.json`, scripts, or workflow files change. It uses the built-in `GITHUB_TOKEN`; no personal access token is required for public profile data.

GitHub Actions must be enabled, and the workflow needs repository `contents: write` permission.

## Customize

Edit `profile-data.json` to update skills, career history, education, projects, project descriptions, repository URLs, and social links.

The GitHub API updates public repository count, followers, following, stars, and language totals. Career history and skills stay under your control.

## Notes

- The included SVG is a fallback. It shows dashes for live metrics until the first successful workflow run.
- GitHub README does not execute custom JavaScript. This package generates SVG artwork and Markdown at build time.
- The contribution snake is referenced only if your existing snake workflow publishes it to the `output` branch.
- If your default branch is `master`, update the workflow branch references.
- Review your public email in `profile-data.json` before publishing.
