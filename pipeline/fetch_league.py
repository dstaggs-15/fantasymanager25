# pipeline/fetch_league.py
"""
Fetch league teams + rosters and emit:
  - docs/data/espn_mTeam.json
  - docs/data/espn_mRoster.json
  - docs/data/team_rosters.json   (normalized for Teams page)

Hardening:
  • Tries read-only host first (lm-api-reads.fantasy.espn.com), then fantasy.espn.com
  • "Priming" GETs to public league page & static assets (mimic browser)
  • Optional CF clearance cookie (CF_CLEARANCE env) if you provide it
  • Retries with jitter and alternate query shapes
  • Falls back to last-good JSON if today’s fetch is blocked

Env (repo secrets or runner env):
  LEAGUE_ID   default '508419792'
  SEASON      default '2025'
  SWID        {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
  ESPN_S2     long cookie string
  CF_CLEARANCE  (optional) Cloudflare cookie from a real browser session

Exit 0 on success (or safe fallback), 2 on hard failure with error breadcrumbs.
"""

from __future__ import annotations
import os, sys, json, time, random, pathlib
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests

LEAGUE_ID = os.getenv("LEAGUE_ID", "508419792")
SEASON = int(os.getenv("SEASON", "2025"))
OUT_DIR = "docs/data"

TEAM_RAW = f"{OUT_DIR}/espn_mTeam.json"
ROSTER_RAW = f"{OUT_DIR}/espn_mRoster.json"
COMBINED   = f"{OUT_DIR}/team_rosters.json"

BASES = [
    f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}",
    f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}",
]

POS_MAP = {
    0:"Quarterback", 2:"Running back", 4:"Wide receiver", 6:"Tight end",
    16:"Team defense / special teams", 17:"Kicker",
}
NFL = {
    1:"ATL",2:"BUFF",3:"CHI",4:"CIN",5:"CLE",6:"DAL",7:"DEN",8:"DET",9:"GB",
    10:"TEN",11:"IND",12:"KC",13:"OAK",14:"LAR",15:"MIA",16:"MIN",17:"NE",
    18:"NO",19:"NYG",20:"NYJ",21:"PHI",22:"ARI",23:"PIT",24:"LAC",25:"SF",
    26:"SEA",27:"TB",28:"WSH",29:"CAR",30:"JAX",33:"BAL",34:"HOU",35:"NO TEAM"
}

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def ensure_out():
    os.makedirs(OUT_DIR, exist_ok=True)

def read_json_if_exists(path: str) -> Any | None:
    p = pathlib.Path(path)
    if p.exists() and p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None

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
    # Optional Cloudflare bypass cookie if you grabbed one from your browser:
    cf = os.getenv("CF_CLEARANCE")
    if cf:
        # CF typically sets cookie on domain (fantasy.espn.com) — set on .espn.com to be safe
        s.cookies.set("cf_clearance", cf, domain=".espn.com", secure=True)
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Origin": "https://fantasy.espn.com",
        "Referer": f"https://fantasy.espn.com/football/league?leagueId={LEAGUE_ID}&seasonId={SEASON}",
    })
    return s

def prime_session(s: requests.Session):
    """
    Hit a few public pages to let ESPN set harmless cookies and reduce bot score.
    Ignore failures.
    """
    urls = [
        f"https://fantasy.espn.com/football/league?leagueId={LEAGUE_ID}&seasonId={SEASON}",
        "https://g.espncdn.com/lm-static/ffl/images/ffl-fantasy-football-logo.png",
        "https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/scoreboard/nwe.png&h=40&w=40",  # a random asset
    ]
    for u in urls:
        try:
            s.get(u, timeout=15)
            time.sleep(0.3 + random.random()*0.4)
        except Exception:
            pass

def hardened_get(s: requests.Session, base: str, view: str) -> Dict[str, Any]:
    """
    Try alternate query shapes with backoff on a given base host.
    """
    shapes = [
        {"view": view, "forTeamId": 1},
        {"view": view},
        {"view": view, "scoringPeriodId": 0},
    ]
    errors: List[str] = []
    for shape in shapes:
        for attempt in range(1, 5):
            try:
                r = s.get(base, params=shape, timeout=30)
                ctype = r.headers.get("content-type", "")
                if "application/json" not in ctype:
                    raise RuntimeError(f"{view} Non-JSON (content-type={ctype})")
                return r.json()
            except Exception as e:
                errors.append(f"{base} {view} {shape} try={attempt}: {type(e).__name__}: {e}")
                time.sleep(0.7 + random.random()*0.9)
        time.sleep(0.8 + random.random()*0.6)
    raise RuntimeError("; ".join(errors[-6:]))

def get_json_any_host(s: requests.Session, view: str) -> Dict[str, Any]:
    prime_session(s)
    last_err = None
    for base in BASES:
        try:
            return hardened_get(s, base, view)
        except Exception as e:
            last_err = e
            # small pause before trying next base
            time.sleep(0.8 + random.random()*0.6)
    raise last_err or RuntimeError(f"{view} all hosts failed")

def normalize_teams(team_payload: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    teams: Dict[int, Dict[str, Any]] = {}
    for t in (team_payload.get("teams") or []):
        teams[t["id"]] = {
            "teamId": t["id"],
            "name": t.get("name") or f"Team {t['id']}",
            "abbrev": t.get("abbrev"),
            "logo": t.get("logo"),
            "owners": t.get("owners", []),
            "players": [],
        }
    return teams

def normalize_roster(roster_payload: Dict[str, Any], teams: Dict[int, Dict[str, Any]]):
    for t in (roster_payload.get("teams") or []):
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

def success_bundle(teams_map: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "league_id": LEAGUE_ID,
        "season": SEASON,
        "generated_utc": utc_now(),
        "teams": list(teams_map.values()),
    }

def main() -> int:
    ensure_out()

    # keep a last-good snapshot for fallback
    last_good = read_json_if_exists(COMBINED)

    try:
        s = make_session()
        # mTeam
        teams_raw = get_json_any_host(s, "mTeam")
        write(TEAM_RAW, {"fetched_at": utc_now(), "data": teams_raw})

        # mRoster
        rosters_raw = get_json_any_host(s, "mRoster")
        write(ROSTER_RAW, {"fetched_at": utc_now(), "data": rosters_raw})

        # normalize
        teams_map = normalize_teams(teams_raw)
        normalize_roster(rosters_raw, teams_map)

        final = success_bundle(teams_map)
        write(COMBINED, final)
        print(f"team_rosters: {len(final['teams'])} teams written")
        return 0

    except Exception as e:
        msg = f"{type(e).__name__}: {e}"

        # If we have last-good with teams, keep serving it (soft success)
        if last_good and isinstance(last_good, dict) and len(last_good.get("teams", [])) > 0:
            warn = {"generated_utc": utc_now(), "teams": last_good["teams"], "warning": msg}
            write(COMBINED, warn)
            write(TEAM_RAW, {"fetched_at": utc_now(), "error": msg})
            write(ROSTER_RAW, {"fetched_at": utc_now(), "error": msg})
            print(f"[WARN] fetch_league blocked; served last-good ({len(last_good['teams'])} teams). Detail: {msg}", file=sys.stderr)
            return 0  # soft OK

        # Otherwise emit explicit error files
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
