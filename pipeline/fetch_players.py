# pipeline/fetch_players.py
"""
Fetch active NFL players from ESPN Fantasy API and write:
- docs/data/players_raw.json
- docs/data/players_summary.json

Needs env:
  SWID     = {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
  ESPN_S2  = (long cookie string)

If ESPN returns HTML (bot page), we retry a few times and then fail
gracefully while writing small JSON error files so the UI won't break.
"""

from __future__ import annotations
import os, sys, json, time, random
from datetime import datetime, timezone
from typing import Dict, Any, List

import requests

SEASON = int(os.getenv("SEASON", "2025"))
OUT_DIR = "docs/data"
RAW_PATH = f"{OUT_DIR}/players_raw.json"
SUM_PATH = f"{OUT_DIR}/players_summary.json"

BASE = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/players"

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        print(f"missing env {name}", file=sys.stderr)
        sys.exit(1)
    return v

def make_session() -> requests.Session:
    swid = require_env("SWID")
    s2   = require_env("ESPN_S2")

    s = requests.Session()
    # ESPN cookies on the .espn.com domain
    s.cookies.set("SWID", swid, domain=".espn.com", secure=True)
    s.cookies.set("espn_s2", s2,  domain=".espn.com", secure=True)

    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": f"https://fantasy.espn.com/football/freeagency?leagueId=508419792&seasonId={SEASON}",
        "Origin": "https://fantasy.espn.com",
        # this header is critical for /players
        # value is the JSON string of the filter (set per-request)
    })
    return s

def fantasy_filter(offset: int, limit: int = 200) -> Dict[str, Any]:
    # This mirrors what the site requests from the Free Agency page.
    return {
        "filterActive": {"value": True},
        "filterSlotIds": {"value": list(range(0, 20))},  # most slots
        "filterRanksForScoringPeriodIds": {"value": [0]},
        "filterRanksForRankTypes": {"value": ["STANDARD"]},
        "filterRanksForSlotIds": {"value": [0, 2, 4, 6, 16]},  # QB, RB, WR, TE, DST
        "limit": limit,
        "offset": offset,
        "sortPercOwned": {"sortPriority": 1, "sortAsc": False},
        "sortDraftRanks": {"sortPriority": 2, "sortAsc": True, "value": "STANDARD"},
    }

def get_page(session: requests.Session, offset: int) -> List[Dict[str, Any]]:
    headers = {
        "X-Fantasy-Filter": json.dumps(fantasy_filter(offset)),
    }
    # IMPORTANT: include view=players_wl (what the web app uses)
    params = {"scoringPeriodId": 0, "view": "players_wl"}
    r = session.get(BASE, headers=headers, params=params, timeout=30)
    ctype = r.headers.get("content-type", "")
    if "application/json" not in ctype:
        raise RuntimeError(f"Non-JSON (content-type={ctype})")
    return r.json()

def summarize(players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for p in players:
        pid = p.get("id")
        name = (p.get("fullName") or f"{p.get('firstName','')} {p.get('lastName','')}").strip()
        pos  = p.get("defaultPositionId") or p.get("positionId")
        team = p.get("proTeamId")
        proj = None
        last5 = None
        for stat in p.get("stats", []) or []:
            if stat.get("statSourceId") == 0 and stat.get("scoringPeriodId") == 0:
                proj = stat.get("appliedTotal")
            if stat.get("statSourceId") == 1 and stat.get("scoringPeriodId") == 0:
                last5 = stat.get("appliedAverage")
        rows.append({
            "id": pid,
            "name": name,
            "positionId": pos,
            "proTeamId": team,
            "proj_season": proj,
            "recent_avg": last5,
        })
    return rows

def write_error(e: Exception) -> int:
    err_msg = f"players fetch error: {type(e).__name__}: {e}"
    payload = {"generated_utc": utc_now(), "count": 0, "error": err_msg}
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    with open(SUM_PATH, "w", encoding="utf-8") as f:
        json.dump({**payload, "rows": []}, f, ensure_ascii=False, separators=(",", ":"))
    print(err_msg, file=sys.stderr)
    return 2

def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    s = make_session()

    all_players: List[Dict[str, Any]] = []
    offset = 0
    page_size = 200
    max_pages = 100

    try:
        for _ in range(max_pages):
            # retry up to 4 times per page if we see HTML
            for attempt in range(4):
                try:
                    chunk = get_page(s, offset)
                    break
                except Exception as e:
                    if attempt == 3:
                        raise
                    # small jittered backoff (helps with CF heuristics)
                    time.sleep(0.6 + random.random() * 0.6)
            if not chunk:
                break
            if not isinstance(chunk, list):
                raise RuntimeError("Unexpected payload (not list)")
            all_players.extend(chunk)
            if len(chunk) < page_size:
                break
            offset += page_size
            time.sleep(0.25)

        with open(RAW_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "generated_utc": utc_now(),
                "count": len(all_players),
                "players": all_players,
            }, f, ensure_ascii=False, separators=(",", ":"))

        summary_rows = summarize(all_players)
        with open(SUM_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "generated_utc": utc_now(),
                "count": len(summary_rows),
                "rows": summary_rows,
            }, f, ensure_ascii=False, separators=(",", ":"))

        print(f"Wrote {len(all_players)} players to {RAW_PATH} and {len(summary_rows)} rows to {SUM_PATH}")
        return 0

    except Exception as e:
        return write_error(e)

if __name__ == "__main__":
    raise SystemExit(main())
