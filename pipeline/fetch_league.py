#!/usr/bin/env python3
"""
Robust league fetcher for ESPN (mTeam + mRoster).

Env required:
  LEAGUE_ID   e.g. 508419792
  SEASON      e.g. 2025 (defaults to 2025 if unset)
  SWID        {with-braces}
  ESPN_S2     long token

Writes (under docs/data/):
  espn_mTeam.json, espn_mRoster.json    (raw)
  team_rosters.json, players_summary.json (site-ready)
"""

import json, os, sys, time, random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

# -------- helpers --------

def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def env_required(key: str) -> str:
    val = os.environ.get(key, "").strip()
    if not val:
        print(f"Missing required env: {key}", file=sys.stderr)
        sys.exit(1)
    return val

def safe_write(path: str, obj: Any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

# -------- request plumbing (hardened) --------

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    s.timeout = 30
    return s

def is_json_response(r: requests.Response) -> bool:
    ctype = r.headers.get("content-type", "")
    return "application/json" in ctype

def get_league_json(session: requests.Session, base_url: str, view: str,
                    cookies: Dict[str, str], cookie_header: str,
                    scoring_period: Optional[int] = None,
                    tries: int = 6) -> Dict[str, Any]:
    """
    Try multiple ways to pull JSON:
      1) normal params + cookies dict
      2) explicit Cookie header + params
      3) raw URL with query string (no params dict)
    Backoff with jitter between attempts.
    """
    referer = f"https://fantasy.espn.com/football/league?leagueId={LEAGUE_ID}"
    session.headers["Referer"] = referer

    last_err: Optional[Exception] = None
    for attempt in range(1, tries + 1):
        # jittered backoff after the first try
        if attempt > 1:
            sleep = min(2.0 * attempt, 8.0) + random.uniform(0, 0.75)
            time.sleep(sleep)

        try:
            # ---- style A: params + cookies dict
            params = {"view": view}
            if scoring_period is not None:
                params["scoringPeriodId"] = scoring_period
            r = session.get(base_url, params=params, cookies=cookies, timeout=30)
            if is_json_response(r):
                return r.json()

            # ---- style B: params + explicit Cookie header (keep cookies dict too)
            hdrs = session.headers.copy()
            hdrs["Cookie"] = cookie_header
            r = session.get(base_url, params=params, cookies=cookies, headers=hdrs, timeout=30)
            if is_json_response(r):
                return r.json()

            # ---- style C: fully composed URL string, explicit Cookie header
            qs = f"view={view}"
            if scoring_period is not None:
                qs += f"&scoringPeriodId={scoring_period}"
            url_full = f"{base_url}?{qs}"
            r = session.get(url_full, headers=hdrs, timeout=30)
            if is_json_response(r):
                return r.json()

            last_err = RuntimeError(f"Non-JSON (content-type={r.headers.get('content-type','')})")

        except Exception as e:
            last_err = e

    raise RuntimeError(f"{view} failed after {tries} tries: {last_err}")

# -------- shaping --------

def flatten_players_from_roster(mroster: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    teams = mroster.get("teams", [])
    pos_map = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "D/ST"}

    # Primary path: teams[*].roster.entries[*].playerPoolEntry.player
    for t in teams:
        team_id = t.get("id")
        team_name = t.get("name") or f"Team {team_id}"
        entries = (t.get("roster") or {}).get("entries", []) or []
        for e in entries:
            p = (e.get("playerPoolEntry") or {}).get("player", {})
            if not p:
                continue
            rows.append({
                "id": p.get("id"),
                "name": p.get("fullName") or p.get("name") or "Unknown",
                "pos": pos_map.get(p.get("defaultPositionId"), str(p.get("defaultPositionId"))),
                "proTeam": p.get("proTeamId"),
                "teamId": team_id,
                "team": team_name,
            })

    # Fallback: some responses include a top-level "players" list
    if not rows and isinstance(mroster.get("players"), list):
        for pe in mroster["players"]:
            p = pe.get("player", {})
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
    team_index: Dict[int, Dict[str, Any]] = {}
    for t in mteam.get("teams", []):
        tid = t.get("id")
        team_index[tid] = {
            "id": tid,
            "name": t.get("name"),
            "logo": t.get("logo"),
            "owners": t.get("owners", []),
            "roster_count": 0,
            "players": [],
        }

    for t in mroster.get("teams", []):
        tid = t.get("id")
        target = team_index.get(tid)
        if not target:
            target = {
                "id": tid,
                "name": t.get("name"),
                "logo": t.get("logo"),
                "owners": t.get("owners", []),
                "roster_count": 0,
                "players": [],
            }
            team_index[tid] = target

        entries = (t.get("roster") or {}).get("entries", []) or []
        target["roster_count"] = len(entries)
        for e in entries:
            p = (e.get("playerPoolEntry") or {}).get("player", {})
            if not p:
                continue
            target["players"].append({
                "id": p.get("id"),
                "name": p.get("fullName") or p.get("name"),
                "posId": p.get("defaultPositionId"),
                "proTeamId": p.get("proTeamId"),
            })

    teams_sorted = sorted(team_index.values(), key=lambda x: (x["id"] or 0))
    return {"generated_utc": utcnow_iso(), "teams": teams_sorted}

# -------- main --------

def main() -> int:
    global LEAGUE_ID  # used for referer building
    LEAGUE_ID = int(env_required("LEAGUE_ID"))
    season = int(os.environ.get("SEASON", "2025").strip() or "2025")
    swid = env_required("SWID")
    s2 = env_required("ESPN_S2")

    base = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{LEAGUE_ID}"
    cookies = {"SWID": swid, "espn_s2": s2}
    cookie_header = f"SWID={swid}; espn_s2={s2}"

    sess = build_session()

    # Pull views with resilient method
    mteam = get_league_json(sess, base, "mTeam", cookies, cookie_header)
    # scoringPeriodId=0 is the safest for preseason/anytime rosters
    mroster = get_league_json(sess, base, "mRoster", cookies, cookie_header, scoring_period=0)

    # Write raw
    outdir = "docs/data"
    safe_write(f"{outdir}/espn_mTeam.json", {"fetched_at": utcnow_iso(), "data": mteam})
    safe_write(f"{outdir}/espn_mRoster.json", {"fetched_at": utcnow_iso(), "data": mroster})

    # Build site files
    team_rosters = build_team_rosters(mteam, mroster)
    safe_write(f"{outdir}/team_rosters.json", team_rosters)

    rows = flatten_players_from_roster(mroster)
    players_summary = {
        "generated_utc": utcnow_iso(),
        "count": len(rows),
        "rows": rows,
        "source": "espn mRoster",
    }
    safe_write(f"{outdir}/players_summary.json", players_summary)

    print(f"Wrote {len(team_rosters['teams'])} teams; {players_summary['count']} players.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        safe_write("docs/data/fetch_league_error.json", {
            "generated_utc": utcnow_iso(),
            "error": repr(e),
        })
        print(f"fetch_league ERROR: {e}", file=sys.stderr)
        sys.exit(2)
