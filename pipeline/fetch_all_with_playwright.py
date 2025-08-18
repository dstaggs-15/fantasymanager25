import os
import json
import time
from playwright.sync_api import sync_playwright, TimeoutError

# --- Configuration ---
LEAGUE_ID = os.getenv('LEAGUE_ID')
ESPN_USER = os.getenv('ESPN_USER')
ESPN_PASS = os.getenv('ESPN_PASS')
SEASON_ID = '2025'
DATA_DIR = 'docs/data'

# We'll save the raw data with these filenames
ENDPOINTS = {
    'raw_mTeam.json': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/leagues/{LEAGUE_ID}?view=mTeam',
    'raw_mRoster.json': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/leagues/{LEAGUE_ID}?view=mRoster',
    'raw_players.json': f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_ID}/players?scoringPeriodId=0&view=players_wl'
}

def main():
    print("--- Starting Playwright Raw Data Fetch ---")
    if not all([LEAGUE_ID, ESPN_USER, ESPN_PASS]):
        print("Error: Missing required environment variables.")
        exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            print("Navigating to ESPN login page...")
            page.goto('https://www.espn.com/login', timeout=60000)
            
            # THE FIX: Wait specifically for the iframe to appear before doing anything else.
            print("Waiting for login form to appear...")
            login_iframe = page.wait_for_selector('#oneid-iframe', timeout=30000)
            frame = login_iframe.content_frame()

            print("Filling in login credentials...")
            frame.get_by_label('Username or Email Address').fill(ESPN_USER)
            frame.get_by_label('Password').fill(ESPN_PASS)
            frame.get_by_role('button', name='Log In').click()
            
            print("Login submitted. Waiting for authentication to complete...")
            page.wait_for_load_state('networkidle', timeout=30000)
            print("Login successful.")

            os.makedirs(DATA_DIR, exist_ok=True)
            for filename, url in ENDPOINTS.items():
                print(f"Fetching raw data for: {filename}...")
                page.goto(url)
                json_text = page.locator('pre').inner_text()
                if not json_text.strip().startswith('{'):
                   raise Exception(f"Failed to fetch valid JSON from {url}.")
                
                output_path = os.path.join(DATA_DIR, filename)
                with open(output_path, 'w') as f:
                    f.write(json_text)
                print(f"Successfully saved raw data to {output_path}")

        except TimeoutError:
            print("A timeout error occurred. ESPN's login page may have changed or is showing a CAPTCHA.")
            page.screenshot(path='error_screenshot.png')
            print("Error screenshot saved to error_screenshot.png")
            exit(1) # Exit with an error code
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            page.screenshot(path='error_screenshot.png')
            print("Error screenshot saved to error_screenshot.png")
            exit(1) # Exit with an error code
        finally:
            browser.close()
            print("--- Raw data fetch finished ---")

if __name__ == '__main__':
    main()
