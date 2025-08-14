#!/usr/bin/env python3
from __future__ import annotations
import os, json, datetime, time, pathlib, requests

# ----- config -----
LEAGUE_ID = os.getenv("LEAGUE_ID", "508419792")
SEASON    = os.getenv("SEASON", "2025")

ROOT     = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
    "Origin": "https://fantasy.espn.com",
    "Referer": f"https://fantasy.espn.com/football/league?leagueId={LEAGUE_ID}",
}

COOKIES = {}
if os.getenv("ESPN_SWID") and os.getenv("ESPN_S2"):
    COOKIES = {"SWID": os.getenv("ESPN_SWID"), "espn_s2": os.getenv("ESPN_S2")}

def utcnow() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def write_json(path: pathlib.Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def fetch_view(session: requests.Session, view: str, extra_params: dict | None = None) -> dict:
    params = {"view": view}
    if extra_params:
        params.update(extra_params)
    r = session.get(BASE, headers=HEADERS, cookies=COOKIES, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def main() -> int:
    s = requests.Session()
    manifest = {"league_id": LEAGUE_ID, "season": SEASON, "generated_utc": utcnow(), "files": [], "errors": []}

    def save(name: str, data):
        out = DATA_DIR / name
        write_json(out, data)
        manifest["files"].append(name)

    # Core views
    for v in ["mStandings", "mMatchup", "mRoster", "mTeam", "mSettings"]:
        try:
            data = fetch_view(s, v)
            save(f"espn_{v}.json", {"fetched_at": utcnow(), "data": data})
            time.sleep(0.25)
        except Exception as e:
            manifest["errors"].append(f"{v}: {type(e).__name__}: {e}")

    # Weekly matchup snapshots (non-fatal pre-season)
    for sp in range(1, 19):
        try:
            data = fetch_view(s, "mMatchup", {"scoringPeriodId": sp})
            save(f"espn_mMatchup_week_{sp}.json", {"fetched_at": utcnow(), "data": data})
            time.sleep(0.2)
        except Exception as e:
            manifest["errors"].append(f"mMatchup_week_{sp}: {type(e).__name__}: {e}")

    # Status + manifest
    write_json(DATA_DIR / "espn_manifest.json", manifest)
    status_note = "ESPN fetch OK" if manifest["files"] else "ESPN fetch failed: no files"
    if manifest["errors"]:
        status_note = f"ESPN fetch partial: {len(manifest['errors'])} error(s)"
    write_json(DATA_DIR / "status.json",
               {"generated_utc": utcnow(), "season": SEASON, "week": None, "notes": status_note})

    # Also write a simple latest.json (table-ready) so UI can be dumb-simple
    # Try to map standings into rows: team, wins, losses, PF, PA
    rows = []
    try:
        raw = json.loads((DATA_DIR / "espn_mStandings.json").read_text(encoding="utf-8"))
        entries = raw.get("data", {}).get("standings", {}).get("entries", [])
        for e in entries:
            team = e.get("team", {}) or {}
            name = team.get("displayName") or f"{team.get('location','').strip()} {team.get('nickname','').strip()}".strip() or "—"
            stats = { (st.get("name") or "").lower(): st.get("value") for st in (e.get("stats") or []) }
            rows.append({
                "teamName": name,
                "wins": int(stats.get("wins", 0) or 0),
                "losses": int(stats.get("losses", 0) or 0),
                "pointsFor": float(stats.get("pointsfor", 0) or 0),
                "pointsAgainst": float(stats.get("pointsagainst", 0) or 0),
            })
    except Exception as e:
        manifest["errors"].append(f"latest.json mapping: {type(e).__name__}: {e}")

    write_json(DATA_DIR / "latest.json", {"generated_utc": utcnow(), "rows": rows})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
