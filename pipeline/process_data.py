import json
import os
import time

DATA_DIR = 'docs/data'
MASTER_FILE = 'fantasy_league_data.json'

def main():
    print(f"--- Starting processing of {MASTER_FILE} ---")
    master_path = os.path.join(DATA_DIR, MASTER_FILE)
    
    try:
        with open(master_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ ERROR: Could not read or parse {master_path}. Error: {e}")
        exit(1)

    # --- Process Teams and Rosters ---
    teams_data = data.get('teams', [])
    team_rosters = {}
    for team in teams_data:
        team_rosters[team['teamId']] = {
            'teamName': team.get('name', 'Unknown Team'),
            'players': team.get('roster', []) # Assuming agent provides simple player name list
        }
    
    final_rosters = {"teams": team_rosters, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(os.path.join(DATA_DIR, 'team_rosters.json'), 'w') as f:
        json.dump(final_rosters, f, indent=2)
    print("✅ Successfully created team_rosters.json")

    # --- For now, let's just copy the other relevant data ---
    # We can add more advanced player processing later if needed
    with open(os.path.join(DATA_DIR, 'espn_mTeam.json'), 'w') as f:
        json.dump(data, f, indent=2)
    print("✅ Successfully created espn_mTeam.json")

    print("\n--- Data Processing Finished Successfully ---")

if __name__ == '__main__':
    main()
