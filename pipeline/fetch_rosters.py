#!/usr/bin/env python3
"""
Fetch ESPN league rosters with a browser-like client.

- Uses cloudscraper (requests-compatible) to negotiate Cloudflare like Chrome
- Sets SWID / espn_s2 cookies on .espn.com
- Warms up by loading the league webpage before API calls
- Retries with backoff and cache-buster
- Writes:
    docs/data/team_rosters.json
    docs/data/players_summary.json
    (app pages read these)
"""

import os
import sys
import json
import time
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

# cloudscraper provides a drop-in Session with proper TLS/JA3 like a browser
try:
    import cloudscraper  # type: ignore
except Exception as e:
    print("cloudscraper is required. Add it to requirements.txt", file=sys.stderr)
    raise

LEAGUE_ID = os.getenv("LEAGUE_ID", "508419792")
SEASON = os.getenv("SEASON", "2025")

OUT_ROSTERS = "docs/data/team_rosters.json"
OUT_PLAYERS = "docs/data/players_summary.json"
STATUS_FILE = "docs/data/status.json"

BASE_API = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"
LEAGUE_WEB = f"https://fantasy.espn.com/football/league?leagueId={LEAGUE_ID}"

UA_POOL = [
    # Realistic desktop UAs
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/126.0.0.0 Safari/537.36",
]

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def get_cookies() -> Dict[str, str]:
    swid = os.getenv("SWID") or os.getenv("ESPN_SWID")
    s2 = os.getenv("ESPN_S2") or os.getenv("ESPN_S2_TOKEN")
    if not swid or not s2:
        raise RuntimeError("Missing SWID / ESPN_S2 in env (set GitHub secrets SWID and ESPN_S2).")
    return {"SWID": swid, "espn_s2": s2}

def new_session(cookies: Dict[str, str]):
    # cloudscraper.create_scraper returns a requests-compatible Session
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "linux", "mobile": False}
    )
    # set cookies for *.espn.com
    jar = scraper.cookies
    jar.set("SWID", cookies["SWID"], domain=".espn.com", path="/")
    jar.set("espn_s2", cookies["espn_s2"], domain=".espn.com", path="/")

    # baseline headers that look like a browser XHR
    scraper.headers.update({
        "User-Agent": random.choice(UA_POOL),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": LEAGUE_WEB,
        "Origin": "https://fantasy.espn.com",
        "Connection": "keep-alive",
        "DNT": "1",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "X-Requested-With": "XMLHttpRequest",
    })
    return scraper

def warm_up(session) -> None:
    # Touch the league web page (establish cookies / CF allow-list)
    try:
        _ = session.get(LEAGUE_WEB, timeout=30)
        time.sleep(1.0)
    except Exception:
        pass

def get_json(session, url: str, params: Dict[str, Any]) -> Any:
    last_err: Exception | None = None
    for attempt in range(1, 11):  # more tries because CF sometimes needs an extra pass
        qp = dict(params)
        qp["_"] = int(time.time() * 1000)  # cache buster
        try:
            if attempt > 1:
                session.headers["User-Agent"] = random.choice(UA_POOL)

            r = session.get(url, params=qp, timeout=35)
            ctype = (r.headers.get("content-type") or "").lower()
            if r.ok and "application/json" in ctype:
                return r.json()

            # Some CF pages return 200 HTML; treat as block
            last_err = RuntimeError(f"Non-JSON (content-type={ctype}) status={r.status_code}")
        except Exception as e:
            last_err = e

        # Backoff with jitter; re-warm occasionally
        time.sleep(0.7 * attempt + random.uniform(0.3, 0.8))
        if attempt in (3, 6, 9):
            warm_up(session)

    raise RuntimeError(f"GET {url} failed after retries: {last_err}")

def fetch_teams(session) -> Tuple[List[Dict[str, Any]], Dict[int, Dict[str, Any]]]:
    data = get_json(session, BASE_API, params={"view": "mTeam"})
    teams = data.get("teams", []) or []
    return teams, {t["id"]: t for t in teams}

def fetch_team_roster(session, team_id: int) -> List[Dict[str, Any]]:
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
    warm_up(session)

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
            fp = flatten_player(e, t)
            block["players"].append(fp)
            flat.append(fp)
        combined["teams"].append(block)

    write_json(OUT_ROSTERS, combined)
    write_json(OUT_PLAYERS, {"generated_utc": ts, "count": len(flat), "rows": flat})
    print(f"Wrote team_rosters={len(combined['teams'])}, players={len(flat)}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        ts = now_utc_iso()
        os.makedirs("docs/data", exist_ok=True)
        # Write error stubs so the site can surface the failure reason
        write_json(OUT_ROSTERS, {"generated_utc": ts, "teams": [], "error": str(e)})
        write_json(OUT_PLAYERS, {"generated_utc": ts, "count": 0, "rows": [], "error": str(e)})
        print(f"fetch_rosters ERROR: {e}", file=sys.stderr)
        sys.exit(2)
