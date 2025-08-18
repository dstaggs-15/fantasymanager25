import os
from playwright.sync_api import sync_playwright

LEAGUE_HOMEPAGE_URL = "https://fantasy.espn.com/football/team?leagueId=508419792&teamId=1&seasonId=2025"

def main():
    print("--- Starting Interactive Cookie-Grabber Script ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Makes the browser visible
        context = browser.new_context()
        page = context.new_page()
        try:
            print(f"Opening your league homepage in a visible browser...")
            page.goto(LEAGUE_HOMEPAGE_URL)
            
            print("\n" + "="*50)
            print("ACTION REQUIRED: Please log in to ESPN and solve the CAPTCHA in the browser window on your desktop.")
            print("The script will wait for up to 3 minutes for you to complete the login.")
            print("="*50 + "\n")

            page.wait_for_url("**/myteams**", timeout=180000)
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
