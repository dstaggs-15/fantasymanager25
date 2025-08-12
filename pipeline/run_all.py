#!/usr/bin/env python3
import json, os, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
data_dir = ROOT / "docs" / "data"
data_dir.mkdir(parents=True, exist_ok=True)

status = {
    "generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "season": os.getenv("SEASON", None),
    "week": os.getenv("WEEK", None),
    "notes": "Heartbeat OK (no football logic yet)."
}

with open(data_dir / "status.json", "w", encoding="utf-8") as f:
    json.dump(status, f, indent=2)

print("Wrote docs/data/status.json")
