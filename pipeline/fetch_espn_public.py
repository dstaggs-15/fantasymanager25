#!/usr/bin/env python3
"""
Fetch ESPN Fantasy Football league data for a PUBLIC league (no cookies).
Writes JSON files under docs/data/ for the frontend to read.

Views fetched:
- mTeam       → team metadata
- mRoster     → roster info by team
- mStandings  → standings
- mSettings   → league & scoring rules
- mMatchup    → current period (and per-week snapshots 1..18)

Outputs:
- docs/data/espn_mTeam.json
- docs/data/espn_mRoster.json
- docs/data/espn_mStandings.json
- docs/data/espn_mSettings.json
- docs/data/espn_mMatchup.json           (current scoring period)
- docs/data/espn_mMatchup_week_#.json    (per-week snapshots)
- docs/data/espn_manifest.json           (what was generated)
- docs/data/status.json                  (timestamp + note)
"""

from __future__ import annotations
import os, json, pathlib, datetime, time
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
DATA.mkdir(parents=True, exist_ok=True)

def utcnow() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def write_json(path: pathlib.Path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def write_status(note: str, season: str, week: str | None):
    write_json(DATA / "status.json", {
        "generated_utc": utcnow(),
        "season": season,
        "week": week,
        "notes": note
    })

def fetch_view(base_url: str, view: str, params: dict | None = None) -> dict:
    """GET a single ESPN 'view' JSON with optional params."""
    p = {"view": view}
    if params:
        p.update(params)
    r = requests.get(base_url, params=p, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    league_id = os.getenv("LEAGUE_ID")
    season = os.getenv("SEASON", "2025")
    # optional: allow WEEK override; used only for status banner
    week = os.getenv("WEEK")

    if not league_id:
        # Create minimal files so the site doesn't break
        write_status("LEAGUE_ID missing; nothing fetched", season, week)
        write_json(DATA / "espn_manifest.json", {"error": "LEAGUE_ID missing"})
        return

    base = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"

    manifest = {
        "league_id": league_id,
        "season": season,
        "generated_utc": utcnow(),
        "files": [],
        "errors": []
    }

    # Core views (single-shot)
    core_views = ["mTeam", "mRoster", "mStandings", "mSettings", "mMatchup"]
    for v in core_views:
        try:
            data = fetch_view(base, v)
            out = DATA / f"espn_{v}.json"
            write_json(out, data)
            manifest["files"].append(out.name)
            # be nice to ESPN's servers
            time.sleep(0.7)
        except Exception as e:
            manifest["errors"].append({v: f"{type(e).__name__}: {e}"})

    # Per-week matchup snapshots (Weeks 1..18; adjust if your league uses fewer)
    # We also write a small index of which weeks succeeded.
    weekly_ok = []
    for sp in range(1, 19):
        try:
            data = fetch_view(base, "mMatchup", params={"scoringPeriodId": sp})
            out = DATA / f"espn_mMatchup_week_{sp}.json"
            write_json(out, data)
            manifest["files"].append(out.name)
            weekly_ok.append(sp)
            time.sleep(0.5)
        except Exception as e:
            # Don't fail the run if a week isn't available pre-season
            manifest["errors"].append({f"mMatchup_week_{sp}": f"{type(e).__name__}: {e}"})

    manifest["weekly_matchup_weeks"] = weekly_ok
    write_json(DATA / "espn_manifest.json", manifest)

    # Update status banner
    note = "ESPN fetch OK"
    if manifest["errors"]:
        note = f"ESPN fetch partial: {len(manifest['errors'])} error(s)"
    write_status(note, season, week)

    print("✅ ESPN public fetch complete")
    print(f"   Files: {len(manifest['files'])}, Errors: {len(manifest['errors'])}")

if __name__ == "__main__":
    main()
