#!/usr/bin/env python3
"""Fetch the last year of GitHub contributions + featured repo metadata.

Writes data/contributions.json, which render_readme_cards.py reads.
Token: PROFILE_TOKEN (a personal token, so private contributions are counted),
then GITHUB_TOKEN, then `gh auth token` locally.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from collections import OrderedDict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE = json.loads((ROOT / "profile-data.json").read_text(encoding="utf-8"))
USER = PROFILE["username"]
OUT = ROOT / "data" / "contributions.json"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
    repositories(privacy: PUBLIC, ownerAffiliations: OWNER) { totalCount }
  }
}
"""


def get_token() -> str:
    token = (os.getenv("PROFILE_TOKEN") or os.getenv("GITHUB_TOKEN") or "").strip()
    if not token and shutil.which("gh"):
        try:
            token = subprocess.check_output(
                ["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except Exception:
            token = ""
    if not token:
        sys.exit("No GitHub token: set GITHUB_TOKEN or log in with `gh auth login`.")
    return token


def request(url: str, token: str, body: dict | None = None, optional: bool = False) -> dict | None:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-readme-cards",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        if optional and err.code in (403, 404):
            return None
        sys.exit(f"GitHub API HTTP {err.code} on {url}: {err.read()[:300]!r}")


def summarise(days: list[dict]) -> dict:
    """Derive streaks, monthly totals and busiest day from the calendar."""
    days = sorted(days, key=lambda d: d["date"])
    today = date.today().isoformat()
    days = [d for d in days if d["date"] <= today]

    monthly: "OrderedDict[str, int]" = OrderedDict()
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    months = [{"month": k, "count": v} for k, v in list(monthly.items())[-12:]]

    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    # Current streak: today may still be empty, so start from yesterday if so.
    current = 0
    tail = list(reversed(days))
    if tail and tail[0]["count"] == 0:
        tail = tail[1:]
    for d in tail:
        if d["count"] == 0:
            break
        current += 1

    busiest = max(days, key=lambda d: d["count"]) if days else {"date": today, "count": 0}
    return {
        "months": months,
        "current_streak": current,
        "longest_streak": longest,
        "active_days": sum(1 for d in days if d["count"] > 0),
        "busiest_day": busiest,
    }


def main() -> None:
    token = get_token()
    gql = request("https://api.github.com/graphql", token, {"query": QUERY, "variables": {"login": USER}})
    if "errors" in gql:
        sys.exit(f"GraphQL errors: {gql['errors']}")
    user = gql["data"]["user"]
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [
        {"date": d["date"], "count": d["contributionCount"], "weekday": d["weekday"]}
        for w in cal["weeks"]
        for d in w["contributionDays"]
    ]

    repos = []
    for name in PROFILE["featured_repos"]:
        r = request(f"https://api.github.com/repos/{USER}/{name}", token, optional=True)
        if r is None or r.get("private"):
            print(f"::warning::skipping featured repo {name}: private or not found")
            continue
        repos.append({
            "name": r["name"],
            "description": r.get("description") or "",
            "language": r.get("language") or "",
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
            "url": r["html_url"],
        })

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "username": USER,
        "total": cal["totalContributions"],
        "public_repos": user["repositories"]["totalCount"],
        "days": days,
        **summarise(days),
        "repos": repos,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    private = user["contributionsCollection"]["restrictedContributionsCount"]
    print(f"wrote {OUT.relative_to(ROOT)}: {out['total']} contributions "
          f"({private} private visible to this token), "
          f"streak {out['current_streak']}, {len(repos)} repos")


if __name__ == "__main__":
    main()
