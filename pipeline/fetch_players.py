# pipeline/fetch_players.py

import json
import requests
import os
import sys
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_players(league_id, swid, espn_s2):
    """
    Fetches a summary of players for the given league using the provided cookies.
    """
    url = f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/2025/players?leagueId={league_id}'
    
    headers = {
        'Accept': 'application/json',
        'x-fantasy-filter': json.dumps({"players": {"filterStatus": {"value": ["FREEAGENT", "WAIVERS", "ONTEAM"]}}})
    }

    try:
        logging.info("Starting player data fetch...")
        session = requests.Session()
        session.cookies.set('SWID', swid)
        session.cookies.set('espn_s2', espn_s2)
        
        response = session.get(url, headers=headers)
        response.raise_for_status()

        # Check for HTML content, which indicates an anti-bot block
        if 'text/html' in response.headers.get('Content-Type', ''):
            logging.error("Received HTML response instead of JSON. ESPN's anti-bot system is blocking the request. Cookies may be invalid or expired.")
            return None

        data = response.json()
        logging.info("Player data fetched successfully.")
        
        # Process the data to create a lean summary
        player_summary = []
        for player in data:
            summary = {
                'id': player.get('id'),
                'name': player.get('fullName'),
                'position': player.get('defaultPositionId'),
                'team': player.get('proTeamId'),
                'projections': player.get('playerRatingsBySeasonId', {}).get('2025', {}).get('points', {}).get('total')
            }
            player_summary.append(summary)

        return player_summary

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching player data: {e}")
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

    players_data = fetch_players(league_id, swid, espn_s2)

    if players_data:
        save_data(players_data, 'players_summary.json')
    else:
        logging.error("Failed to fetch player data. Saving an empty list to prevent site breakage.")
        save_data([], 'players_summary.json')
        sys.exit(1)

if __name__ == "__main__":
    main()
