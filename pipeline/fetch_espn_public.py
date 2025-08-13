#!/usr/bin/env python3
"""
Fetch ESPN Fantasy Football league data for a PUBLIC league.
Adds browser-like headers to avoid 403 from ESPN anti-bot, and
optionally retries with cookies (SWID/espn_s2) if provided as secrets.

Outputs under docs/data/:
  - espn_mTeam.json
  - espn_mRoster.json
  - espn_mStandings.json
  - espn_mSettings.json
  - espn_mMatchup.json
  - espn_mMatchup_week_#.json (1..18 best-effort)
  - espn_manifest.json
  - status.json
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

def make_headers(league_id: str) -> dict:
    # Pretend to be a normal browser hitting the league page
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://fantasy.espn.com/football/league?leagueId={league_id}",
        "Origin": "https://fantasy.espn.com",
        # These headers aren’t strictly required, but sometimes help:
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

def get_cookies_from_env() -> dict | None:
    swid = os.getenv("ESPN_SWID")
    s2 = os.getenv("ESPN_S2")
    if swid and s2:
        return {"SWID": swid, "espn_s2": s2}
    return None

def fetch_view(session: requests.Session, base_url: str, view: str, params: dict | None = None) -> dict:
    p = {"view": view}
    if params:
        p.update(params)
    r = session.get(base_url, params=p, timeout=30, allow_redirects=True)
    r.raise_for_status()
    return r.json()

def attempt_fetch(league_id: str, season: str, cookies: dict | None = None):
    base = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"

    session = requests.Session()
    session.headers.update(make_headers(league_id))
    if cookies:
        session.cookies.update(cookies)

    manifest = {
        "league_id": league_id,
        "season": season,
        "generated_utc": utcnow(),
        "files": [],
        "errors": [],
        "used_cookies": bool(cookies),
    }

    # Core views
    core_views = ["mTeam", "mRoster", "mStandings", "mSettings", "mMatchup"]
    for v in core_views:
        try:
            data = fetch_view(session, base, v)
            out = DATA / f"espn_{v}.json"
            write_json(out, data)
            manifest["files"].append(out.name)
            time.sleep(0.5)
        except Exception as e:
            manifest["errors"].append({v: f"{type(e).__name__}: {e}"})

    # Per-week matchups (best effort — some weeks may not exist yet)
    weekly_ok = []
    for sp in range(1, 19):
        try:
            data = fetch_view(session, base, "mMatchup", params={"scoringPeriodId": sp})
            out = DATA / f"espn_mMatchup_week_{sp}.json"
            write_json(out, data)
            manifest["files"].append(out.name)
            weekly_ok.append(sp)
            time.sleep(0.35)
        except Exception as e:
            manifest["errors"].append({f"mMatchup_week_{sp}": f"{type(e).__name__}: {e}"})

    manifest["weekly_matchup_weeks"] = weekly_ok
    return manifest

def main():
    league_id = os.getenv("LEAGUE_ID")
    season = os.getenv("SEASON", "2025")
    week = os.getenv("WEEK")

    if not league_id:
        write_status("LEAGUE_ID missing; nothing fetched", season, week)
        write_json(DATA / "espn_manifest.json", {"error": "LEAGUE_ID missing"})
        return

    # 1) Try without cookies (public path)
    manifest = attempt_fetch(league_id, season, cookies=None)

    # 2) If we got blanket 403s, retry ONCE with cookies if provided as secrets
    all_403 = manifest["files"] == [] and any("403" in list(err.values())[0] for err in manifest["errors"])
    if all_403:
        cookies = get_cookies_from_env()
        if cookies:
            manifest = attempt_fetch(league_id, season, cookies=cookies)

    # Write outputs
    write_json(DATA / "espn_manifest.json", manifest)
    note = "ESPN fetch OK" if not manifest["errors"] else f"ESPN fetch partial: {len(manifest['errors'])} error(s)"
    if manifest["files"] == []:
        note = "ESPN fetch failed: no files written"
    write_status(note, season, week)

    print("✅ ESPN fetch finished")
    print(f"   Used cookies: {manifest['used_cookies']}")
    print(f"   Files: {len(manifest['files'])}, Errors: {len(manifest['errors'])}")

if __name__ == "__main__":
    main()
