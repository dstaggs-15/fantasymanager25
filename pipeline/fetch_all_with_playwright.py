import os
import json
import time
from playwright.sync_api import sync_playwright

# --- Configuration ---
LEAGUE_ID = os.getenv('LEAGUE_ID')
ESPN_USER = os.getenv('ESPN_USER')
ESPN_PASS = os.getenv('ESPN_PASS')
SEASON_ID = '2025'
DATA_DIR = 'docs/data'

# Define the ESPN API endpoints we need to visit
ENDPOINTS = {
    'espn_mTeam.json': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/leagues/{LEAGUE_ID}?view=mTeam',
    'team_rosters.json': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/leagues/{LEAGUE_ID}?view=mRoster',
    'players_summary.json': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/players?scoringPeriodId=0&view=players_wl'
}

def main():
    print("--- Starting Playwright Fantasy Data Fetch ---")

    if not all([LEAGUE_ID, ESPN_USER, ESPN_PASS]):
        print("Error: Missing required environment variables (LEAGUE_ID, ESPN_USER, ESPN_PASS).")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1. Log in to ESPN
            print("Navigating to ESPN login page...")
            page.goto('https://www.espn.com/login')
            time.sleep(3) # Wait for page elements to load

            # Find the login iframe and fill in credentials
            iframe = page.frame_locator('#oneid-iframe')
            iframe.get_by_label('Username or Email Address').fill(ESPN_USER)
            iframe.get_by_label('Password').fill(ESPN_PASS)
            iframe.get_by_role('button', name='Log In').click()
            print("Login submitted. Waiting for authentication...")
            page.wait_for_load_state('networkidle', timeout=30000) # Wait for login to complete

            # 2. Fetch data from each endpoint
            os.makedirs(DATA_DIR, exist_ok=True)
            for filename, url in ENDPOINTS.items():
                print(f"Fetching data for: {filename}...")
                page.goto(url)
                # ESPN API endpoints wrap the JSON in a <pre> tag
                json_text = page.locator('pre').inner_text()
                
                # Verify we got JSON, not an HTML error page
                if not json_text.strip().startswith('{'):
                   raise Exception(f"Failed to fetch valid JSON from {url}. Got HTML page instead.")

                data = json.loads(json_text)
                
                # Write the data to a file
                output_path = os.path.join(DATA_DIR, filename)
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Successfully saved data to {output_path}")

        except Exception as e:
            print(f"An error occurred: {e}")
            page.screenshot(path='error_screenshot.png')
            print("Error screenshot saved to error_screenshot.png")
        finally:
            browser.close()
            print("--- Playwright process finished ---")

if __name__ == '__main__':
    main()
