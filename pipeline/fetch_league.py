# pipeline/fetch_league.py

import json
import requests
import os
import sys
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_league(league_id, swid, espn_s2):
    """
    Fetches league metadata using the provided cookies.
    """
    url = f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/2025/leagues/{league_id}'

    try:
        logging.info("Starting league data fetch...")
        session = requests.Session()
        session.cookies.set('SWID', swid)
        session.cookies.set('espn_s2', espn_s2)
        
        response = session.get(url)
        response.raise_for_status()

        if 'text/html' in response.headers.get('Content-Type', ''):
            logging.error("Received HTML response instead of JSON. ESPN's anti-bot system is blocking the request.")
            return None

        data = response.json()
        logging.info("League data fetched successfully.")
        return data

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching league data: {e}")
        return None

def save_data(data, filename):
    """
    Saves data to a JSON file.
    """
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

    if not all([league_id, swid, espn_s2]):
        logging.error("Missing required environment variables: LEAGUE_ID, SWID, and ESPN_S2.")
        sys.exit(1)

    league_data = fetch_league(league_id, swid, espn_s2)

    if league_data:
        save_data(league_data, 'espn_mTeam.json')
    else:
        logging.error("Failed to fetch league data. Saving an empty list to prevent site breakage.")
        save_data([], 'espn_mTeam.json')
        sys.exit(1)

if __name__ == "__main__":
    main()
