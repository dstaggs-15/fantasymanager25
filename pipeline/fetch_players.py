#!/usr/bin/env python3
"""
Fetch ESPN players pages (requires SWID & ESPN_S2 env) and build players_summary.json
Outputs to docs/data.
"""
import os
import time
import json
from datetime import datetime, timezone
from pathlib import Path
import requests
from urllib.parse import urlencode

DATA_DIR = Path("docs/data")
BASE = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/players"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

def cookies_from_env():
    swid = os.environ.get("SWID")
    s2 = os.environ.get("ESPN_S2")
    if not swid or not s2:
        raise RuntimeError("Missing SWID/ESPN_S2 env")
    return {"SWID": swid, "espn_s2": s2}

def fetch_page(season: int, offset: int, cookies):
    # ESPN players endpoint supports paging via "offset" and "limit"
    params = {
        "scoringPeriodId": 0,
        "view": "players_wl",
        "sortPercOwned": "true",
        "limit": 200,
        "offset": offset
    }
    url = BASE.format(season=season) + "?" + urlencode(params)
    r = requests.get(url, headers=HEADERS, cookies=cookies, timeout=20)
    ctype = r.headers.get("content-type", "")
    if "application/json" not in ctype:
        raise RuntimeError(f"Non-JSON (content-type={ctype})")
    return r.json()

def simplify(players):
    rows = []
    for p in players:
        # schema sometimes nests differently by season; guard with .get
        info = p
        full = info.get("fullName") or info.get("name") or "Unknown"
        pro_team = info.get("proTeam", info.get("proTeamId"))
        pos = info.get("defaultPositionId")
        # ownership & projections are optional
        own = (info.get("ownership") or {}).get("percentOwned")
        proj = (info.get("appliedStatTotal")) or (info.get("projectedTotal", None))
        rows.append({
            "id": info.get("id"),
            "name": full,
            "pos": pos,
            "proTeam": pro_team,
            "owned_pct": own,
            "proj_season": proj
        })
    return rows

def main():
    season = int(os.environ.get("SEASON", "2025"))
    cookies = cookies_from_env()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_players = []
    offset = 0
    while True:
        page = fetch_page(season, offset, cookies)
        if not isinstance(page, list) or not page:
            break
        all_players.extend(page)
        if len(page) < 200:
            break
        offset += 200
        time.sleep(0.6)  # be nice

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(all_players),
        "rows": simplify(all_players)
    }

    with (DATA_DIR / "players_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"Wrote {DATA_DIR / 'players_summary.json'} with {summary['count']} rows")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
