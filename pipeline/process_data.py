import json
import os
import time

DATA_DIR = 'docs/data'

# --- Data Processing Functions ---
def process_rosters(roster_data):
    """Processes raw mRoster data into the format the website expects."""
    teams_processed = {}
    for team in roster_data.get('teams', []):
        team_id = team['id']
        teams_processed[team_id] = {
            'teamName': team.get('name', 'Unknown Team'),
            'players': [player['playerPoolEntry']['player']['fullName'] for player in team.get('roster', {}).get('entries', [])]
        }
    return {"teams": teams_processed, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

def process_players(player_data):
    """Processes raw players_wl data into a clean list for the website."""
    players_processed = []
    position_map = {0: 'TQB', 1: 'QB', 2: 'RB', 3: 'WR', 4: 'TE', 5: 'K', 16: 'D/ST'}
    for player_entry in player_data.get('players', []):
        player = player_entry.get('player', {})
        if not player or not player.get('proTeamAbbr'):
            continue
        players_processed.append({
            'id': player.get('id'),
            'name': player.get('fullName'),
            'pos': position_map.get(player.get('defaultPositionId'), 'N/A'),
            'team': player.get('proTeamAbbr', 'FA')
        })
    return players_processed

# --- Main Execution ---
def main():
    print("--- Starting Data Processing ---")
    
    # Files to read from the fetcher script
    raw_files = {
        "mTeam": "raw_mTeam.json",
        "mRoster": "raw_mRoster.json",
        "players_wl": "raw_players.json"
    }
    
    # Load all raw data first
    raw_data = {}
    for key, filename in raw_files.items():
        try:
            with open(os.path.join(DATA_DIR, filename), 'r') as f:
                raw_data[key] = json.load(f)
        except FileNotFoundError:
            print(f"::error::Raw file not found: {filename}. The fetching script may have failed.")
            return
        except json.JSONDecodeError:
            print(f"::error::Could not decode JSON from {filename}. It may be empty or malformed.")
            return

    # Process and save the final, clean files
    print("Processing and saving final files for the website...")
    
    # 1. Process and save rosters
    processed_rosters = process_rosters(raw_data['mRoster'])
    with open(os.path.join(DATA_DIR, 'team_rosters.json'), 'w') as f:
        json.dump(processed_rosters, f, indent=2)

    # 2. Process and save players
    processed_players = process_players(raw_data['players_wl'])
    with open(os.path.join(DATA_DIR, 'players_summary.json'), 'w') as f:
        json.dump(processed_players, f, indent=2)
    
    # 3. Copy the team data directly (this was the missing step)
    with open(os.path.join(DATA_DIR, 'espn_mTeam.json'), 'w') as f:
        json.dump(raw_data['mTeam'], f, indent=2)

    print("--- Data Processing Finished ---")
    print("All three data files have been created successfully.")

if __name__ == '__main__':
    main()
