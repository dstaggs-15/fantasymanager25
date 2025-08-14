#!/usr/bin/env python3
from __future__ import annotations
import json, pathlib, datetime

ROOT     = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs" / "data"

def utcnow() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def read_json(name: str):
    path = DATA_DIR / name
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def stat_map(stats):
    """Return dict of last known totals: actual and projected."""
    actual_total = None
    proj_total   = None
    if isinstance(stats, list):
        # ESPN uses statSourceId 0 = actuals, 1 = projections
        for s in stats:
            ss = s.get("statSourceId")
            val = s.get("appliedTotal")
            if ss == 0:
                actual_total = val if val is not None else actual_total
            elif ss == 1:
                proj_total = val if val is not None else proj_total
    return {
        "actual": float(actual_total) if actual_total is not None else None,
        "projected": float(proj_total) if proj_total is not None else None,
    }

def main() -> int:
    roster_raw = read_json("espn_mRoster.json")
    team_raw   = read_json("espn_mTeam.json")

    if not roster_raw or not team_raw:
        out = {"generated_utc": utcnow(), "teams": [], "error": "missing espn_mRoster.json or espn_mTeam.json"}
        (DATA_DIR / "team_rosters.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        print("⚠️ team_rosters.json written empty (missing source files)")
        return 0

    # ESPN payload is wrapped under {"data": ...}
    roster_data = (roster_raw.get("data") or roster_raw) if isinstance(roster_raw, dict) else roster_raw
    team_data   = (team_raw.get("data") or team_raw) if isinstance(team_raw, dict) else team_raw

    # Build teamId -> teamName
    team_entries = team_data.get("teams") or []
    team_name_by_id = {}
    for t in team_entries:
        tid = t.get("id")
        name = (
            t.get("location","").strip() + " " + t.get("nickname","").strip()
            if (t.get("location") or t.get("nickname")) else t.get("name") or t.get("abbrev") or f"Team {tid}"
        ).strip()
        team_name_by_id[tid] = name

    # Build rosters
    # roster_data usually has "teams": [ { id, roster: { entries: [...] } } ]
    teams_out = []
    for t in (roster_data.get("teams") or []):
        tid = t.get("id")
        tname = team_name_by_id.get(tid, f"Team {tid}")
        entries = (((t.get("roster") or {}).get("entries")) or [])
        players = []
        for e in entries:
            p = (e.get("playerPoolEntry") or {}).get("player") or e.get("player") or {}
            # name + basics
            full = p.get("fullName") or p.get("name") or "—"
            posid = p.get("defaultPositionId")
            pos = {
                0:"Quarterback",1:"Running Back",2:"Wide Receiver",3:"Tight End",4:"Kicker",5:"Defense/Special Teams",
                16:"Defensive Tackle",17:"Defensive End",18:"Linebacker",19:"Cornerback",20:"Safety"
            }.get(posid, "Unknown")
            nfl = p.get("proTeamAbbreviation") or p.get("proTeam") or p.get("proTeamId") or "—"

            smap = stat_map(p.get("stats") or [])
            players.append({
                "name": full,
                "position": pos,
                "nfl": nfl,
                "projected": smap["projected"],
                "actual": smap["actual"],
            })

        teams_out.append({
            "teamId": tid,
            "teamName": tname,
            "players": players
        })

    out = {"generated_utc": utcnow(), "teams": teams_out}
    (DATA_DIR / "team_rosters.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"✅ team_rosters.json teams={len(teams_out)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
