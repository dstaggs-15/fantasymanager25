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

def _clean_cookie(val: str | None) -> str | None:
    if not val:
        return None
    v = val.strip().strip('"').strip("'")
    return v

def _clean_swid(val: str | None) -> str | None:
    v = _clean_cookie(val)
    if not v:
        return None
    # ensure braces exist
    if not (v.startswith("{") and v.endswith("}")):
        v = "{" + v.strip("{}") + "}"
    return v

SWID = _clean_swid(os.getenv("ESPN_SWID"))
S2   = _clean_cookie(os.getenv("ESPN_S2"))

COOKIES = {}
if SWID and S2:
    COOKIES = {"SWID": SWID, "espn_s2": S2}

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
    # guard non-JSON
    ctype = (r.headers.get("content-type") or "").lower()
    if "json" not in ctype:
        raise RuntimeError(f"Non-JSON response (content-type={ctype})")
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
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
