import os
import json
import time
from playwright.sync_api import sync_playwright

# --- Configuration ---
LEAGUE_ID = '508419792'
SEASON_ID = '2025'
DATA_DIR = 'docs/data'
LEAGUE_HOMEPAGE_URL = f"https://fantasy.espn.com/football/league?leagueId={LEAGUE_ID}"

# --- Data to capture ---
captured_data = {}

# --- Data Processing Functions ---
def process_data(league_data, player_data):
    print("Processing captured data...")
    processed = {}
    
    # Process Rosters and Teams
    teams_processed = {}
    for team in league_data.get('teams', []):
        teams_processed[team['id']] = {
            'teamName': team.get('name', 'Unknown Team'),
            'players': [p['playerPoolEntry']['player']['fullName'] for p in team.get('roster', {}).get('entries', [])]
        }
    processed['team_rosters.json'] = {"teams": teams_processed, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    processed['espn_mTeam.json'] = league_data # Save the whole object for team info

    # Process Players
    players_processed = []
    position_map = {0: 'TQB', 1: 'QB', 2: 'RB', 3: 'WR', 4: 'TE', 5: 'K', 16: 'D/ST'}
    for player_entry in player_data.get('players', []):
        player = player_entry.get('player', {})
        if not player or not player.get('proTeamAbbr'): continue
        players_processed.append({
            'id': player.get('id'),
            'name': player.get('fullName'),
            'pos': position_map.get(player.get('defaultPositionId'), 'N/A'),
            'team': player.get('proTeamAbbr', 'FA')
        })
    processed['players_summary.json'] = players_processed
    
    return processed

# --- Main Execution ---
def main():
    print("--- Starting Smart Scraper ---")
    
    def handle_response(response):
        # This function runs for every network response the page makes
        if "apis/v3/games/ffl" in response.url:
            print(f"Intercepted API call: {response.url}")
            if "view=mRoster" in response.url or "view=mTeam" in response.url:
                captured_data['league_data'] = response.json()
            if "view=players_wl" in response.url:
                captured_data['players_wl'] = response.json()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36')
        page = context.new_page()
        
        # Listen for API responses
        page.on("response", handle_response)
        
        try:
            print(f"Navigating to league homepage to trigger data loading...")
            page.goto(LEAGUE_HOMEPAGE_URL, wait_until='networkidle', timeout=60000)
            print("Page loaded. Data should be captured.")
            page.close() # We're done with the browser now

            # Check if we captured the data
            if 'league_data' not in captured_data or 'players_wl' not in captured_data:
                raise Exception("Failed to capture necessary API data from the page.")

            # Process the data we captured
            final_data = process_data(captured_data['league_data'], captured_data['players_wl'])
            
            # Save the final, clean files
            os.makedirs(DATA_DIR, exist_ok=True)
            for filename, data in final_data.items():
                output_path = os.path.join(DATA_DIR, filename)
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Successfully saved {filename}")

            print("--- Scraper Finished Successfully ---")

        except Exception as e:
            print(f"::error::Scraper failed: {e}")
            page.screenshot(path='error_screenshot.png')
            exit(1)
        finally:
            browser.close()

if __name__ == '__main__':
    main()
