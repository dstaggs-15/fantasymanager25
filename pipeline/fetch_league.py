# pipeline/fetch_league.py
"""
Fetch league teams + rosters from ESPN and emit:
  - docs/data/espn_mTeam.json
  - docs/data/espn_mRoster.json
  - docs/data/team_rosters.json   (normalized for the Teams page)

Env needed on runner:
  LEAGUE_ID   (defaults to 508419792)
  SEASON      (defaults to 2025)
  SWID        {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
  ESPN_S2     long cookie string

This version adds:
  • Cloudflare-hardened requests (retries, alt query shapes, jitter)
  • Graceful error files if ESPN serves HTML repeatedly
"""

from __future__ import annotations
import os, sys, json, time, random
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

# ---------- utils ----------

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
    # cookies on .espn.com so subdomains pick it up
    s.cookies.set("SWID", swid, domain=".espn.com", secure=True)
    s.cookies.set("espn_s2", s2,  domain=".espn.com", secure=True)
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Origin": "https://fantasy.espn.com",
        "Referer": f"https://fantasy.espn.com/football/league?leagueId={LEAGUE_ID}&seasonId={SEASON}",
    })
    return s

def get_json_hardened(session: requests.Session, view: str) -> Dict[str, Any]:
    """
    Try multiple request shapes + retry backoff to dodge HTML challenge.
    """
    attempts = []
    # shapes: with forTeamId=1 (what the app often uses), without, and with an extra benign param
    query_shapes = [
        {"view": view, "forTeamId": 1},
        {"view": view},
        {"view": view, "scoringPeriodId": 0},
    ]

    for shape in query_shapes:
        for attempt in range(1, 5):  # up to 4 tries per shape
            try:
                r = session.get(BASE, params=shape, timeout=30)
                ctype = r.headers.get("content-type", "")
                if "application/json" not in ctype:
                    raise RuntimeError(f"{view} Non-JSON (content-type={ctype})")
                return r.json()
            except Exception as e:
                attempts.append(f"{view} shape={shape} try={attempt}: {type(e).__name__}: {e}")
                # jittered backoff
                time.sleep(0.7 + random.random() * 0.8)
        # brief pause before trying the next shape
        time.sleep(0.8 + random.random() * 0.6)

    raise RuntimeError("; ".join(attempts[-6:]))  # include details from the last few tries

# ---------- normalize ----------

def normalize_teams(team_payload: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    teams: Dict[int, Dict[str, Any]] = {}
    for t in team_payload.get("teams", []) or []:
        teams[t["id"]] = {
            "teamId": t["id"],
            "name": t.get("name") or f"Team {t['id']}",
            "abbrev": t.get("abbrev"),
            "logo": t.get("logo"),
            "owners": t.get("owners", []),
            "players": [],  # filled from roster
        }
    return teams

def normalize_roster(roster_payload: Dict[str, Any], teams: Dict[int, Dict[str, Any]]):
    for t in roster_payload.get("teams", []) or []:
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

# ---------- main ----------

def main() -> int:
    ensure_out()
    try:
        s = make_session()

        # 1) Teams (mTeam) with hardened fetch
        teams_raw = get_json_hardened(s, "mTeam")
        write(TEAM_RAW, {"fetched_at": utc_now(), "data": teams_raw})

        # 2) Rosters (mRoster) with hardened fetch
        rosters_raw = get_json_hardened(s, "mRoster")
        write(ROSTER_RAW, {"fetched_at": utc_now(), "data": rosters_raw})

        # 3) Normalize for Teams page
        teams_map = normalize_teams(teams_raw)
        normalize_roster(rosters_raw, teams_map)

        final = {
            "league_id": LEAGUE_ID,
            "season": SEASON,
            "generated_utc": utc_now(),
            "teams": list(teams_map.values()),
        }
        write(COMBINED, final)

        print(f"team_rosters: {len(final['teams'])} teams written")
        return 0

    except Exception as e:
        # Always leave breadcrumbs the UI can read
        msg = f"{type(e).__name__}: {e}"
        err = {"fetched_at": utc_now(), "error": msg}
        try:
            write(TEAM_RAW, err)
            write(ROSTER_RAW, err)
            write(COMBINED, {"generated_utc": utc_now(), "teams": [], "error": msg})
        except Exception:
            pass
        print(f"fetch_league ERROR: {msg}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
