import os
import json
import requests
from playwright.sync_api import sync_playwright, TimeoutError

# --- Configuration ---
LEAGUE_ID = os.getenv('LEAGUE_ID')
ESPN_USER = os.getenv('ESPN_USER')
ESPN_PASS = os.getenv('ESPN_PASS')
ESPN_SWID = os.getenv('ESPN_SWID')
ESPN_S2 = os.getenv('ESPN_S2')
SEASON_ID = '2025'
DATA_DIR = 'docs/data'

ENDPOINTS = {
    'raw_mTeam.json': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/leagues/{LEAGUE_ID}?view=mTeam',
    'raw_mRoster.json': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/leagues/{LEAGUE_ID}?view=mRoster',
    'raw_players.json': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/players?scoringPeriodId=0&view=players_wl'
}

def fetch_with_requests():
    """Fetches data using the fast requests method with cookies."""
    print("--- Starting Fast Fetch using cookies (requests) ---")
    
    cookies = {'swid': ESPN_SWID, 'espn_s2': ESPN_S2}
    # THE FIX: Add a User-Agent header to look like a real browser
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
    
    os.makedirs(DATA_DIR, exist_ok=True)
    for filename, url in ENDPOINTS.items():
        print(f"Fetching: {filename}...")
        try:
            res = requests.get(url, cookies=cookies, headers=headers, timeout=15)
            res.raise_for_status()
            
            with open(os.path.join(DATA_DIR, filename), 'w') as f:
                json.dump(res.json(), f)
            print(f"Successfully saved {filename}")
        except requests.exceptions.RequestException as e:
            print(f"::error::Failed to fetch {url}. Error: {e}")
            exit(1)
    print("--- Fast Fetch Finished ---")

def fetch_with_playwright():
    # This is now just a fallback and is unlikely to be used, but we keep it.
    print("--- Starting Full Fetch using browser (Playwright) ---")
    # ... (rest of the playwright function remains the same, no changes needed here) ...

# ... (the rest of the file remains the same) ...

# The code below this line is unchanged.

def main():
    if not LEAGUE_ID:
        print("::error::LEAGUE_ID is not set.")
        exit(1)

    if ESPN_SWID and ESPN_S2:
        fetch_with_requests()
    else:
        print("SWID and S2 secrets not found. Falling back to Playwright login.")
        fetch_with_playwright()

if __name__ == '__main__':
    main()
