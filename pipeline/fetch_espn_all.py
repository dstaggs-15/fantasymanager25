#!/usr/bin/env python3
"""
Single-file ESPN fetcher (no intra-project imports).
Writes outputs to docs/data/ so GitHub Pages can serve them at:
https://<user>.github.io/fantasymanager25/data/<file>.json
"""

from __future__ import annotations
import os, json, time, datetime, pathlib
import requests

# ---------- Config from env with safe defaults ----------
LEAGUE_ID = os.getenv("LEAGUE_ID", "508419792")
SEASON    = os.getenv("SEASON", "2025")

# Repo root is parent of this file's folder (pipeline/)
ROOT     = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs" / "data"
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

# Optional cookies (only needed for private leagues)
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
        print(f"✅ wrote {out.relative_to(ROOT)}")

    core_views = ["mStandings", "mMatchup", "mRoster", "mTeam", "mSettings"]

    # Fetch core views
    for v in core_views:
        try:
            print(f"→ fetching {v}")
            data = fetch_view(session, v)
            save(f"espn_{v}.json", {"fetched_at": utcnow(), "data": data})
            time.sleep(0.35)
        except Exception as e:
            err = f"{v}: {type(e).__name__}: {e}"
            manifest["errors"].append(err)
            print(f"⚠️  {err}")

    # Weekly matchup snapshots (not fatal if pre-season)
    weekly_ok = []
    for sp in range(1, 19):
        try:
            print(f"→ fetching mMatchup scoringPeriodId={sp}")
            data = fetch_view(session, "mMatchup", {"scoringPeriodId": sp})
            save(f"espn_mMatchup_week_{sp}.json", {"fetched_at": utcnow(), "data": data})
            weekly_ok.append(sp)
            time.sleep(0.25)
        except Exception as e:
            manifest["errors"].append(f"mMatchup_week_{sp}: {type(e).__name__}: {e}")

    manifest["weekly_matchup_weeks"] = weekly_ok
    write_json(DATA_DIR / "espn_manifest.json", manifest)

    # Status banner for the UI
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
    # Do not fail the action on ESPN hiccups
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
