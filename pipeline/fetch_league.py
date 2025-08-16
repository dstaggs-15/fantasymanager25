# pipeline/fetch_league.py
"""
Fetch league teams + rosters from ESPN and emit:
  - docs/data/espn_mTeam.json
  - docs/data/espn_mRoster.json
  - docs/data/team_rosters.json   (normalized for the Teams page)

Env needed on runner:
  LEAGUE_ID   (defaults to 508419792)
  SEASON      (defaults to 2025)
  SWID        e.g. {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
  ESPN_S2     long cookie string

Exit 0 on success; nonzero on failure (but still writes error JSONs).
"""

from __future__ import annotations
import os, sys, json, time
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests

LEAGUE_ID = os.getenv("LEAGUE_ID", "508419792")
SEASON = int(os.getenv("SEASON", "2025"))
OUT_DIR = "docs/data"

TEAM_RAW = f"{OUT_DIR}/espn_mTeam.json"
ROSTER_RAW = f"{OUT_DIR}/espn_mRoster.json"
COMBINED = f"{OUT_DIR}/team_rosters.json"

BASE = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def ensure_out():
    os.makedirs(OUT_DIR, exist_ok=True)

def write(path: str, obj: Any):
    ensure_out()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))

def require(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env: {name}")
    return v

def make_session() -> requests.Session:
    swid = require("SWID")
    s2   = require("ESPN_S2")
    s = requests.Session()
    s.cookies.set("SWID", swid, domain=".espn.com", secure=True)
    s.cookies.set("espn_s2", s2,  domain=".espn.com", secure=True)
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://fantasy.espn.com",
        "Referer": f"https://fantasy.espn.com/football/league?leagueId={LEAGUE_ID}&seasonId={SEASON}",
    })
    return s

def get_json(session: requests.Session, view: str) -> Dict[str, Any]:
    r = session.get(BASE, params={"view": view, "forTeamId": 1}, timeout=30)
    ctype = r.headers.get("content-type", "")
    if "application/json" not in ctype:
        raise RuntimeError(f"{view} Non-JSON (content-type={ctype})")
    return r.json()

POS_MAP = {
    0: "Quarterback",
    2: "Running back",
    4: "Wide receiver",
    6: "Tight end",
    16: "Team defense / special teams",
    17: "Kicker",
}

NFL = {
    1:"ATL",2:"BUF",3:"CHI",4:"CIN",5:"CLE",6:"DAL",7:"DEN",8:"DET",9:"GB",
    10:"TEN",11:"IND",12:"KC",13:"OAK",14:"LAR",15:"MIA",16:"MIN",17:"NE",
    18:"NO",19:"NYG",20:"NYJ",21:"PHI",22:"ARI",23:"PIT",24:"LAC",25:"SF",
    26:"SEA",27:"TB",28:"WSH",29:"CAR",30:"JAX",33:"BAL",34:"HOU",35:"NO TEAM"
}

def normalize_teams(team_payload: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    teams = {}
    for t in team_payload.get("teams", []):
        teams[t["id"]] = {
            "teamId": t["id"],
            "name": t.get("name") or f"Team {t['id']}",
            "abbrev": t.get("abbrev"),
            "logo": t.get("logo"),
            "owners": t.get("owners", []),
            "players": [],  # fill from roster view
        }
    return teams

def normalize_roster(roster_payload: Dict[str, Any], teams: Dict[int, Dict[str, Any]]):
    # mRoster contains a "teams" array; each team has "roster" with "entries"
    for t in roster_payload.get("teams", []):
        tid = t.get("id")
        team_rec = teams.get(tid)
        if not team_rec:
            continue
        players = []
        roster = (t.get("roster") or {}).get("entries") or []
        for e in roster:
            p = (e.get("playerPoolEntry") or {}).get("player") or {}
            name = p.get("fullName") or f"{p.get('firstName','')} {p.get('lastName','')}".strip()
            posId = p.get("defaultPositionId")
            proId = p.get("proTeamId")
            players.append({
                "id": p.get("id"),
                "name": name,
                "positionId": posId,
                "position": POS_MAP.get(posId, str(posId) if posId is not None else None),
                "proTeamId": proId,
                "team": NFL.get(proId, str(proId) if proId is not None else None),
            })
        team_rec["players"] = players

def main() -> int:
    ensure_out()
    try:
        s = make_session()

        # 1) Teams
        teams_raw = get_json(s, "mTeam")
        write(TEAM_RAW, {"fetched_at": utc_now(), "data": teams_raw})

        # 2) Rosters
        rosters_raw = get_json(s, "mRoster")
        write(ROSTER_RAW, {"fetched_at": utc_now(), "data": rosters_raw})

        # 3) Normalize
        teams = normalize_teams(teams_raw)
        normalize_roster(rosters_raw, teams)

        final = {
            "league_id": LEAGUE_ID,
            "season": SEASON,
            "generated_utc": utc_now(),
            "teams": list(teams.values()),
        }
        write(COMBINED, final)

        print(f"team_rosters: {len(final['teams'])} teams written")
        return 0

    except Exception as e:
        # Write error stubs so the UI shows a message instead of dying
        err = {"fetched_at": utc_now(), "error": f"{type(e).__name__}: {e}"}
        try:
            write(TEAM_RAW, err)
            write(ROSTER_RAW, err)
            write(COMBINED, {"generated_utc": utc_now(), "teams": [], "error": err["error"]})
        except Exception:
            pass
        print(f"fetch_league ERROR: {err['error']}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
