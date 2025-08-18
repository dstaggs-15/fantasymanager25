import os
import json
import time
from playwright.sync_api import sync_playwright

# --- Configuration ---
LEAGUE_ID = os.getenv('LEAGUE_ID')
ESPN_SWID = os.getenv('ESPN_SWID')
ESPN_S2 = os.getenv('ESPN_S2')
SEASON_ID = '2025'
DATA_DIR = 'docs/data'

ENDPOINTS = {
    'raw_mTeam.json': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/leagues/{LEAGUE_ID}?view=mTeam',
    'raw_mRoster.json': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/leagues/{LEAGUE_ID}?view=mRoster',
    'raw_players.json': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/players?scoringPeriodId=0&view=players_wl'
}

def main():
    print("--- Starting Playwright Fetch with Pre-Authentication ---")
    if not all([LEAGUE_ID, ESPN_SWID, ESPN_S2]):
        print("::error::This script requires LEAGUE_ID, ESPN_SWID, and ESPN_S2 to be set.")
        exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        
        try:
            # THE FIX: Inject the authentication cookies directly into the browser context.
            print("Injecting authentication cookies into the browser...")
            cookies = [
                {'name': 'swid', 'value': ESPN_SWID, 'domain': '.espn.com', 'path': '/'},
                {'name': 'espn_s2', 'value': ESPN_S2, 'domain': '.espn.com', 'path': '/'}
            ]
            context.add_cookies(cookies)
            print("Cookies injected. The browser is now pre-authenticated.")

            page = context.new_page()
            os.makedirs(DATA_DIR, exist_ok=True)

            for filename, url in ENDPOINTS.items():
                print(f"Fetching: {filename} from {url}")
                # Go directly to the API endpoint. No login page needed.
                page.goto(url)
                
                # ESPN API endpoints wrap the JSON in a <pre> tag
                json_text = page.locator('pre').inner_text(timeout=20000)
                
                if not json_text.strip().startswith('{'):
                   raise Exception(f"Failed to fetch valid JSON from {url}. Response was not JSON.")

                output_path = os.path.join(DATA_DIR, filename)
                with open(output_path, 'w') as f:
                    f.write(json_text)
                print(f"Successfully saved raw data to {output_path}")

        except Exception as e:
            print(f"::error::Playwright failed: {e}")
            page.screenshot(path='error_screenshot.png')
            exit(1)
        finally:
            browser.close()
    
    print("--- Playwright Fetch Finished Successfully ---")

if __name__ == '__main__':
    main()
