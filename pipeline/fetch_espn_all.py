#!/usr/bin/env python3
"""
Single-file ESPN fetcher (no imports from other project files).
- Works for public leagues; can optionally use cookies if provided.
- Writes outputs to fantasymanager25/docs/data/.
- Produces a manifest + status so the frontend can show errors gracefully.

Env vars (recommended):
  LEAGUE_ID   e.g. 508419792
  SEASON      e.g. 2025
  ESPN_SWID   optional; include braces, e.g. {ABCDEF12-....}
  ESPN_S2     optional; long cookie string

Outputs (JSON):
  fantasymanager25/docs/data/espn_mStandings.json
  fantasymanager25/docs/data/espn_mMatchup.json
  fantasymanager25/docs/data/espn_mRoster.json
  fantasymanager25/docs/data/espn_mTeam.json
  fantasymanager25/docs/data/espn_mSettings.json
  fantasymanager25/docs/data/espn_mMatchup_week_#.json  (best effort, 1..18)
  fantasymanager25/docs/data/espn_manifest.json
  fantasymanager25/docs/data/status.json
"""

from __future__ import annotations
import os, json, time, datetime, pathlib
import requests

# ---------- Config ----------
LEAGUE_ID = os.getenv("LEAGUE_ID", "508419792")
SEASON    = os.getenv("SEASON", "2025")

ROOT     = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "fantasymanager25" / "docs" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://fantasy.espn.com",
    "Referer": f"https://fantasy.espn.com/football/league?leagueId={LEAGUE_ID}",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

COOKIES = {}
if os.getenv("ESPN_SWID") and os.getenv("ESPN_S2"):
    COOKIES = {"SWID": os.getenv("ESPN_SWID"), "espn_s2": os.getenv("ESPN_S2")}

# ---------- Helpers ----------
def utcnow() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def write_json(path: pathlib.Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def fetch_view(session: requests.Session, view: str, extra_params: dict | None = None) -> dict:
    params = {"view": view}
    if extra_params:
        params.update(extra_params)
    r = session.get(BASE, headers=HEADERS, cookies=COOKIES, params=params, timeout=30, allow_redirects=True)
    r.raise_for_status()
    return r.json()

# ---------- Main ----------
def main() -> int:
    session = requests.Session()

    manifest = {
        "league_id": LEAGUE_ID,
        "season": SEASON,
        "generated_utc": utcnow(),
        "used_cookies": bool(COOKIES),
        "files": [],
        "errors": []
    }

    def save(name: str, data):
        out = DATA_DIR / name
        write_json(out, data)
        manifest["files"].append(name)
        print(f"✅ wrote {out}")

    core_views = ["mStandings", "mMatchup", "mRoster", "mTeam", "mSettings"]

    # Fetch core views
    for v in core_views:
        try:
            print(f"→ fetching {v}")
            data = fetch_view(session, v)
            # include timestamp to help the UI
            save(f"espn_{v}.json", {"fetched_at": utcnow(), "data": data})
            time.sleep(0.4)
        except Exception as e:
            err = f"{v}: {type(e).__name__}: {e}"
            manifest["errors"].append(err)
            print(f"⚠️  {err}")

    # Weekly matchup snapshots (best effort, not fatal if pre-season)
    weekly_ok = []
    for sp in range(1, 19):
        try:
            print(f"→ fetching mMatchup scoringPeriodId={sp}")
            data = fetch_view(session, "mMatchup", {"scoringPeriodId": sp})
            save(f"espn_mMatchup_week_{sp}.json", {"fetched_at": utcnow(), "data": data})
            weekly_ok.append(sp)
            time.sleep(0.3)
        except Exception as e:
            manifest["errors"].append(f"mMatchup_week_{sp}: {type(e).__name__}: {e}")

    manifest["weekly_matchup_weeks"] = weekly_ok
    write_json(DATA_DIR / "espn_manifest.json", manifest)

    # Status banner for the site
    note = "ESPN fetch OK" if manifest["files"] else "ESPN fetch failed: no files written"
    if manifest["errors"]:
        note = f"ESPN fetch partial: {len(manifest['errors'])} error(s)"
    status = {
        "generated_utc": utcnow(),
        "season": SEASON,
        "week": None,
        "notes": note
    }
    write_json(DATA_DIR / "status.json", status)

    print("———— done ————")
    print(json.dumps({"files": len(manifest["files"]), "errors": len(manifest["errors"])}, indent=2))
    # Never hard-fail the workflow on ESPN quirks; return 0.
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
