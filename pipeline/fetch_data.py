import os
import json
import time
from playwright.sync_api import sync_playwright, TimeoutError

# --- Configuration ---
LEAGUE_ID = '508419792'
SEASON_ID = '2025'
DATA_DIR = 'docs/data'

ENDPOINTS = {
    'league_data': f'https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/segments/0/leagues/{LEAGUE_ID}?view=mSettings&view=mRoster&view=mTeam&view=modular&view=mNav',
    'players_wl': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/players?scoringPeriodId=0&view=players_wl'
}

# --- Data Processing Functions ---
def process_rosters(roster_data):
    teams_processed = {}
    for team in roster_data.get('teams', []):
        teams_processed[team['id']] = {
            'teamName': team.get('name', 'Unknown Team'),
            'players': [player['playerPoolEntry']['player']['fullName'] for player in team.get('roster', {}).get('entries', [])]
        }
    return {"teams": teams_processed, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

def process_players(player_data):
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
    return players_processed

# --- Main Execution ---
def main():
    print("--- Starting Public Data Fetch with Playwright ---")
    raw_data = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # THE FIX: Impersonate a real browser by setting a User-Agent
        context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36')
        page = context.new_page()
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            for key, url in ENDPOINTS.items():
                print(f"Fetching {key} from {url}...")
                page.goto(url, wait_until='domcontentloaded')
                try:
                    json_text = page.locator('pre').inner_text(timeout=5000)
                except TimeoutError:
                    print("Could not find <pre> tag, using body content.")
                    json_text = page.locator('body').inner_text()
                raw_data[key] = json.loads(json_text)
                print(f"Success.")
            
            print("Processing and saving final files...")
            with open(os.path.join(DATA_DIR, 'team_rosters.json'), 'w') as f:
                json.dump(process_rosters(raw_data['league_data']), f, indent=2)
            with open(os.path.join(DATA_DIR, 'players_summary.json'), 'w') as f:
                json.dump(process_players(raw_data['players_wl']), f, indent=2)
            with open(os.path.join(DATA_DIR, 'espn_mTeam.json'), 'w') as f:
                json.dump(raw_data['league_data'], f, indent=2)

            print("--- Data Fetch and Processing Finished Successfully ---")
        except Exception as e:
            print(f"::error::Playwright failed: {e}")
            page.screenshot(path='error_screenshot.png')
            exit(1)
        finally:
            browser.close()

if __name__ == '__main__':
    main()
