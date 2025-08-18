import os
import json
import time
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
    
    os.makedirs(DATA_DIR, exist_ok=True)
    for filename, url in ENDPOINTS.items():
        print(f"Fetching: {filename}...")
        try:
            res = requests.get(url, cookies=cookies, timeout=10)
            res.raise_for_status() # Raises an exception for bad status codes
            
            output_path = os.path.join(DATA_DIR, filename)
            with open(output_path, 'w') as f:
                json.dump(res.json(), f)
            print(f"Successfully saved {filename}")
        except requests.exceptions.RequestException as e:
            print(f"::error::Failed to fetch {url}. Error: {e}")
            exit(1)
    print("--- Fast Fetch Finished ---")

def fetch_with_playwright():
    """Fallback method: Fetches data by logging in with Playwright."""
    print("--- Starting Full Fetch using browser (Playwright) ---")
    if not all([ESPN_USER, ESPN_PASS]):
        print("::error::Playwright fallback requires ESPN_USER and ESPN_PASS secrets.")
        exit(1)
        
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto('https://www.espn.com/login', timeout=60000)
            login_iframe = page.wait_for_selector('#oneid-iframe', timeout=30000)
            frame = login_iframe.content_frame()
            frame.get_by_label('Username or Email Address').fill(ESPN_USER)
            frame.get_by_label('Password').fill(ESPN_PASS)
            frame.get_by_role('button', name='Log In').click()
            page.wait_for_load_state('networkidle', timeout=30000)
            print("Login successful.")

            os.makedirs(DATA_DIR, exist_ok=True)
            for filename, url in ENDPOINTS.items():
                page.goto(url)
                json_text = page.locator('pre').inner_text()
                output_path = os.path.join(DATA_DIR, filename)
                with open(output_path, 'w') as f:
                    f.write(json_text)
                print(f"Successfully saved {filename}")

        except Exception as e:
            print(f"::error::Playwright failed: {e}")
            page.screenshot(path='error_screenshot.png')
            print("Error screenshot saved to error_screenshot.png")
            exit(1)
        finally:
            browser.close()
    print("--- Full Fetch Finished ---")

def main():
    if not LEAGUE_ID:
        print("::error::LEAGUE_ID is not set.")
        exit(1)

    # This is the crucial logic that was missing
    if ESPN_SWID and ESPN_S2:
        fetch_with_requests()
    else:
        print("SWID and S2 secrets not found. Falling back to Playwright login.")
        fetch_with_playwright()

if __name__ == '__main__':
    main()
