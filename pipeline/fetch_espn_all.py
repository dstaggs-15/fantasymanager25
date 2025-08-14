#!/usr/bin/env python3
from __future__ import annotations
import os, json, datetime, time, pathlib, requests, traceback

LEAGUE_ID = os.getenv("LEAGUE_ID", "508419792")
SEASON    = os.getenv("SEASON", "2025")

ROOT     = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
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

def fetch_view_once(session: requests.Session, view: str, extra_params: dict | None = None):
    params = {"view": view}
    if extra_params:
        params.update(extra_params)
    r = session.get(BASE, headers=HEADERS, cookies=COOKIES, params=params, timeout=30)
    info = {
        "status_code": r.status_code,
        "content_type": (r.headers.get("content-type") or "").lower(),
        "url": r.url
    }
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code} for {view}: {info}")
    if "json" not in info["content_type"]:
        snippet = r.text[:240].replace("\n", " ")
        raise RuntimeError(f"Non-JSON (content-type={info['content_type']}), snippet={snippet}")
    return r.json()

def safe_fetch_view(session: requests.Session, view: str, extra_params: dict | None = None, tries: int = 3, delay: float = 0.6):
    last_err = None
    for i in range(tries):
        try:
            return fetch_view_once(session, view, extra_params)
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            time.sleep(delay * (i + 1))
    # all retries failed
    raise RuntimeError(last_err or f"{view} failed")

def main() -> int:
    s = requests.Session()
    manifest = {"league_id": LEAGUE_ID, "season": SEASON, "generated_utc": utcnow(), "files": [], "errors": []}

    def save_ok(name: str, data):
        out = DATA_DIR / name
        write_json(out, {"fetched_at": utcnow(), "data": data})
        manifest["files"].append(name)

    def save_err(name: str, err_msg: str):
        out = DATA_DIR / name
        write_json(out, {"fetched_at": utcnow(), "error": err_msg})
        manifest["errors"].append(f"{name}: {err_msg}")

    views = ["mStandings", "mMatchup", "mRoster", "mTeam", "mSettings"]
    for v in views:
        fname = f"espn_{v}.json"
        try:
            data = safe_fetch_view(s, v)
            save_ok(fname, data)
        except Exception as e:
            save_err(fname, f"{type(e).__name__}: {e}")
        time.sleep(0.3)

    # Weekly snapshots (don’t fail; still write files with error on miss)
    for sp in range(1, 19):
        fname = f"espn_mMatchup_week_{sp}.json"
        try:
            data = safe_fetch_view(s, "mMatchup", {"scoringPeriodId": sp})
            save_ok(fname, data)
        except Exception as e:
            save_err(fname, f"{type(e).__name__}: {e}")
        time.sleep(0.2)

    # Status + manifest
    write_json(DATA_DIR / "espn_manifest.json", manifest)
    note = "ESPN fetch OK" if manifest["files"] else "ESPN fetch failed (see espn_manifest.json)"
    if manifest["errors"]:
        note = f"ESPN fetch partial: {len(manifest['errors'])} error(s)"
    write_json(DATA_DIR / "status.json", {"generated_utc": utcnow(), "season": SEASON, "week": None, "notes": note})

    print(json.dumps({"files_written": len(manifest["files"]), "errors": len(manifest["errors"])}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
