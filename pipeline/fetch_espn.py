#!/usr/bin/env python3
from __future__ import annotations
import json, os, datetime, pathlib, random

DATA = pathlib.Path(__file__).resolve().parents[1] / "docs" / "data"
DATA.mkdir(parents=True, exist_ok=True)

def utcnow() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def write_status(note: str):
    status = {
        "generated_utc": utcnow(),
        "season": os.getenv("SEASON") or None,
        "week": os.getenv("WEEK") or None,
        "notes": note,
    }
    (DATA / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")

def write_dummy(note: str):
    # keep the site alive even if ESPN fails
    teams = [
        {"team": "Duloc Gingerbread Men", "wins": 2, "losses": 1, "pointsFor": 296, "pointsAgainst": 274},
        {"team": "Far Far Away Knights", "wins": 2, "losses": 1, "pointsFor": 281, "pointsAgainst": 263},
        {"team": "Dragon’s Lair", "wins": 1, "losses": 2, "pointsFor": 248, "pointsAgainst": 303},
    ]
    # tiny jitter so commits change
    for t in teams:
        t["pointsFor"] += random.randint(0, 1)
        t["pointsAgainst"] += random.randint(0, 1)
    (DATA / "latest.json").write_text(json.dumps(teams, indent=2), encoding="utf-8")
    write_status(note)

def main():
    LEAGUE_ID = os.getenv("LEAGUE_ID")
    SEASON = int(os.getenv("SEASON", "2025"))
    SWID = os.getenv("ESPN_SWID")          # looks like "{ABCDEF12-...}"
    S2 = os.getenv("ESPN_S2")              # long cookie string

    if not (LEAGUE_ID and SWID and S2):
        write_dummy("ESPN secrets missing → serving dummy data")
        return

    try:
        # lazy import so we don’t pin the dependency when running dummy
        from espn_api.football import League
        league = League(league_id=int(LEAGUE_ID), year=SEASON, espn_s2=S2, swid=SWID)

        rows = []
        for t in league.teams:
            rows.append({
                "team": t.team_name,
                "wins": t.wins,
                "losses": t.losses,
                "pointsFor": round(t.points_for, 0),
                "pointsAgainst": round(t.points_against, 0),
            })

        # sort by wins desc, tie‑break by pointsFor desc
        rows.sort(key=lambda x: (x["wins"], x["pointsFor"]), reverse=True)

        (DATA / "latest.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        write_status("ESPN league sync OK")
    except Exception as e:
        # Never break the site — fall back
        write_dummy(f"ESPN fetch failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
