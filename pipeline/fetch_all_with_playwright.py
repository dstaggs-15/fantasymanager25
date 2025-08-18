import os
from playwright.sync_api import sync_playwright

# --- Configuration ---
ESPN_USER = os.getenv('ESPN_USER')
ESPN_PASS = os.getenv('ESPN_PASS')
# The correct URL you provided
LEAGUE_HOMEPAGE_URL = "https://fantasy.espn.com/football/team?leagueId=508419792&teamId=1&seasonId=2025"

def main():
    print("--- Starting Interactive Cookie-Grabber Script ---")
    if not all([ESPN_USER, ESPN_PASS]):
        print("::error::This script requires ESPN_USER and ESPN_PASS.")
        exit(1)

    with sync_playwright() as p:
        # headless=False makes the browser window visible for you to interact with.
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            print(f"Opening your league homepage in a visible browser: {LEAGUE_HOMEPAGE_URL}")
            page.goto(LEAGUE_HOMEPAGE_URL)
            
            print("\n" + "="*50)
            print("ACTION REQUIRED: Please log in to ESPN in the browser window that just opened on your remote desktop.")
            print("The script will wait for up to 3 minutes for you to complete the login.")
            print("="*50 + "\n")

            # After a successful login, the URL will still contain "myteams" or the leagueId.
            # We will wait for the page to fully load after you log in.
            page.wait_for_load_state('networkidle', timeout=180000)
            print("Login successful! Capturing cookies...")
            
            cookies = context.cookies()
            swid_cookie = next((c for c in cookies if c['name'] == 'swid'), None)
            s2_cookie = next((c for c in cookies if c['name'] == 'espn_s2'), None)

            if not all([swid_cookie, s2_cookie]):
                raise Exception("Could not find SWID or ESPN_S2 cookies after login.")

            print("\n" + "="*50)
            print("✅ SUCCESS! Copy the values below and save them as GitHub Secrets.")
            print(f"\nESPN_SWID:\n{swid_cookie['value']}")
            print(f"\nESPN_S2:\n{s2_cookie['value']}")
            print("\n" + "="*50 + "\n")

        except Exception as e:
            print(f"::error::An error occurred: {e}")
            page.screenshot(path='error_screenshot.png')
            exit(1)
        finally:
            browser.close()

if __name__ == '__main__':
    main()
