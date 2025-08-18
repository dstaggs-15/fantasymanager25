import os
from playwright.sync_api import sync_playwright

# --- Configuration ---
ESPN_USER = os.getenv('ESPN_USER')
ESPN_PASS = os.getenv('ESPN_PASS')

def main():
    print("--- Starting Interactive Cookie-Grabber Script ---")
    if not all([ESPN_USER, ESPN_PASS]):
        print("::error::This script requires ESPN_USER and ESPN_PASS.")
        exit(1)

    with sync_playwright() as p:
        # THE CHANGE: headless=False makes the browser window visible.
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("Opening ESPN login page in a visible browser...")
            page.goto('https://fantasy.espn.com/football/')
            
            print("\n" + "="*50)
            print("ACTION REQUIRED: Please log in to ESPN in the browser window that will open on your remote desktop.")
            print("The script will wait for up to 3 minutes for you to complete the login.")
            print("="*50 + "\n")

            # Wait for the user to successfully log in. 
            # We know login is successful when the URL contains "myteams".
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
