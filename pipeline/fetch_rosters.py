#!/usr/bin/env python3
"""
Hardened ESPN fetcher:
- Uses a Session with real browser headers
- Sets SWID/espn_s2 cookies on the .espn.com domain
- Warms up by loading the league webpage first
- Retries with backoff + cache-buster
Writes:
  docs/data/team_rosters.json
  docs/data/players_summary.json
"""

import os
import sys
import json
import time
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

import requests

LEAGUE_ID = os.getenv("LEAGUE_ID", "508419792")
SEASON = os.getenv("SEASON", "2025")

OUT_ROSTERS = "docs/data/team_rosters.json"
OUT_PLAYERS = "docs/data/players_summary.json"
STATUS_FILE = "docs/data/status.json"

BASE_API = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"
LEAGUE_WEB = f"https://fantasy.espn.com/football/league?leagueId={LEAGUE_ID}"

UA_POOL = [
    # current desktop UAs (mix Chrome/Edge, Windows/Linux)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/126.0 Safari/537.36",
]

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def get_cookies() -> Dict[str, str]:
    swid = os.getenv("SWID") or os.getenv("ESPN_SWID")
    s2 = os.getenv("ESPN_S2") or os.getenv("ESPN_S2_TOKEN") or os.getenv("ESPN_S2")
    if not swid or not s2:
        raise RuntimeError("Missing SWID / ESPN_S2 in env.")
    return {"SWID": swid, "espn_s2": s2}

def new_session(cookies: Dict[str, str]) -> requests.Session:
    s = requests.Session()
    # set cookies on the *.espn.com scope
    jar = requests.cookies.RequestsCookieJar()
    jar.set("SWID", cookies["SWID"], domain=".espn.com", path="/")
    jar.set("espn_s2", cookies["espn_s2"], domain=".espn.com", path="/")
    s.cookies.update(jar)

    s.headers.update({
        "User-Agent": random.choice(UA_POOL),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": LEAGUE_WEB,
        "Sec-Fetch-Site": "same-origin",
    })
    return s

def warm_up(session: requests.Session) -> None:
    # Touch the league webpage like a browser; ignore response body
    try:
        r = session.get(LEAGUE_WEB, timeout=20)
        # tiny pause; helps with CF timing
        time.sleep(1.0)
    except Exception:
        pass

def get_json(session: requests.Session, url: str, params: Dict[str, Any]) -> Any:
    # Retry with backoff, rotate UA occasionally, add cache-buster
    last_err = None
    for attempt in range(1, 7):
        qp = dict(params)
        qp["_"] = int(time.time() * 1000)  # cache buster
        try:
            if attempt > 1:
                # rotate UA after first attempt
                session.headers["User-Agent"] = random.choice(UA_POOL)
            r = session.get(url, params=qp, timeout=25)
            ctype = r.headers.get("content-type", "")
            if r.ok and "application/json" in ctype.lower():
                return r.json()
            last_err = RuntimeError(f"Non-JSON (content-type={ctype}) status={r.status_code}")
        except Exception as e:
            last_err = e
        # backoff with jitter
        time.sleep(0.8 * attempt + random.uniform(0.2, 0.6))
        # occasionally touch webpage again
        if attempt in (3, 5):
            warm_up(session)
    raise RuntimeError(f"GET {url} failed after retries: {last_err}")

def fetch_teams(session: requests.Session) -> Tuple[List[Dict[str, Any]], Dict[int, Dict[str, Any]]]:
    data = get_json(session, BASE_API, params={"view": "mTeam"})
    teams = data.get("teams", []) or []
    by_id = {t["id"]: t for t in teams}
    return teams, by_id

def fetch_team_roster(session: requests.Session, team_id: int) -> List[Dict[str, Any]]:
    data = get_json(session, BASE_API, params={"view": "mRoster", "teamId": team_id})
    teams = data.get("teams", []) or []
    if not teams:
        return []
    roster = teams[0].get("roster", {}) or {}
    return roster.get("entries", []) or []

def flatten_player(entry: Dict[str, Any], team_meta: Dict[str, Any]) -> Dict[str, Any]:
    ppe = entry.get("playerPoolEntry", {}) or {}
    player = ppe.get("player", {}) or {}
    full_name = player.get("fullName") or player.get("name") or "Unknown"
    default_pos = player.get("defaultPositionId")
    POS_MAP = {0:"QB",2:"RB",4:"WR",6:"TE",16:"D/ST",17:"K",23:"FLEX"}
    pos = POS_MAP.get(default_pos, str(default_pos) if default_pos is not None else "")
    return {
        "id": player.get("id"),
        "name": full_name,
        "pos": pos,
        "proTeamId": player.get("proTeamId"),
        "teamId": team_meta.get("id"),
        "team": team_meta.get("abbrev") or team_meta.get("location") or "",
        "source": "espn:mRoster",
    }

def write_json(path: str, payload: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def main() -> int:
    ts = now_utc_iso()
    cookies = get_cookies()
    session = new_session(cookies)
    warm_up(session)  # establish session like a browser

    teams, _by_id = fetch_teams(session)
    if not teams:
        raise RuntimeError("No teams returned by mTeam")

    combined = {"generated_utc": ts, "leagueId": LEAGUE_ID, "season": SEASON, "teams": []}
    flat: List[Dict[str, Any]] = []

    for t in teams:
        tid = t["id"]
        try:
            entries = fetch_team_roster(session, tid)
        except Exception as e:
            entries = []
            print(f"[warn] roster fetch failed for team {tid}: {e}", file=sys.stderr)

        block = {
            "teamId": tid,
            "abbrev": t.get("abbrev"),
            "name": t.get("name"),
            "count": len(entries),
            "players": [],
        }
        for e in entries:
            flat_p = flatten_player(e, t)
            block["players"].append(flat_p)
            flat.append(flat_p)

        combined["teams"].append(block)

    write_json(OUT_ROSTERS, combined)
    write_json(OUT_PLAYERS, {"generated_utc": ts, "count": len(flat), "rows": flat})

    # status note (optional)
    try:
        status = {}
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                status = json.load(f)
        status.setdefault("notes", []).append(
            f"{ts} wrote team_rosters.json ({len(combined['teams'])} teams) & players_summary.json ({len(flat)})"
        )
        write_json(STATUS_FILE, status)
    except Exception:
        pass

    print(f"Wrote rosters={len(combined['teams'])}, players={len(flat)}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        ts = now_utc_iso()
        os.makedirs("docs/data", exist_ok=True)
        write_json(OUT_ROSTERS, {"generated_utc": ts, "teams": [], "error": str(e)})
        write_json(OUT_PLAYERS, {"generated_utc": ts, "count": 0, "rows": [], "error": str(e)})
        print(f"fetch_rosters ERROR: {e}", file=sys.stderr)
        sys.exit(2)
