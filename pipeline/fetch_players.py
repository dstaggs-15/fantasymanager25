#!/usr/bin/env python3
from __future__ import annotations
import os, json, time, datetime, pathlib, requests
from typing import Any, Dict, List

# ---------- Config ----------
SEASON    = os.getenv("SEASON", "2025")
LIMIT     = 200                    # ESPN returns max ~200 per page
VIEWS     = ["kona_player_info", "players_wl"]  # info + waiver wire / availability
BASE_PLAY = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/players"

ROOT     = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
    "Origin": "https://fantasy.espn.com",
    "Referer": "https://fantasy.espn.com/football/players",
}
# Optional cookies if you later need private-only fields (usually not necessary for players list)
COOKIES = {}
if os.getenv("ESPN_SWID") and os.getenv("ESPN_S2"):
    COOKIES = {"SWID": os.getenv("ESPN_SWID"), "espn_s2": os.getenv("ESPN_S2")}

POS_MAP = {
    0: "Quarterback", 1: "Running Back", 2: "Wide Receiver", 3: "Tight End",
    4: "Kicker", 5: "Defense/Special Teams", 16: "Defensive Tackle",
    17: "Defensive End", 18: "Linebacker", 19: "Cornerback", 20: "Safety",
}

def utcnow() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def req(url: str, params: Dict[str, Any]) -> Any:
    r = requests.get(url, headers=HEADERS, cookies=COOKIES, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_all_players() -> List[Dict[str, Any]]:
    """Paginate over ESPN players endpoint with the exact views needed."""
    out: List[Dict[str, Any]] = []
    offset = 0
    # We try with kona_player_info (deep info); if that 403s in your environment, we still have players_wl
    while True:
        params = {"limit": LIMIT, "offset": offset, "scoringPeriodId": 0}
        # request both views (ESPN API accepts multiple "view" params)
        for v in VIEWS:
            params.setdefault("view", [])
            params["view"].append(v)
        data = req(BASE_PLAY, params)
        if not isinstance(data, list):
            # Some responses may wrap; normalize to list
            data = data.get("players") or data.get("items") or []
        if not data:
            break
        out.extend(data)
        offset += LIMIT
        time.sleep(0.25)  # be nice to their servers
    return out

def safe_num(x, default=0.0):
    try:
        if x is None: return default
        return float(x)
    except Exception:
        return default

def latest_projection(stats: List[Dict[str, Any]]) -> float:
    """Return projected season total if present, else 0."""
    if not stats: return 0.0
    # ESPN marks projections with statSourceId == 1 (actuals are 0)
    best = 0.0
    for s in stats:
        if s.get("statSourceId") == 1:
            best = max(best, safe_num(s.get("appliedTotal"), 0.0))
    return best

def recent_actual_avg(stats: List[Dict[str, Any]], window: int = 5) -> float:
    """Average of last N scoring periods where actual totals exist."""
    if not stats: return 0.0
    actuals = [safe_num(s.get("appliedTotal")) for s in stats if s.get("statSourceId") == 0]
    if not actuals: return 0.0
    # stats may be unordered; ESPN usually includes scoringPeriodId
    # sort by scoringPeriodId if present, else keep as-is
    def sp(s): return int(s.get("scoringPeriodId", 0))
    stats_sorted = sorted([s for s in stats if s.get("statSourceId") == 0], key=sp)
    tail = stats_sorted[-window:]
    vals = [safe_num(s.get("appliedTotal")) for s in tail]
    return round(sum(vals) / max(1, len(vals)), 2)

def summarize(players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create a compact table ready for the website."""
    rows: List[Dict[str, Any]] = []
    for p in players:
        info = p.get("player", p)  # some responses nest under "player"
        full = info.get("fullName") or info.get("name") or "—"
        pid  = info.get("id")
        pos  = POS_MAP.get(info.get("defaultPositionId"), "Unknown")
        pro  = info.get("proTeamAbbreviation") or info.get("proTeam") or info.get("proTeamId")
        # stats sometimes sit under info["stats"] or p["player"]["stats"]
        stats = info.get("stats") or p.get("player", {}).get("stats") or p.get("stats") or []

        rows.append({
            "id": pid,
            "name": full,
            "position": pos,
            "team": pro,
            "proj_season": latest_projection(stats),
            "recent_avg": recent_actual_avg(stats, window=5),
        })
    return rows

def main() -> int:
    raw = fetch_all_players()
    # Save full dump (handy for debugging / richer analytics later)
    (DATA_DIR / "players_raw.json").write_text(json.dumps({"generated_utc": utcnow(), "count": len(raw), "players": raw}, indent=2), encoding="utf-8")
    # Save compact table
    summary = summarize(raw)
    (DATA_DIR / "players_summary.json").write_text(json.dumps({"generated_utc": utcnow(), "count": len(summary), "rows": summary}, indent=2), encoding="utf-8")
    print(f"✅ players_summary.json rows={len(summary)}  | players_raw.json players={len(raw)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
