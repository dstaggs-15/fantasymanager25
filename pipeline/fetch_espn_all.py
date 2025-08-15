#!/usr/bin/env python3
"""
Robust ESPN fetcher for private leagues (runs on self-hosted runner).
- Reads SWID and ESPN_S2 from env (including braces in SWID).
- Uses real browser-like headers.
- Sends cookies via 'cookies={...}' (safer than raw Cookie header).
- Detects redirects to HTML and logs them.
- Writes JSON into docs/data/*.json
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

# --------- Config from env ----------
LEAGUE_ID = os.getenv("LEAGUE_ID", "").strip()
SEASON = os.getenv("SEASON", "").strip()
SWID = os.getenv("SWID", "").strip()
ESPN_S2 = os.getenv("ESPN_S2", "").strip()

OUT_DIR = os.path.join("docs", "data")

# --------- Utilities ----------
def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def ensure_outdir() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

def write_json(fname: str, obj: Dict[str, Any]) -> None:
    ensure_outdir()
    path = os.path.join(OUT_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def fail(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)

# --------- Validate env ----------
missing = []
if not LEAGUE_ID:
    missing.append("LEAGUE_ID")
if not SEASON:
    missing.append("SEASON")
if not SWID:
    missing.append("SWID")
if not ESPN_S2:
    missing.append("ESPN_S2")
if missing:
    fail(f"Missing required env: {', '.join(missing)}")

# ESPN requires SWID including braces. Quick sanity check:
if not (SWID.startswith("{") and SWID.endswith("}")):
    print("WARNING: SWID usually includes curly braces {…}. Your SWID does not.", file=sys.stderr)

# --------- HTTP session ----------
SESSION = requests.Session()
SESSION.headers.update({
    # Reasonable desktop UA:
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": f"https://fantasy.espn.com/football/league?leagueId={LEAGUE_ID}",
    "Connection": "keep-alive",
})

# Send cookies via requests' cookies arg, not a raw header string:
COOKIES = {
    "SWID": SWID,
    "espn_s2": ESPN_S2,
}

# --------- Endpoints ----------
BASE_V3 = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"

VIEWS = {
    "espn_mStandings.json": ["mStandings"],
    "espn_mTeam.json": ["mTeam"],
    "espn_mRoster.json": ["mRoster"],
    "espn_mSettings.json": ["mSettings"],
    "espn_mMatchup.json": ["mMatchup"],
}

# We’ll also try each matchup week, 1..18 (ESPN uses mMatchup + scoringPeriodId)
WEEKS = list(range(1, 19))

# --------- Core fetch ----------
def fetch_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 20) -> Dict[str, Any]:
    """
    Return dict with keys: ok(bool), status(int), type(str), json(obj|None), text_snippet(str|None), redirected(bool)
    """
    info: Dict[str, Any] = {
        "ok": False,
        "status": None,
        "type": None,
        "json": None,
        "text_snippet": None,
        "redirected": False,
    }
    try:
        # We want to detect redirects to login pages explicitly.
        r = SESSION.get(url, params=params or {}, cookies=COOKIES, timeout=timeout, allow_redirects=False)
        info["status"] = r.status_code
        ctype = r.headers.get("Content-Type", "")
        info["type"] = ctype

        # If ESPN tries to redirect to HTML, record it:
        if 300 <= r.status_code < 400:
            info["redirected"] = True
            # follow once to show what content-type looks like
            loc = r.headers.get("Location", "")
            r = SESSION.get(requests.compat.urljoin(url, loc), cookies=COOKIES, timeout=timeout)
            info["status"] = r.status_code
            info["type"] = r.headers.get("Content-Type", "")
            info["redirected"] = True

        if "application/json" in (info["type"] or "").lower():
            info["json"] = r.json()
            info["ok"] = True
        else:
            # Not JSON → stash a small snippet to debug
            text = r.text or ""
            info["text_snippet"] = text[:300].replace("\n", "\\n")
            info["ok"] = False
        return info
    except Exception as e:
        info["text_snippet"] = f"EXC: {type(e).__name__}: {e}"
        info["ok"] = False
        return info

def fetch_view(view_name: str) -> Dict[str, Any]:
    url = BASE_V3
    params = {"view": view_name}
    return fetch_json(url, params=params)

def fetch_week(view_name: str, week: int) -> Dict[str, Any]:
    url = BASE_V3
    params = {"view": view_name, "scoringPeriodId": week}
    return fetch_json(url, params=params)

# --------- Main ----------
def main() -> int:
    ensure_outdir()

    manifest = {
        "league_id": LEAGUE_ID,
        "season": SEASON,
        "generated_utc": utcnow(),
        "probe": {},
        "errors": [],
        "wrote": [],
    }

    # Probe: simple call to mStandings
    probe = fetch_view("mStandings")
    manifest["probe"]["mStandings"] = {
        "ok": probe["ok"],
        "status": probe["status"],
        "type": probe["type"],
        "redirected": probe["redirected"],
        "has_json": probe["json"] is not None,
        "snippet": probe["text_snippet"],
    }
    write_json("espn_probe.json", manifest["probe"])

    # Save each primary view
    for fname, views in VIEWS.items():
        results = []
        ok_any = False
        for v in views:
            res = fetch_view(v)
            results.append({k: res[k] for k in ("ok", "status", "type", "redirected")})
            if res["ok"] and isinstance(res["json"], dict):
                write_json(fname, res["json"])
                manifest["wrote"].append(fname)
                ok_any = True
                break  # one good result is enough
        if not ok_any:
            manifest["errors"].append(f"{fname}: Non-JSON or failed. probe={results} (see espn_probe.json)")

        time.sleep(0.8)  # be polite

    # Matchup per week
    for wk in WEEKS:
        res = fetch_week("mMatchup", wk)
        fname = f"espn_mMatchup_week_{wk}.json"
        if res["ok"] and isinstance(res["json"], dict):
            write_json(fname, res["json"])
            manifest["wrote"].append(fname)
        else:
            manifest["errors"].append(
                f"{fname}: status={res['status']} type={res['type']} redirected={res['redirected']} "
                f"snippet={res['text_snippet']}"
            )
        time.sleep(0.5)

    # Final manifest
    write_json("espn_manifest.json", manifest)

    # If nothing at all worked, signal error (so you notice in Actions)
    if not manifest["wrote"]:
        write_json("status.json", {
            "generated_utc": utcnow(),
            "season": SEASON,
            "notes": f"ESPN fetch failed — see espn_probe.json and espn_manifest.json",
        })
        print("ERROR: No JSON files written. See espn_probe.json / espn_manifest.json details.")
        return 2

    # Success-ish
    write_json("status.json", {
        "generated_utc": utcnow(),
        "season": SEASON,
        "notes": f"Wrote {len(manifest['wrote'])} files",
    })
    print(f"OK: wrote {len(manifest['wrote'])} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
