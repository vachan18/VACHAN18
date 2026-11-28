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

PR_QUERY = """
query($q: String!, $cursor: String) {
  search(query: $q, type: ISSUE, first: 100, after: $cursor) {
    issueCount
    pageInfo { hasNextPage endCursor }
    nodes { ... on PullRequest { repository { name isPrivate owner { login } } } }
  }
}
"""

COUNT_QUERY = """
query($q: String!) { search(query: $q, type: ISSUE, first: 1) { issueCount } }
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


def _gql(token: str, query: str, variables: dict) -> dict:
    res = request("https://api.github.com/graphql", token, {"query": query, "variables": variables},
                  optional=True)
    if not res or "errors" in res:
        raise RuntimeError(res.get("errors") if res else "no response")
    return res["data"]


def summarise_prs(nodes: list[dict], merged: int, opened: int) -> dict:
    """Aggregate merged PRs per repo. Private repo names never leave this function."""
    per_repo: dict[tuple[str, str], dict] = {}
    for n in nodes:
        repo = (n or {}).get("repository")
        if not repo:
            continue
        key = (repo["owner"]["login"], repo["name"])
        entry = per_repo.setdefault(key, {"private": repo["isPrivate"], "count": 0})
        entry["count"] += 1
    external = {k: v for k, v in per_repo.items()
                if k[0].lower() != USER.lower() and not v["private"]}
    public = sorted(((k, v) for k, v in per_repo.items() if not v["private"]),
                    key=lambda kv: -kv[1]["count"])
    return {
        "opened": opened,
        "merged": merged,
        "repos": len(per_repo),
        "top_public": [{"name": k[1] if k[0].lower() == USER.lower() else f"{k[0]}/{k[1]}",
                        "count": v["count"]} for k, v in public[:5]],
        "external_merged": sum(v["count"] for v in external.values()),
        "external_repos": len(external),
        "external_orgs": len({k[0].lower() for k in external}),
    }


def fetch_prs(token: str) -> dict:
    """Merged/opened PR stats. On failure, keep the last known numbers so the card never drops to 0."""
    try:
        q = f"is:pr author:{USER} is:merged"
        nodes, cursor, merged = [], None, 0
        while True:
            s = _gql(token, PR_QUERY, {"q": q, "cursor": cursor})["search"]
            merged = s["issueCount"]
            nodes += s["nodes"]
            if not s["pageInfo"]["hasNextPage"]:
                break
            cursor = s["pageInfo"]["endCursor"]
        opened = _gql(token, COUNT_QUERY, {"q": f"is:pr author:{USER}"})["search"]["issueCount"]
        return summarise_prs(nodes, merged, opened)
    except Exception as err:  # noqa: BLE001 - any failure falls back to cached data
        print(f"::warning::PR stats unavailable ({err}); keeping previous values")
        try:
            return json.loads(OUT.read_text(encoding="utf-8")).get("prs") or {}
        except Exception:
            return {}


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
        "prs": fetch_prs(token),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    private = user["contributionsCollection"]["restrictedContributionsCount"]
    print(f"wrote {OUT.relative_to(ROOT)}: {out['total']} contributions "
          f"({private} private visible to this token), "
          f"streak {out['current_streak']}, {len(repos)} repos, "
          f"{out['prs'].get('merged', '?')} PRs merged "
          f"({out['prs'].get('external_merged', '?')} open-source)")


if __name__ == "__main__":
    main()
