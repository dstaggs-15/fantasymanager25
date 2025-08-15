# pipeline/fetch_players.py
"""
Players fetch with graceful fallback.

1) Try the private fantasy players endpoint (needs SWID + ESPN_S2).
   - Writes projections & recent averages when available.
2) If ESPN serves HTML (anti-bot), fall back to public ESPN players feed
   (no cookies required) so the site still has player rows.

Outputs (always under docs/data):
  - players_raw.json        (source payload or minimal payload on fallback)
  - players_summary.json    (rows UI reads)

Env required for private pull:
  SWID     = {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
  ESPN_S2  = long cookie string
Optional:
  SEASON   = 2025 (default)
"""

from __future__ import annotations
import json, os, sys, time, random
from datetime import datetime, timezone
from typing import List, Dict, Any

import requests

SEASON = int(os.getenv("SEASON", "2025"))
OUT_DIR = "docs/data"
RAW_PATH = f"{OUT_DIR}/players_raw.json"
SUM_PATH = f"{OUT_DIR}/players_summary.json"

# Private fantasy endpoint (cookie-gated)
FANTASY_BASE = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/players"

# Public (no cookie) – broad NFL athletes list
PUBLIC_FEED = "https://site.api.espn.com/apis/common/v3/sports/football/nfl/athletes?limit=2000"

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def write(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))

# ---------------------- PRIVATE FANTASY PULL ----------------------

def require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"missing env {name}")
    return v

def make_private_session() -> requests.Session:
    swid = require_env("SWID")
    s2   = require_env("ESPN_S2")
    s = requests.Session()
    s.cookies.set("SWID", swid, domain=".espn.com", secure=True)
    s.cookies.set("espn_s2", s2,  domain=".espn.com", secure=True)
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": f"https://fantasy.espn.com/football/freeagency?seasonId={SEASON}",
        "Origin": "https://fantasy.espn.com",
    })
    return s

def fantasy_filter(offset: int, limit: int = 100) -> Dict[str, Any]:
    # smaller page + sane filters reduces bot triggers
    return {
        "filterActive": {"value": True},
        "filterSlotIds": {"value": list(range(0, 20))},
        "filterRanksForScoringPeriodIds": {"value": [0]},
        "filterRanksForRankTypes": {"value": ["STANDARD"]},
        "filterRanksForSlotIds": {"value": [0, 2, 4, 6, 16]},
        "limit": limit,
        "offset": offset,
        "sortPercOwned": {"sortPriority": 1, "sortAsc": False},
        "sortDraftRanks": {"sortPriority": 2, "sortAsc": True, "value": "STANDARD"},
    }

def private_page(session: requests.Session, offset: int) -> List[Dict[str, Any]]:
    headers = {"X-Fantasy-Filter": json.dumps(fantasy_filter(offset))}
    params = {"scoringPeriodId": 0, "view": "players_wl"}
    r = session.get(FANTASY_BASE, headers=headers, params=params, timeout=30)
    ctype = r.headers.get("content-type", "")
    if "application/json" not in ctype:
        raise RuntimeError(f"Non-JSON (content-type={ctype})")
    return r.json()

def summarize_private(players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for p in players:
        pid  = p.get("id")
        name = (p.get("fullName")
                or f"{p.get('firstName','')} {p.get('lastName','')}".strip())
        pos  = p.get("defaultPositionId") or p.get("positionId")
        team = p.get("proTeamId")
        proj = None
        last5 = None
        for st in (p.get("stats") or []):
            # 0=projected, 1=actual
            if st.get("statSourceId") == 0 and st.get("scoringPeriodId") == 0:
                proj = st.get("appliedTotal")
            if st.get("statSourceId") == 1 and st.get("scoringPeriodId") == 0:
                last5 = st.get("appliedAverage")
        rows.append({
            "id": pid, "name": name,
            "positionId": pos, "proTeamId": team,
            "proj_season": proj, "recent_avg": last5,
            "source": "private"
        })
    return rows

def try_private() -> Dict[str, Any]:
    s = make_private_session()
    all_players: List[Dict[str, Any]] = []
    offset = 0
    page_size = 100
    max_pages = 60

    for _ in range(max_pages):
        # retry each page up to 4 times if we see HTML
        last_err = None
        for attempt in range(4):
            try:
                chunk = private_page(s, offset)
                break
            except Exception as e:
                last_err = e
                time.sleep(0.7 + random.random() * 0.7)
        else:
            raise last_err or RuntimeError("private page failed")

        if not isinstance(chunk, list):
            raise RuntimeError("Unexpected payload (not list)")
        all_players.extend(chunk)
        if len(chunk) < page_size:
            break
        offset += page_size
        time.sleep(0.3 + random.random() * 0.3)

    return {
        "generated_utc": utc_now(),
        "count": len(all_players),
        "players": all_players,
        "mode": "private",
    }

# ---------------------- PUBLIC FALLBACK ----------------------

def public_players() -> Dict[str, Any]:
    # Public athletes feed (no cookies). Shape is different, but safe.
    r = requests.get(PUBLIC_FEED, timeout=30, headers={
        "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        "Accept": "application/json, text/plain, */*",
    })
    ctype = r.headers.get("content-type", "")
    if "application/json" not in ctype:
        raise RuntimeError(f"Public feed non-JSON (content-type={ctype})")
    data = r.json()

    # The public response has 'athletes' list (current ESPN format).
    # If it changes, we still produce a stable, minimal summary.
    athletes = data.get("athletes") or data.get("items") or []
    players = []
    for a in athletes:
        # different keys across variants; be defensive
        pid  = a.get("id") or a.get("uid") or a.get("athlete", {}).get("id")
        name = a.get("displayName") or a.get("fullName") or a.get("name")
        pos  = (a.get("position", {}) or {}).get("abbreviation") or a.get("position")
        team = (a.get("team", {}) or {}).get("abbreviation") or a.get("team")
        players.append({
            "id": pid, "name": name,
            "position": pos, "team": team,
            "source": "public"
        })

    return {
        "generated_utc": utc_now(),
        "count": len(players),
        "players": players,
        "mode": "public",
    }

def summarize_public(players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for p in players:
        rows.append({
            "id": p.get("id"),
            "name": p.get("name"),
            "positionId": None,     # unknown here
            "proTeamId": None,      # unknown here
            "proj_season": None,
            "recent_avg": None,
            "team": p.get("team"),
            "position": p.get("position"),
        })
    return rows

# ---------------------- MAIN ----------------------

def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1) Try private pull (if cookies missing, skip to public)
    private_ok = False
    raw = None
    try:
        if os.getenv("SWID") and os.getenv("ESPN_S2"):
            raw = try_private()
            private_ok = True
        else:
            raise RuntimeError("cookies not provided")
    except Exception as e:
        # Fallback to public
        try:
            raw = public_players()
        except Exception as e2:
            # Write minimal error files and fail
            err = {"generated_utc": utc_now(), "count": 0,
                   "error": f"players fetch error: {type(e2).__name__}: {e2}"}
            write(RAW_PATH, err)
            write(SUM_PATH, {**err, "rows": []})
            print(err["error"], file=sys.stderr)
            return 2

    write(RAW_PATH, raw)

    # 2) Summarize into a uniform table
    if raw.get("mode") == "private":
        rows = summarize_private(raw.get("players", []))
    else:
        rows = summarize_public(raw.get("players", []))

    write(SUM_PATH, {
        "generated_utc": utc_now(),
        "count": len(rows),
        "rows": rows
    })

    print(f"players: mode={raw.get('mode')} wrote {len(rows)} rows")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
