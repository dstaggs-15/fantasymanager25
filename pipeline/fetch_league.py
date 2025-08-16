#!/usr/bin/env python3
"""
Fetch league-wide data from ESPN (mTeam + mRoster) using SWID/ESPN_S2 cookies
and generate the site-ready JSON under docs/data/.

Requires env:
  LEAGUE_ID   (e.g. 508419792)
  SEASON      (e.g. 2025)
  SWID        (keep the {} braces)
  ESPN_S2     (your long token)

Outputs (all UTC timestamps):
  docs/data/espn_mTeam.json          # raw ESPN league (mTeam)
  docs/data/espn_mRoster.json        # raw ESPN league (mRoster)
  docs/data/team_rosters.json        # {generated_utc, teams:[{id,name,logo,owners,roster_count,players:[...] }]}
  docs/data/players_summary.json     # {generated_utc, count, rows:[{id, name, pos, proTeam, teamId, team}]}
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
})

def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def env_required(key: str) -> str:
    val = os.environ.get(key, "").strip()
    if not val:
        print(f"Missing required env: {key}", file=sys.stderr)
        sys.exit(1)
    return val

def league_url(season: int, league_id: int, params: Dict[str, Any]) -> str:
    base = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"
    if params:
        # requests will add params; building string here only for logs
        return base
    return base

def req_json(url: str, params: Dict[str, Any], cookies: Dict[str, str]) -> Dict[str, Any]:
    r = SESSION.get(url, params=params, cookies=cookies, timeout=30)
    ctype = r.headers.get("content-type", "")
    if "application/json" not in ctype:
        raise RuntimeError(f"Non-JSON (content-type={ctype})")
    return r.json()

def safe_write(path: str, data: Any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_view(season: int, league_id: int, view: str, cookies: Dict[str, str], *,
               scoring_period_id: int | None = None,
               tries: int = 4, sleep_secs: float = 1.5) -> Dict[str, Any]:
    url = league_url(season, league_id, {})
    params = {"view": view}
    if scoring_period_id is not None:
        params["scoringPeriodId"] = scoring_period_id

    last_err = None
    for attempt in range(1, tries + 1):
        try:
            return req_json(url, params, cookies)
        except Exception as e:
            last_err = e
            time.sleep(sleep_secs)
    raise RuntimeError(f"{view} failed after {tries} tries: {last_err}")

def flatten_players_from_roster(mroster: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    mRoster -> rows of players with minimal fields used by Players page.
    """
    rows: List[Dict[str, Any]] = []
    teams = mroster.get("teams", [])
    # player metadata sometimes sits under mRoster["players"] too, but teams[*].roster.entries is reliable
    for t in teams:
        team_id = t.get("id")
        team_name = t.get("name") or f"Team {team_id}"
        roster = (t.get("roster") or {}).get("entries", [])
        for entry in roster:
            p = (entry.get("playerPoolEntry") or {}).get("player", {})
            pid = p.get("id")
            full = p.get("fullName") or p.get("name") or "Unknown"
            default_pos = (p.get("defaultPositionId") or "")
            pro_team_id = p.get("proTeamId")
            # position mapping (basic)
            pos_map = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "D/ST"}
            pos = pos_map.get(default_pos, str(default_pos))

            rows.append({
                "id": pid,
                "name": full,
                "pos": pos,
                "proTeam": pro_team_id,
                "teamId": team_id,
                "team": team_name,
            })
    return rows

def build_team_rosters(mteam: Dict[str, Any], mroster: Dict[str, Any]) -> Dict[str, Any]:
    team_index: Dict[int, Dict[str, Any]] = {}
    for t in mteam.get("teams", []):
        tid = t.get("id")
        team_index[tid] = {
            "id": tid,
            "name": t.get("name"),
            "logo": t.get("logo"),
            "owners": t.get("owners", []),
            "roster_count": 0,
            "players": [],  # we’ll fill from mRoster if available
        }

    for t in mroster.get("teams", []):
        tid = t.get("id")
        target = team_index.get(tid)
        if not target:
            # create if not seen in mTeam (edge-case)
            target = {
                "id": tid,
                "name": t.get("name"),
                "logo": t.get("logo"),
                "owners": t.get("owners", []),
                "roster_count": 0,
                "players": [],
            }
            team_index[tid] = target

        entries = (t.get("roster") or {}).get("entries", []) or []
        target["roster_count"] = len(entries)
        for e in entries:
            p = (e.get("playerPoolEntry") or {}).get("player", {})
            target["players"].append({
                "id": p.get("id"),
                "name": p.get("fullName") or p.get("name"),
                "posId": p.get("defaultPositionId"),
                "proTeamId": p.get("proTeamId"),
            })

    teams_sorted = sorted(team_index.values(), key=lambda x: x["id"] or 0)
    return {
        "generated_utc": utcnow_iso(),
        "teams": teams_sorted,
    }

def main() -> int:
    league_id = int(env_required("LEAGUE_ID"))
    season = int(os.environ.get("SEASON", "2025").strip() or "2025")
    swid = env_required("SWID")
    s2 = env_required("ESPN_S2")

    cookies = {"SWID": swid, "espn_s2": s2}

    # 1) fetch raw views
    mteam = fetch_view(season, league_id, "mTeam", cookies)
    # preseason / pre-week rosters are under scoringPeriodId 0; once the season starts, current week works too
    mroster = fetch_view(season, league_id, "mRoster", cookies, scoring_period_id=0)

    # 2) write raw dumps (handy for debugging)
    raw_out_dir = "docs/data"
    safe_write(f"{raw_out_dir}/espn_mTeam.json", {"fetched_at": utcnow_iso(), "data": mteam})
    safe_write(f"{raw_out_dir}/espn_mRoster.json", {"fetched_at": utcnow_iso(), "data": mroster})

    # 3) build team_rosters.json (feeds Teams page)
    team_rosters = build_team_rosters(mteam, mroster)
    safe_write(f"{raw_out_dir}/team_rosters.json", team_rosters)

    # 4) build players_summary.json (feeds Players page)
    rows = flatten_players_from_roster(mroster)
    players_summary = {
        "generated_utc": utcnow_iso(),
        "count": len(rows),
        "rows": rows,
        "source": "espn mRoster",
    }
    safe_write(f"{raw_out_dir}/players_summary.json", players_summary)

    print(f"Wrote {len(team_rosters['teams'])} teams; {players_summary['count']} players.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        # If we ever regress, emit a small error file so the site shows why it’s empty
        safe_write("docs/data/fetch_league_error.json", {
            "generated_utc": utcnow_iso(),
            "error": repr(e)
        })
        print(f"fetch_league ERROR: {e}", file=sys.stderr)
        sys.exit(2)
