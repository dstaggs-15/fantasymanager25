#!/usr/bin/env python3
"""
Fetch league teams (mTeam) and team rosters (mRoster) from ESPN's private API,
then write:
  - docs/data/team_rosters.json
  - docs/data/players_summary.json

Relies on SWID and ESPN_S2 being provided via GitHub Actions secrets or runner env.
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

import requests

LEAGUE_ID = os.getenv("LEAGUE_ID", "508419792")
SEASON = os.getenv("SEASON", "2025")

OUT_ROSTERS = "docs/data/team_rosters.json"
OUT_PLAYERS = "docs/data/players_summary.json"
STATUS_FILE = "docs/data/status.json"  # optional: append a note

BASE = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"

def get_cookies() -> Dict[str, str]:
    swid = os.getenv("SWID") or os.getenv("ESPN_SWID")
    s2 = os.getenv("ESPN_S2") or os.getenv("ESPN_S2_TOKEN") or os.getenv("ESPN_S2")
    if not swid or not s2:
        raise RuntimeError("Missing SWID / ESPN_S2 in env.")
    return {"SWID": swid, "espn_s2": s2}

def req(url: str, cookies: Dict[str, str], params: Dict[str, Any]) -> Any:
    # Be nice to ESPN; minimal headers + retries
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://fantasy.espn.com/",
    }
    last_err = None
    for attempt in range(1, 6):
        r = requests.get(url, headers=headers, cookies=cookies, params=params, timeout=20)
        ctype = r.headers.get("content-type", "")
        if r.ok and "application/json" in ctype.lower():
            try:
                return r.json()
            except Exception as e:
                last_err = e
        else:
            last_err = RuntimeError(f"Non-JSON (content-type={ctype}) status={r.status_code}")
        time.sleep(1.2 * attempt)  # backoff
    raise RuntimeError(f"GET {url} failed after retries: {last_err}")

def fetch_teams(cookies: Dict[str, str]) -> Tuple[List[Dict[str, Any]], Dict[int, Dict[str, Any]]]:
    data = req(BASE, cookies, params={"view": "mTeam"})
    teams = data.get("teams", [])
    by_id = {t["id"]: t for t in teams}
    return teams, by_id

def fetch_team_roster(team_id: int, cookies: Dict[str, str]) -> Dict[str, Any]:
    # Query just this team’s roster
    data = req(BASE, cookies, params={"view": "mRoster", "teamId": team_id})
    # Response still returns a league object, but only the requested team in "teams"
    teams = data.get("teams", [])
    if not teams:
        return {"teamId": team_id, "entries": []}
    team = teams[0]
    roster = team.get("roster", {}) or {}
    entries = roster.get("entries", []) or []
    return {"teamId": team_id, "entries": entries}

def flatten_player(entry: Dict[str, Any], team_meta: Dict[str, Any]) -> Dict[str, Any]:
    # entry.playerPoolEntry.player with lots of metadata
    ppe = entry.get("playerPoolEntry", {}) or {}
    player = ppe.get("player", {}) or {}
    full_name = player.get("fullName") or player.get("name") or "Unknown"
    pro_team = player.get("proTeamId")
    default_pos = None
    if player.get("defaultPositionId") is not None:
        default_pos = player["defaultPositionId"]  # numeric
    # Slots / lineup position (optional)
    lineup_slot_id = entry.get("lineupSlotId")

    # Map ESPN defaultPositionId to common strings (QB/RB/WR/TE/K/DST)
    POS_MAP = {0:"QB",2:"RB",4:"WR",6:"TE",16:"D/ST",17:"K",23:"FLEX"}
    pos = POS_MAP.get(default_pos, str(default_pos) if default_pos is not None else "")

    return {
        "id": player.get("id"),
        "name": full_name,
        "pos": pos,
        "proTeamId": pro_team,
        "teamId": team_meta.get("id"),
        "team": team_meta.get("abbrev") or team_meta.get("location") or "",
        "lineupSlotId": lineup_slot_id,
        "source": "espn:mRoster",
    }

def main() -> int:
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cookies = get_cookies()

    # 1) mTeam to discover teams
    teams, by_id = fetch_teams(cookies)
    if not teams:
        raise RuntimeError("No teams returned by mTeam")

    # 2) per-team mRoster
    combined = {
        "generated_utc": ts,
        "leagueId": LEAGUE_ID,
        "season": SEASON,
        "teams": [],
    }
    flat_players: List[Dict[str, Any]] = []

    for t in teams:
        tid = t["id"]
        try:
            r = fetch_team_roster(tid, cookies)
            entries = r.get("entries", [])
        except Exception as e:
            entries = []
            print(f"[warn] roster fetch failed for team {tid}: {e}", file=sys.stderr)

        # keep a compact team block for team_rosters.json
        team_block = {
            "teamId": tid,
            "abbrev": t.get("abbrev"),
            "name": t.get("name"),
            "count": len(entries),
            "players": [],
        }

        for e in entries:
            flat = flatten_player(e, t)
            team_block["players"].append(flat)
            flat_players.append(flat)

        combined["teams"].append(team_block)

    # 3) Write team_rosters.json
    os.makedirs(os.path.dirname(OUT_ROSTERS), exist_ok=True)
    with open(OUT_ROSTERS, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    # 4) Write players_summary.json (flat)
    players_out = {
        "generated_utc": ts,
        "count": len(flat_players),
        "rows": flat_players,
    }
    with open(OUT_PLAYERS, "w", encoding="utf-8") as f:
        json.dump(players_out, f, ensure_ascii=False, indent=2)

    # Optional: touch status.json to show success
    try:
        status = {}
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                status = json.load(f)
        status.setdefault("notes", [])
        status["notes"].append(f"{ts} wrote team_rosters.json ({len(combined['teams'])} teams) and players_summary.json ({len(flat_players)} players)")
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
    except Exception as _:
        pass

    print(f"Wrote {OUT_ROSTERS} and {OUT_PLAYERS} — teams={len(combined['teams'])}, players={len(flat_players)}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        # If something fails, write empty-but-informative files so the UI shows a message
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        os.makedirs("docs/data", exist_ok=True)
        with open(OUT_ROSTERS, "w", encoding="utf-8") as f:
            json.dump({"generated_utc": ts, "teams": [], "error": str(e)}, f, indent=2)
        with open(OUT_PLAYERS, "w", encoding="utf-8") as f:
            json.dump({"generated_utc": ts, "count": 0, "rows": [], "error": str(e)}, f, indent=2)
        print(f"fetch_rosters ERROR: {e}", file=sys.stderr)
        sys.exit(2)
