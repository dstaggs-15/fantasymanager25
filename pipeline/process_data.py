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

    # --- Process espn_mTeam.json (for the Teams page) ---
    # We can pass the whole object, as it contains the 'teams' and 'members' keys
    with open(os.path.join(DATA_DIR, 'espn_mTeam.json'), 'w') as f:
        json.dump(data, f, indent=2)
    print("✅ Successfully created espn_mTeam.json")
    
    # --- Process team_rosters.json ---
    teams_data = data.get('teams', [])
    team_rosters = {}
    for team in teams_data:
        # The agent provides teamId, which is what we need
        team_id = team.get('teamId')
        if team_id:
            team_rosters[team_id] = {
                'teamName': team.get('name', 'Unknown Team'),
                # The roster is empty pre-draft, which is correct
                'players': team.get('roster', []) 
            }
    
    final_rosters = {"teams": team_rosters, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(os.path.join(DATA_DIR, 'team_rosters.json'), 'w') as f:
        json.dump(final_rosters, f, indent=2)
    print("✅ Successfully created team_rosters.json")

    # --- Create an empty players_summary.json for now ---
    with open(os.path.join(DATA_DIR, 'players_summary.json'), 'w') as f:
        json.dump([], f, indent=2) # Empty list
    print("✅ Successfully created an empty players_summary.json")

    print("\n--- Data Processing Finished Successfully ---")

if __name__ == '__main__':
    main()
