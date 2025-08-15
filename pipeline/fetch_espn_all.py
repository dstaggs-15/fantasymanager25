#!/usr/bin/env python3
"""
Robust ESPN fetcher for private leagues (runs on self-hosted runner).
- Accepts SWID secrets as either SWID or ESPN_SWID, and s2 as ESPN_S2 or S2.
- Uses browser-like headers + cookies param (not raw Cookie header).
- Detects redirects/HTML and logs a probe.
- Writes JSON into docs/data/*.json
"""

import json, os, sys, time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import requests

# --------- helpers ----------
def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def getenv_any(*names: str, default: str = "") -> str:
    for n in names:
        v = os.getenv(n)
        if v and v.strip():
            return v.strip()
    return default

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def write_json(path: str, obj: Dict[str, Any]):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

# --------- config ----------
OUT_DIR = "docs/data"

LEAGUE_ID = getenv_any("LEAGUE_ID")
SEASON    = getenv_any("SEASON")
# Accept both naming schemes
SWID      = getenv_any("SWID", "ESPN_SWID")
ESPN_S2   = getenv_any("ESPN_S2", "S2")

missing = [k for k,v in [("LEAGUE_ID",LEAGUE_ID), ("SEASON",SEASON), ("SWID",SWID), ("ESPN_S2",ESPN_S2)] if not v]
if missing:
    print(f"Missing required env: {', '.join(missing)}", file=sys.stderr)
    sys.exit(1)

# normalize SWID braces
if not (SWID.startswith("{") and SWID.endswith("}")):
    SWID = "{" + SWID.strip("{}") + "}"

# ESPN endpoints (reads cluster is sometimes friendlier)
BASE_V3 = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"

# --------- session ----------
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://fantasy.espn.com",
    "Referer": f"https://fantasy.espn.com/football/league?leagueId={LEAGUE_ID}",
    "Connection": "keep-alive",
})
COOKIES = {"SWID": SWID, "espn_s2": ESPN_S2}

def fetch_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 25) -> Dict[str, Any]:
    info: Dict[str, Any] = {"ok": False, "status": None, "type": None, "json": None, "snippet": None, "redirected": False}
    try:
        r = SESSION.get(url, params=params or {}, cookies=COOKIES, timeout=timeout, allow_redirects=False)
        info["status"] = r.status_code
        info["type"] = (r.headers.get("Content-Type") or "")
        if 300 <= r.status_code < 400:
            info["redirected"] = True
            loc = r.headers.get("Location","")
            r = SESSION.get(requests.compat.urljoin(url, loc), cookies=COOKIES, timeout=timeout)
            info["status"] = r.status_code
            info["type"] = (r.headers.get("Content-Type") or "")
        if "json" in info["type"].lower():
            info["json"] = r.json()
            info["ok"] = True
        else:
            info["snippet"] = (r.text or "")[:300].replace("\n"," ")
    except Exception as e:
        info["snippet"] = f"EXC {type(e).__name__}: {e}"
    return info

def main() -> int:
    ensure_dir(OUT_DIR)
    views = ["mStandings","mTeam","mRoster","mSettings","mMatchup"]
    wrote, errors = [], {}

    # Probe first
    probe = fetch_json(BASE_V3, {"view":"mStandings"})
    write_json(f"{OUT_DIR}/espn_probe.json", {
        "generated_utc": utcnow(),
        "url": BASE_V3,
        "status": probe["status"],
        "type": probe["type"],
        "redirected": probe["redirected"],
        "ok": probe["ok"],
        "snippet": probe["snippet"],
    })

    # Core views
    for v in views:
        res = fetch_json(BASE_V3, {"view": v})
        fname = f"{OUT_DIR}/espn_{v}.json"
        if res["ok"] and isinstance(res["json"], dict):
            write_json(fname, {"fetched_at": utcnow(), "data": res["json"]})
            wrote.append(fname)
        else:
            write_json(fname, {"fetched_at": utcnow(), "error": f"status={res['status']} type={res['type']} redir={res['redirected']} snip={res['snippet']}"})
            errors[f"espn_{v}.json"] = res

        time.sleep(0.5)

    # Weeks 1..18
    for wk in range(1,19):
        res = fetch_json(BASE_V3, {"view":"mMatchup", "scoringPeriodId": wk})
        fname = f"{OUT_DIR}/espn_mMatchup_week_{wk}.json"
        if res["ok"] and isinstance(res["json"], dict):
            write_json(fname, {"fetched_at": utcnow(), "data": res["json"]})
            wrote.append(fname)
        else:
            write_json(fname, {"fetched_at": utcnow(), "error": f"status={res['status']} type={res['type']} redir={res['redirected']} snip={res['snippet']}"})

        time.sleep(0.35)

    # Manifest + status
    write_json(f"{OUT_DIR}/espn_manifest.json", {
        "league_id": LEAGUE_ID, "season": SEASON, "generated_utc": utcnow(),
        "wrote": wrote, "error_count": len(errors), "probe_ok": probe["ok"]
    })
    write_json(f"{OUT_DIR}/status.json", {
        "generated_utc": utcnow(), "season": SEASON,
        "notes": f"Wrote {len(wrote)} files; probe_ok={probe['ok']}"
    })

    # non-zero exit on total failure to get your attention
    return 0 if wrote else 2

if __name__ == "__main__":
    sys.exit(main())
