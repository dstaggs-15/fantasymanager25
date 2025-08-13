#!/usr/bin/env python3
"""
Minimal heartbeat pipeline.
- Ensures /docs/data exists
- Writes status.json with UTC timestamp
- Writes latest.json with dummy league table
"""

import json, pathlib, datetime, os, random

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
DATA.mkdir(parents=True, exist_ok=True)

# 1) status.json
status = {
    "generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "season": os.getenv("SEASON") or None,
    "week": os.getenv("WEEK") or None,
    "notes": "Heartbeat OK",
}
(DATA / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")

# 2) latest.json (dummy standings so the page shows real rows)
teams = [
    {"team": "Duloc Gingerbread Men", "wins": 2, "losses": 1, "pointsFor": 296, "pointsAgainst": 274},
    {"team": "Far Far Away Knights", "wins": 2, "losses": 1, "pointsFor": 281, "pointsAgainst": 263},
    {"team": "Dragon’s Lair", "wins": 1, "losses": 2, "pointsFor": 248, "pointsAgainst": 302},
]
# add tiny randomness so commits actually change
for t in teams:
    t["pointsFor"] += random.randint(0, 1)
    t["pointsAgainst"] += random.randint(0, 1)

(DATA / "latest.json").write_text(json.dumps(teams, indent=2), encoding="utf-8")

print("✅ Wrote docs/data/status.json and docs/data/latest.json")
