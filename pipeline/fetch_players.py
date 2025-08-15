# pipeline/fetch_players.py
"""
Fetch active NFL players from ESPN Fantasy API and write:
- docs/data/players_raw.json     (all fields we downloaded; paginated)
- docs/data/players_summary.json (lightweight table for the UI)

Requires repo/runner env:
  SWID      -> like {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
  ESPN_S2   -> long cookie string

Exit code 0 on success; nonzero on failure.
"""

from __future__ import annotations
import os, sys, json, time
from datetime import datetime, timezone
from typing import Dict, Any, List

import requests

SEASON = int(os.getenv("SEASON", "2025"))
OUT_DIR = "docs/data"
RAW_PATH = f"{OUT_DIR}/players_raw.json"
SUM_PATH = f"{OUT_DIR}/players_summary.json"

# --- Helpers -----------------------------------------------------------------

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        print(json.dumps({"generated_utc": utc_now(), "count": 0,
                          "error": f"missing env {name}"}), file=sys.stderr)
        sys.exit(1)
    return v

def make_session() -> requests.Session:
    swid = require_env("SWID")
    s2   = require_env("ESPN_S2")

    s = requests.Session()
    # Cookies must match the fantasy domain
    s.cookies.set("SWID", swid, domain=".espn.com", secure=True)
    s.cookies.set("espn_s2", s2,  domain=".espn.com", secure=True)

    # Headers that ESPN expects
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://fantasy.espn.com/football/league?seasonId={SEASON}",
        "Origin": "https://fantasy.espn.com",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    })
    return s

# ESPN players endpoint. We must send X-Fantasy-Filter.
BASE = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/players"

# Basic filter: active NFL players, exclude free agents without teamId, page in chunks.
# You can enrich this later (add position filters, injury data, etc.).
def fantasy_filter(offset: int, limit: int = 200) -> Dict[str, Any]:
    return {
        "filterActive": {"value": True},
        "filterSlotIds": {"value": list(range(0, 17))},  # all offensive slots
        "filterStatsForCurrentSeasonScoringPeriodId": {"value": 0},
        "limit": limit,
        "offset": offset,
        "sortPercOwned": {"sortAsc": False, "sortPriority": 1},
        "sortDraftRanks": {"sortPriority": 2, "sortAsc": True, "value": "STANDARD"},
        "filterRanksForScoringPeriodIds": {"value": [0]},
        "filterRanksForRankTypes": {"value": ["STANDARD"]},
        "filterRanksForSlotIds": {"value": [0,2,4,6,16]},  # QB,RB,WR,TE,DST
    }

def fetch_page(session: requests.Session, offset: int) -> List[Dict[str, Any]]:
    # ESPN accepts GET with the filter in X-Fantasy-Filter header.
    headers = {
        "X-Fantasy-Filter": json.dumps(fantasy_filter(offset)),
    }
    # scoringPeriodId=0 = season aggregate
    params = {"scoringPeriodId": 0}
    r = session.get(BASE, headers=headers, params=params, timeout=30)
    ctype = r.headers.get("content-type", "")
    if "application/json" not in ctype:
        raise RuntimeError(f"Non-JSON (content-type={ctype})")
    return r.json()  # list of players for this page

def summarize(players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for p in players:
        # Safe accessors
        pid = p.get("id")
        fn  = (p.get("firstName") or "").strip()
        ln  = (p.get("lastName") or "").strip()
        name = (p.get("fullName") or f"{fn} {ln}").strip()
        pos  = (p.get("defaultPositionId") or p.get("positionId"))
        team = p.get("proTeamId")

        # Season projections/avg points if present (slot 0 = overall)
        proj = None
        last5 = None
        for stat in p.get("stats", []):
            # statSourceId 0 = projected, 1 = actual; 0 scoringPeriodId 0 = season
            if stat.get("statSourceId") == 0 and stat.get("scoringPeriodId") == 0:
                proj = stat.get("appliedTotal")
            # rolling last 5 actual may not be present pre-season; leave None
            if stat.get("statSourceId") == 1 and stat.get("scoringPeriodId") == 0:
                # Some payloads carry "appliedAverage" for various windows; fallback
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

def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    s = make_session()

    all_players: List[Dict[str, Any]] = []
    offset = 0
    page_size = 200
    max_pages = 100  # safety

    try:
        for _ in range(max_pages):
            chunk = fetch_page(s, offset)
            if not isinstance(chunk, list):
                raise RuntimeError("Unexpected payload (not a list)")
            if not chunk:
                break
            all_players.extend(chunk)
            offset += page_size
            # small polite delay
            time.sleep(0.25)

        # Write RAW
        with open(RAW_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "generated_utc": utc_now(),
                "count": len(all_players),
                "players": all_players,
            }, f, ensure_ascii=False, separators=(",", ":"))

        # Write SUMMARY
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
        # On error, still write small error files so the UI can message it
        err_msg = f"players fetch error: {type(e).__name__}: {e}"
        payload = {"generated_utc": utc_now(), "count": 0, "error": err_msg}
        with open(RAW_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        with open(SUM_PATH, "w", encoding="utf-8") as f:
            json.dump({**payload, "rows": []}, f, ensure_ascii=False, separators=(",", ":"))
        print(err_msg, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
