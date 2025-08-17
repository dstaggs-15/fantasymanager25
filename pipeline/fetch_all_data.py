# pipeline/fetch_all_data.py

import json
import requests
import os
import sys
import logging
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_cookies_with_playwright(email, password, league_id):
    """Logs into ESPN and extracts the SWID and ESPN_S2 cookies."""
    try:
        logging.info("Attempting to get cookies with Playwright...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            league_url = f'https://fantasy.espn.com/football/league?leagueId={league_id}'
            page.goto(league_url, wait_until='domcontentloaded')

            iframe = page.frame_locator('iframe[title="Sign in"]')
            iframe.get_by_placeholder("Username or Email Address").fill(email)
            iframe.get_by_placeholder("Password (case sensitive)").fill(password)
            iframe.get_by_role("button", name="Log In").click()

            page.wait_for_url(league_url, timeout=20000)
            
            cookies = context.cookies(urls=[league_url])
            swid = next((c['value'] for c in cookies if c['name'] == 'SWID'), None)
            espn_s2 = next((c['value'] for c in cookies if c['name'] == 'espn_s2'), None)

            browser.close()
            
            if not swid or not espn_s2:
                logging.error("SWID or ESPN_S2 cookie not found after login.")
                return None, None
            
            logging.info("Successfully extracted SWID and ESPN_S2 cookies.")
            return swid, espn_s2
    except Exception as e:
        logging.error(f"Playwright login failed: {e}")
        return None, None

def fetch_data(url, swid, espn_s2, headers=None):
    """Fetches data from a URL using a persistent session."""
    try:
        session = requests.Session()
        session.cookies.set('SWID', swid)
        session.cookies.set('espn_s2', espn_s2)
        response = session.get(url, headers=headers)
        response.raise_for_status()
        
        if 'text/html' in response.headers.get('Content-Type', ''):
            logging.error("Received HTML response instead of JSON. Cookies are invalid.")
            return None
            
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data from {url}: {e}")
        return None

def save_json(data, filename):
    """Saves data to a JSON file."""
    output_dir = 'docs/data'
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logging.info(f"Data saved to {filepath}")

def main():
    league_id = os.environ.get('LEAGUE_ID')
    swid = os.environ.get('SWID') or os.environ.get('ESPN_SWID')
    espn_s2 = os.environ.get('ESPN_S2')
    
    if not swid or not espn_s2:
        logging.warning("Cookies not found. Attempting Playwright login.")
        swid, espn_s2 = get_cookies_with_playwright(os.environ.get('ESPN_USER'), os.environ.get('ESPN_PASS'), league_id)
        if not swid or not espn_s2:
            logging.error("Failed to get cookies. Exiting.")
            sys.exit(1)

    # Fetch and save player data
    players_url = f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/2025/players?leagueId={league_id}'
    players_headers = {'x-fantasy-filter': json.dumps({"players": {"filterStatus": {"value": ["FREEAGENT", "WAIVERS", "ONTEAM"]}}})}
    players_data = fetch_data(players_url, swid, espn_s2, headers=players_headers)
    if players_data:
        save_json([{'id': p['id'], 'name': p['fullName']} for p in players_data], 'players_summary.json')
    else:
        save_json([], 'players_summary.json')

    # Fetch and save league data
    league_url = f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/2025/leagues/{league_id}'
    league_data = fetch_data(league_url, swid, espn_s2)
    if league_data:
        save_json(league_data, 'espn_mTeam.json')
    else:
        save_json([], 'espn_mTeam.json')

    # Fetch and save rosters data
    rosters_url = f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/2025/leagues/{league_id}?view=mRoster'
    rosters_data = fetch_data(rosters_url, swid, espn_s2)
    if rosters_data:
        rosters = {}
        for team in rosters_data.get('teams', []):
            rosters[team['id']] = {'players': [e['playerPoolEntry']['player'] for e in team['roster']['entries']]}
        save_json(rosters, 'team_rosters.json')
    else:
        save_json({}, 'team_rosters.json')

if __name__ == "__main__":
    main()
