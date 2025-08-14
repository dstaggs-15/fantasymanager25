import requests
import json
import os
from datetime import datetime

# ====== SETTINGS ======
LEAGUE_ID = 508419792  # Your league ID
YEAR = 2025
BASE_URL = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{YEAR}/segments/0/leagues/{LEAGUE_ID}"
VIEWS = ["mStandings", "mMatchup", "mRoster", "mTeam", "mSettings"]

# Output folder (same as your /data directory in repo)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Make sure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_view(view):
    url = f"{BASE_URL}?view={view}"
    print(f"Fetching {view} ... {url}")
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Error fetching {view}: {resp.status_code}")
        return None
    return resp.json()

def save_json(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {filename}")

if __name__ == "__main__":
    timestamp = datetime.utcnow().isoformat() + "Z"
    for view in VIEWS:
        data = fetch_view(view)
        if data:
            save_json(f"espn_{view}.json", {"fetched_at": timestamp, "data": data})

    print("All ESPN data views fetched and saved.")
