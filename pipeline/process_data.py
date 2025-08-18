import json
import os
import time

DATA_DIR = 'docs/data'

# --- Data Processing Functions ---
def process_rosters(roster_data):
    teams_processed = {}
    for team in roster_data.get('teams', []):
        team_id = team['id']
        teams_processed[team_id] = {
            'teamName': team.get('name', 'Unknown Team'),
            'players': [player['playerPoolEntry']['player']['fullName'] for player in team.get('roster', {}).get('entries', [])]
        }
    return {"teams": teams_processed, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

def process_players(player_data):
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
    
    # Define which files to read, process, and overwrite
    files_to_process = {
        'team_rosters.json': process_rosters,
        'players_summary.json': process_players,
    }

    for filename, process_func in files_to_process.items():
        filepath = os.path.join(DATA_DIR, filename)
        try:
            print(f"Processing {filepath}...")
            with open(filepath, 'r') as f:
                raw_data = json.load(f)

            # Transform the data using the correct function
            processed_data = process_func(raw_data)
            
            # Overwrite the original file with the clean data
            with open(filepath, 'w') as f:
                json.dump(processed_data, f, indent=2)
            print(f"Successfully processed and overwrote {filepath}")

        except FileNotFoundError:
            print(f"Error: File not found at {filepath}. Skipping.")
        except Exception as e:
            print(f"An error occurred while processing {filename}: {e}")

    print("--- Data Processing Finished ---")

if __name__ == '__main__':
    main()
