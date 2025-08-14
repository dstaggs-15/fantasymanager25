#!/usr/bin/env python3
from __future__ import annotations
import os, json, time, datetime, pathlib, requests
from typing import Any, Dict, List

# ---------- Config ----------
SEASON    = os.getenv("SEASON", "2025")
LIMIT     = 200                              # paginate size
VIEW      = "players_wl"                     # public-friendly view
BASE      = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/players"

ROOT     = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
    "Origin": "https://fantasy.espn.com",
    "Referer": "https://fantasy.espn.com/football/players",
}
COOKIES = {}
if os.getenv("ESPN_SWID") and os.getenv("ESPN_S2"):
    COOKIES = {"SWID": os.getenv("ESPN_SWID"), "espn_s2": os.getenv("ESPN_S2")}

POS_MAP = {
    0: "Quarterback", 1: "Running Back", 2: "Wide Receiver", 3: "Tight End",
    4: "Kicker", 5: "Defense/Special Teams", 16: "Defensive Tackle", 17: "Defensive End",
    18: "Linebacker", 19: "Cornerback", 20: "Safety",
}

def utcnow() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def get_json(url: str, params: Dict[str, Any]) -> Any:
    """GET and return JSON; if response isn't JSON, raise a clear error."""
    r = requests.get(url, headers=HEADERS, cookies=COOKIES, params=params, timeout=30)
    # If status isn't 200, raise HTTPError with status first
    r.raise_for_status()
    # Some blocks return text/html; guard JSON parse
    ctype = (r.headers.get("content-type") or "").lower()
    if "application/json" not in ctype and "json" not in ctype:
        snippet = r.text[:160].replace("\n", " ")
        raise RuntimeError(f"Non-JSON response (content-type={ctype}): {snippet}")
    try:
        return r.json()
    except Exception as e:
        snippet = r.text[:160].replace("\n", " ")
        raise RuntimeError(f"JSON decode failed: {e}; snippet={snippet}")

def fetch_all_players() -> List[Dict[str, Any]]:
    """Paginate over ESPN public players endpoint."""
    players: List[Dict[str, Any]] = []
    offset = 0
    while True:
        params = {
            "view": VIEW,
            "limit": LIMIT,
            "offset": offset,
            "scoringPeriodId": 0,  # preseason-safe
        }
        data = get_json(BASE, params)

        # Normalize to list
        if isinstance(data, list):
            page = data
        else:
            # some rare responses wrap under "players"
            page = data.get("players") or data.get("items") or []

        if not page:
            break

        players.extend(page)
        offset += LIMIT
        time.sleep(0.25)  # politeness
    return players

def safe_num(x, default=0.0):
    try:
        if x is None: return default
        return float(x)
    except Exception:
        return default

def latest_projection(stats: List[Dict[str, Any]]) -> float:
    """Projected season total if present (statSourceId == 1)."""
    if not stats: return 0.0
    best = 0.0
    for s in stats:
        if s.get("statSourceId") == 1:
            best = max(best, safe_num(s.get("appliedTotal"), 0.0))
    return best

def recent_actual_avg(stats: List[Dict[str, Any]], window: int = 5) -> float:
    """Average of last N actual games (statSourceId == 0)."""
    if not stats: return 0.0
    actuals = [s for s in stats if s.get("statSourceId") == 0]
    if not actuals: return 0.0
    actuals.sort(key=lambda s: int(s.get("scoringPeriodId", 0)))
    tail = actuals[-window:]
    vals = [safe_num(s.get("appliedTotal")) for s in tail]
    return round(sum(vals) / max(1, len(vals)), 2)

def summarize(players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for p in players:
        # some responses: { "player": {..., "stats":[...] } }
        info = p.get("player", p)
        full = info.get("fullName") or info.get("name") or "—"
        pid  = info.get("id")
        pos  = POS_MAP.get(info.get("defaultPositionId"), "Unknown")

        # pro team: try abbrev, else numeric id
        pro  = info.get("proTeamAbbreviation")
        if not pro:
            pro = info.get("proTeam")
        if not pro:
            pro = info.get("proTeamId")

        stats = info.get("stats") or p.get("stats") or []
        rows.append({
            "id": pid,
            "name": full,
            "position": pos,
            "team": pro if pro is not None else "—",
            "proj_season": latest_projection(stats),
            "recent_avg": recent_actual_avg(stats, window=5),
        })
    return rows

def write(path: pathlib.Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def main() -> int:
    try:
        players = fetch_all_players()
        write(DATA_DIR / "players_raw.json", {
            "generated_utc": utcnow(), "count": len(players), "players": players
        })
        summary = summarize(players)
        write(DATA_DIR / "players_summary.json", {
            "generated_utc": utcnow(), "count": len(summary), "rows": summary
        })
        # also bump status.json note (append-only style)
        status_path = DATA_DIR / "status.json"
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
        except Exception:
            status = {}
        status["players_note"] = f"players_summary rows={len(summary)}"
        status["generated_utc"] = utcnow()
        write(status_path, status)
        print(f"✅ players_summary.json rows={len(summary)} | players_raw.json players={len(players)}")
        return 0
    except Exception as e:
        # Graceful fallback: write minimal/empty files so the site keeps working
        msg = f"players fetch error: {type(e).__name__}: {e}"
        write(DATA_DIR / "players_raw.json", {"generated_utc": utcnow(), "count": 0, "error": msg, "players": []})
        write(DATA_DIR / "players_summary.json", {"generated_utc": utcnow(), "count": 0, "rows": [], "error": msg})
        status_path = DATA_DIR / "status.json"
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
        except Exception:
            status = {}
        status["players_error"] = msg
        status["generated_utc"] = utcnow()
        write(status_path, status)
        print(f"⚠️ {msg}")
        return 0  # don't fail the workflow

if __name__ == "__main__":
    raise SystemExit(main())
