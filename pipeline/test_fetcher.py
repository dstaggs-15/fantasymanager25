import os
import json
import requests

# --- Configuration ---
LEAGUE_ID = '508419792'
SEASON_ID = '2025'
DATA_DIR = 'docs/data'

ENDPOINTS = {
    'raw_league_data.json': f'https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/segments/0/leagues/{LEAGUE_ID}?view=mSettings&view=mRoster&view=mTeam&view=modular&view=mNav',
    'raw_players_wl.json': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/players?scoringPeriodId=0&view=players_wl'
}

def main():
    print("--- Starting Lightweight Fetch Test ---")
    
    # Load cookies from the json file
    try:
        with open('cookies.json', 'r') as f:
            cookie_data = json.load(f)
        cookies = {
            'swid': cookie_data['ESPN_SWID'],
            'espn_s2': cookie_data['ESPN_S2']
        }
        print("Successfully loaded cookies.")
    except Exception as e:
        print(f"::error::Could not load cookies.json. Please ensure the file exists and is formatted correctly. Error: {e}")
        exit(1)

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
    os.makedirs(DATA_DIR, exist_ok=True)

    for filename, url in ENDPOINTS.items():
        print(f"Fetching: {filename}...")
        try:
            res = requests.get(url, cookies=cookies, headers=headers, timeout=15)
            res.raise_for_status() # Raises an exception for bad status codes (like 403)
            
            # Save the raw data
            output_path = os.path.join(DATA_DIR, filename)
            with open(output_path, 'w') as f:
                json.dump(res.json(), f, indent=2)
            print(f"✅ Success! Data saved to {output_path}")

        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED to fetch {url}. Error: {e}")
            exit(1)

    print("\n--- Test Complete: Both endpoints fetched successfully! ---")

if __name__ == '__main__':
    main()
