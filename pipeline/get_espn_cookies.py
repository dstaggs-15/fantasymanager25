# pipeline/get_espn_cookies.py

import sys
import asyncio
import os
import argparse
from playwright.async_api import async_playwright
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def get_cookies(email, password, league_id):
    """
    Launches a browser, logs into ESPN, and extracts the SWID and ESPN_S2 cookies.
    """
    async with async_playwright() as p:
        logging.info("Launching Chromium browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to a league page to get the right cookie context
        league_url = f'https://fantasy.espn.com/football/league?leagueId={league_id}'
        logging.info(f"Navigating to {league_url}")
        await page.goto(league_url, wait_until='domcontentloaded')

        # Click the "Log In" button
        try:
            logging.info("Waiting for the 'Log In' button...")
            await page.get_by_role("button", name="Log In").click(timeout=10000)
            logging.info("Clicked 'Log In' button.")
        except Exception as e:
            logging.warning(f"Could not find 'Log In' button on main page, attempting direct login. Error: {e}")
            pass

        # Wait for the login iframe
        logging.info("Waiting for the login iframe...")
        iframe_selector = 'iframe[title="Sign in"]'
        await page.wait_for_selector(iframe_selector, state='attached', timeout=20000)
        login_iframe = page.frame(name='disneyid-iframe')

        if not login_iframe:
            logging.error("Could not find the 'disneyid-iframe' by name.")
            raise Exception("Login iframe not found.")

        # Fill in the login form
        logging.info("Filling login form...")
        await login_iframe.fill('input[type="email"]', email)
        await login_iframe.fill('input[type="password"]', password)

        # Click the "Log In" button inside the iframe
        logging.info("Submitting login form...")
        await login_iframe.click('button[type="submit"]')

        # Wait for navigation after login
        try:
            await page.wait_for_url(league_url, timeout=20000)
            logging.info("Login successful. Navigated back to league page.")
        except Exception as e:
            logging.error("Login failed or timed out. Check credentials or network. Error: %s", e)
            
            # Save screenshot for debugging
            screenshot_path = 'artifacts/login_failure.png'
            os.makedirs('artifacts', exist_ok=True)
            await page.screenshot(path=screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            
            # Get the HTML content for further debugging
            with open('artifacts/login_failure.html', 'w') as f:
                f.write(await page.content())
            logging.info("Page HTML content saved for debugging.")

            raise Exception("Login process failed.")

        # Extract cookies
        logging.info("Extracting cookies...")
        cookies = await context.cookies(urls=[f"https://fantasy.espn.com/football/league?leagueId={league_id}"])
        swid = None
        espn_s2 = None

        for cookie in cookies:
            if cookie['name'] == 'SWID':
                swid = cookie['value']
            elif cookie['name'] == 'espn_s2':
                espn_s2 = cookie['value']

        if swid and espn_s2:
            logging.info("Successfully extracted SWID and ESPN_S2 cookies.")
            print(f"ESPN_SWID={swid}")
            print(f"ESPN_S2={espn_s2}")
        else:
            logging.error("SWID or ESPN_S2 cookie not found after login.")
            raise Exception("SWID or ESPN_S2 not found.")

        await browser.close()
        
        return swid, espn_s2

async def main():
    parser = argparse.ArgumentParser(description='ESPN Cookie Collector.')
    parser.add_argument('--league-id', required=True, help='ESPN League ID')
    args = parser.parse_args()

    espn_user = os.environ.get('ESPN_USER')
    espn_pass = os.environ.get('ESPN_PASS')
    
    if not espn_user or not espn_pass:
        logging.error("ESPN_USER and ESPN_PASS environment variables must be set.")
        sys.exit(1)

    try:
        await get_cookies(espn_user, espn_pass, args.league_id)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
