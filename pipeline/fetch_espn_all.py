import os
import sys
import json

# Add current folder (pipeline) to Python path so imports work
sys.path.append(os.path.dirname(__file__))

from fetch_espn_standings import fetch_espn_standings
from fetch_espn_scoreboard import fetch_espn_scoreboard
from fetch_status import fetch_status

# Define the correct data directory
DATA_DIR = os.path.join("fantasymanager25", "docs", "data")

# Make sure the folder exists
os.makedirs(DATA_DIR, exist_ok=True)

def save_json(filename, data):
    """Save data as JSON in the docs/data folder."""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved {filename} to {DATA_DIR}")

if __name__ == "__main__":
    print("📡 Fetching ESPN standings...")
    standings = fetch_espn_standings()
    save_json("espn_mStandings.json", standings)

    print("📡 Fetching ESPN scoreboard...")
    scoreboard = fetch_espn_scoreboard()
    save_json("espn_mScoreboard.json", scoreboard)

    print("📡 Fetching status data...")
    status = fetch_status()
    save_json("status.json", status)

    print("🎯 All data fetched and saved.")
