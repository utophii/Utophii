#!/usr/bin/env python3

import datetime as dt
import json
import os
import urllib.request
from pathlib import Path

USER = "utophii"
STATS = Path(__file__).parent / "stats.json"
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def api(url, data=None):
    req = urllib.request.Request(url, data=data)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    if data:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def graphql(query):
    return api("https://api.github.com/graphql",
               json.dumps({"query": query}).encode())


def main():
    today = dt.date.today()
    year_start = f"{today.year}-01-01T00:00:00Z"

    q = f"""
    query {{
      user(login: "{USER}") {{
        followers {{ totalCount }}
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false,
                     orderBy: {{field: STARGAZERS, direction: DESC}}) {{
          totalCount
          nodes {{
            name stargazerCount description
            primaryLanguage {{ name }}
          }}
        }}
        contributionsCollection(from: "{year_start}") {{
          totalCommitContributions
          contributionCalendar {{
            weeks {{ contributionDays {{ date contributionCount }} }}
          }}
        }}
      }}
    }}"""
    user = graphql(q)["data"]["user"]

    repos = user["repositories"]["nodes"]
    stars = sum(r["stargazerCount"] for r in repos)
    auto_projects = [
        {
            "name": r["name"],
            "stars": r["stargazerCount"],
            "desc": (r["description"] or "")[:90],
            "lang": (r["primaryLanguage"] or {}).get("name", ""),
        }
        for r in repos[:3]
    ]

    days = [
        d
        for w in user["contributionsCollection"]["contributionCalendar"]["weeks"]
        for d in w["contributionDays"]
        if d["date"] <= today.isoformat()
    ]
    days.sort(key=lambda d: d["date"])

    current = 0
    for d in reversed(days):
        if d["contributionCount"] > 0:
            current += 1
        elif d["date"] == today.isoformat():
            continue
        else:
            break
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    spark = [d["contributionCount"] for d in days[-14:]]

    last_active = next(
        (d["date"] for d in reversed(days) if d["contributionCount"] > 0), None)
    if last_active:
        gap = (today - dt.date.fromisoformat(last_active)).days
        if gap <= 2:
            activity = {"label": "active", "level": "on"}
        elif gap <= 14:
            activity = {"label": "around", "level": "mid"}
        else:
            activity = {"label": "away", "level": "off"}
    else:
        activity = {"label": "quiet", "level": "off"}

    stats = {
        "updated": today.isoformat(),
        "metrics": {
            "commits": user["contributionsCollection"]["totalCommitContributions"],
            "repos": user["repositories"]["totalCount"],
            "stars": stars,
            "followers": user["followers"]["totalCount"],
        },
        "streak": {"current": current, "longest": longest, "spark": spark},
        "auto_projects": auto_projects,
        "activity": activity,
    }
    STATS.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n",
                     encoding="utf-8")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
