#!/usr/bin/env python3
"""
Build docs/data/team_rosters.json from ESPN mTeam + mRoster JSONs.
Input:
  docs/data/espn_mTeam.json
  docs/data/espn_mRoster.json
Output:
  docs/data/team_rosters.json
"""

import json
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("docs/data")

def load_json(p: Path):
    if not p.exists():
        raise FileNotFoundError(f"missing {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def main():
    teams_raw = load_json(DATA_DIR / "espn_mTeam.json")
    roster_raw = load_json(DATA_DIR / "espn_mRoster.json")

    # mTeam payload is under ["data"] for our fetcher
    teams = teams_raw.get("data", {}).get("teams", [])
    team_index = {t["id"]: t for t in teams}

    # mRoster payload is under ["data"]["teams"][i]["roster"]["entries"]
    out_rows = []
    for t in roster_raw.get("data", {}).get("teams", []):
        tid = t.get("id")
        tmeta = team_index.get(tid, {})
        tname = tmeta.get("name", f"Team {tid}")
        tabbrev = tmeta.get("abbrev", "")
        owner_id = (tmeta.get("primaryOwner") or "").strip("{}")
        owners = tmeta.get("owners") or []
        owner_ids = [o.strip("{}") for o in owners]

        entries = (t.get("roster") or {}).get("entries") or []
        players = []
        for e in entries:
            p = e.get("playerPoolEntry", {}).get("player", {})
            full = p.get("fullName") or p.get("name") or "Unknown"
            pos = ",".join(p.get("defaultPositionId", [])) if isinstance(p.get("defaultPositionId"), list) else p.get("defaultPositionId")
            # ESPN gives pro team & eligibleSlots in different places depending on season/schema
            pro_team = (p.get("proTeamId") if isinstance(p.get("proTeamId"), (int, str)) else p.get("proTeam")) or ""
            elig = p.get("eligibleSlots") or []
            players.append({
                "id": p.get("id"),
                "name": full,
                "pos": pos,
                "proTeam": pro_team,
                "eligible": elig,
            })

        out_rows.append({
            "team_id": tid,
            "team": tname,
            "abbrev": tabbrev,
            "owners": owner_ids or ([owner_id] if owner_id else []),
            "player_count": len(players),
            "players": players,
        })

    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count_teams": len(out_rows),
        "rows": out_rows,
        "source": ["espn_mTeam.json", "espn_mRoster.json"]
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with (DATA_DIR / "team_rosters.json").open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote {DATA_DIR / 'team_rosters.json'}")

if __name__ == "__main__":
    main()
