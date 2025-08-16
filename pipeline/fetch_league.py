#!/usr/bin/env python3
"""
Resilient ESPN league fetcher.

Requires env:
  LEAGUE_ID, SEASON (default 2025), SWID, ESPN_S2

Writes (under docs/data/):
  espn_mTeam.json, espn_mRoster.json (raw wraps)
  team_rosters.json, players_summary.json (site files)
  _last_attempt.json (tiny debug snapshot)
"""

import json, os, sys, time, random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

# ---------- misc helpers ----------

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def need(k: str) -> str:
    v = os.environ.get(k, "").strip()
    if not v:
        print(f"Missing required env: {k}", file=sys.stderr)
        sys.exit(1)
    return v

def write_json(path: str, obj: Any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

# ---------- HTTP plumbing ----------

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "Chrome/126.0.0.0 Safari/537.36")

BASE_HOSTS = [
    "fantasy.espn.com",            # primary
    "lm-api-reads.fantasy.espn.com" # read-only edge that often bypasses HTML wall
]

COMMON_HEADERS = {
    "User-Agent": UA,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    # extra browser-ish hints
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "DNT": "1",
}

def is_json(r: requests.Response) -> bool:
    return "application/json" in r.headers.get("content-type", "").lower()

def build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(COMMON_HEADERS)
    s.timeout = 30
    return s

def warmup(sess: requests.Session, league_id: int, cookies_dict: Dict[str,str], cookie_header: str):
    """
    Hit the public league page first. This often 'keys' Akamai/Cloudflare on our session.
    """
    url = f"https://fantasy.espn.com/football/league?leagueId={league_id}"
    hdrs = sess.headers.copy()
    hdrs["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    hdrs["Cookie"] = cookie_header
    try:
        r = sess.get(url, headers=hdrs, cookies=cookies_dict, timeout=20)
        # ignore body; just trying to set edge state
        time.sleep(0.8 + random.random() * 0.6)  # small human-ish pause
    except Exception:
        pass

def backoff(attempt: int):
    # 1.0s, 2.0s, 3.0s ... with jitter
    time.sleep(min(1.0 * attempt, 6.0) + random.uniform(0.0, 0.75))

def get_view(sess: requests.Session, host: str, season: int, league_id: int, view: str,
             cookies_dict: Dict[str,str], cookie_header: str,
             scoring_period: Optional[int] = None) -> Dict[str, Any]:
    """
    Try three request styles against a specific host.
    """
    base = f"https://{host}/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"
    referer = f"https://fantasy.espn.com/football/league?leagueId={league_id}"
    sess.headers["Referer"] = referer

    params = {"view": view}
    if scoring_period is not None:
        params["scoringPeriodId"] = scoring_period

    # A) standard params + cookies dict
    r = sess.get(base, params=params, cookies=cookies_dict, timeout=30)
    if is_json(r):
        return r.json()

    # B) same but force Cookie header too
    hdrs = sess.headers.copy()
    hdrs["Cookie"] = cookie_header
    r = sess.get(base, params=params, cookies=cookies_dict, headers=hdrs, timeout=30)
    if is_json(r):
        return r.json()

    # C) fully composed URL (no params dict), explicit Cookie header
    qs = f"view={view}"
    if scoring_period is not None:
        qs += f"&scoringPeriodId={scoring_period}"
    r = sess.get(f"{base}?{qs}", headers=hdrs, timeout=30)
    if is_json(r):
        return r.json()

    raise RuntimeError(f"Non-JSON (content-type={r.headers.get('content-type','')})")

def fetch_view_resilient(sess: requests.Session, season: int, league_id: int, view: str,
                         cookies_dict: Dict[str,str], cookie_header: str,
                         scoring_period: Optional[int] = None,
                         tries: int = 8) -> Dict[str, Any]:
    """
    Multi-host + multi-style; backoff with jitter.
    """
    last_err: Optional[Exception] = None
    for attempt in range(1, tries + 1):
        for host in BASE_HOSTS:
            try:
                return get_view(sess, host, season, league_id, view,
                                cookies_dict, cookie_header, scoring_period)
            except Exception as e:
                last_err = e
        backoff(attempt)
    raise RuntimeError(f"{view} failed after {tries} tries: {last_err}")

# ---------- shaping ----------

def rows_from_mroster(mroster: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    teams = mroster.get("teams", [])
    pos_map = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "D/ST"}
    for t in teams:
        tid = t.get("id")
        tname = t.get("name") or f"Team {tid}"
        entries = (t.get("roster") or {}).get("entries", []) or []
        for e in entries:
            p = (e.get("playerPoolEntry") or {}).get("player", {}) or {}
            if not p: 
                continue
            rows.append({
                "id": p.get("id"),
                "name": p.get("fullName") or p.get("name") or "Unknown",
                "pos": pos_map.get(p.get("defaultPositionId"), str(p.get("defaultPositionId"))),
                "proTeam": p.get("proTeamId"),
                "teamId": tid,
                "team": tname,
            })
    # fallback if some edge returns top-level players list
    if not rows and isinstance(mroster.get("players"), list):
        for pe in mroster["players"]:
            p = pe.get("player", {}) or {}
            if not p:
                continue
            rows.append({
                "id": p.get("id"),
                "name": p.get("fullName") or p.get("name") or "Unknown",
                "pos": pos_map.get(p.get("defaultPositionId"), str(p.get("defaultPositionId"))),
                "proTeam": p.get("proTeamId"),
                "teamId": None,
                "team": None,
            })
    return rows

def build_team_rosters(mteam: Dict[str, Any], mroster: Dict[str, Any]) -> Dict[str, Any]:
    index: Dict[int, Dict[str, Any]] = {}
    for t in mteam.get("teams", []):
        tid = t.get("id")
        index[tid] = {
            "id": tid, "name": t.get("name"), "logo": t.get("logo"),
            "owners": t.get("owners", []), "players": [], "roster_count": 0,
        }
    for t in mroster.get("teams", []):
        tid = t.get("id")
        target = index.setdefault(tid, {
            "id": tid, "name": t.get("name"), "logo": t.get("logo"),
            "owners": t.get("owners", []), "players": [], "roster_count": 0,
        })
        entries = (t.get("roster") or {}).get("entries", []) or []
        target["roster_count"] = len(entries)
        for e in entries:
            p = (e.get("playerPoolEntry") or {}).get("player", {}) or {}
            if not p: 
                continue
            target["players"].append({
                "id": p.get("id"),
                "name": p.get("fullName") or p.get("name"),
                "posId": p.get("defaultPositionId"),
                "proTeamId": p.get("proTeamId"),
            })
    teams_sorted = sorted(index.values(), key=lambda x: (x["id"] or 0))
    return {"generated_utc": now_iso(), "teams": teams_sorted}

# ---------- main ----------

def main() -> int:
    league_id = int(need("LEAGUE_ID"))
    season = int(os.environ.get("SEASON", "2025").strip() or "2025")
    swid = need("SWID")               # must include braces {}
    s2 = need("ESPN_S2")

    outdir = "docs/data"
    cookies_dict = {"SWID": swid, "espn_s2": s2}
    cookie_header = f"SWID={swid}; espn_s2={s2}"

    sess = build_session()

    # Warm up the session once per run
    warmup(sess, league_id, cookies_dict, cookie_header)

    # Pull views with multi-host fallback
    mteam_wrap = {}
    mroster_wrap = {}
    debug = {"started": now_iso(), "steps": []}

    try:
        mteam = fetch_view_resilient(sess, season, league_id, "mTeam",
                                     cookies_dict, cookie_header,
                                     scoring_period=None, tries=8)
        mteam_wrap = {"fetched_at": now_iso(), "data": mteam}
        write_json(f"{outdir}/espn_mTeam.json", mteam_wrap)
        debug["steps"].append({"mTeam": "ok"})
    except Exception as e:
        debug["steps"].append({"mTeam": f"error: {e}"})
        raise

    # scoringPeriodId=0 tends to work for rosters pre-season/anytime
    try:
        mroster = fetch_view_resilient(sess, season, league_id, "mRoster",
                                       cookies_dict, cookie_header,
                                       scoring_period=0, tries=8)
        mroster_wrap = {"fetched_at": now_iso(), "data": mroster}
        write_json(f"{outdir}/espn_mRoster.json", mroster_wrap)
        debug["steps"].append({"mRoster": "ok"})
    except Exception as e:
        debug["steps"].append({"mRoster": f"error: {e}"})
        raise

    # Site files
    team_rosters = build_team_rosters(mteam_wrap.get("data", {}), mroster_wrap.get("data", {}))
    write_json(f"{outdir}/team_rosters.json", team_rosters)

    rows = rows_from_mroster(mroster_wrap.get("data", {}))
    players_summary = {
        "generated_utc": now_iso(),
        "count": len(rows),
        "rows": rows,
        "source": "espn mRoster",
    }
    write_json(f"{outdir}/players_summary.json", players_summary)

    debug["finished"] = now_iso()
    debug["players_count"] = len(rows)
    debug["teams_count"] = len(team_rosters.get("teams", []))
    write_json(f"{outdir}/_last_attempt.json", debug)

    print(f"OK: {debug['teams_count']} teams; {debug['players_count']} players")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        # ensure we leave breadcrumbs even on hard fail
        write_json("docs/data/_last_attempt.json",
                   {"ended": now_iso(), "fatal": repr(e)})
        print(f"fetch_league ERROR: {e}", file=sys.stderr)
        sys.exit(2)
