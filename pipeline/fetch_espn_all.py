import os
import json
from pipeline.fetch_espn_standings import fetch_espn_standings

# Always save data to the /docs/data folder at repo root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "docs", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Fetch ESPN standings
standings = fetch_espn_standings()

# Save standings JSON
standings_file = os.path.join(DATA_DIR, "espn_mStandings.json")
with open(standings_file, "w") as f:
    json.dump(standings, f, indent=2)

# Save status JSON
status_file = os.path.join(DATA_DIR, "status.json")
status_data = {
    "last_update": standings.get("last_update", None)
}
with open(status_file, "w") as f:
    json.dump(status_data, f, indent=2)

print(f"✅ Data saved to {DATA_DIR}")
