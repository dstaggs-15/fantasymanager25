# pipeline/fetch_rosters.py

import json
import requests
import os
import sys
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_rosters(league_id, swid, espn_s2):
    """
    Fetches current rosters for all teams in the league.
    """
    url = f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/2025/leagues/{league_id}'
    
    headers = {
        'Accept': 'application/json',
        'x-fantasy-filter': json.dumps({"players": {"filterStatus": {"value": ["ONTEAM"]}}, "rosters": {"rosterItems": {"filterRosterStatus": {"value": ["ONTEAM"]}}}})
    }

    try:
        logging.info("Starting roster data fetch...")
        session = requests.Session()
        session.cookies.set('SWID', swid)
        session.cookies.set('espn_s2', espn_s2)
        
        response = session.get(url, headers=headers)
        response.raise_for_status()

        if 'text/html' in response.headers.get('Content-Type', ''):
            logging.error("Received HTML response instead of JSON. ESPN's anti-bot system is blocking the request.")
            return None

        data = response.json()
        logging.info("Roster data fetched successfully.")

        teams_data = {}
        for team in data.get('teams', []):
            team_id = str(team['id'])
            players = []
            for player_item in team.get('roster', {}).get('entries', []):
                player_data = player_item.get('playerPoolEntry', {}).get('player', {})
                players.append({
                    "id": player_data.get('id'),
                    "name": player_data.get('fullName'),
                    "pos": player_data.get('defaultPositionId'),
                })
            
            teams_data[team_id] = {
                "teamName": team.get('name'),
                "players": players
            }

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "teams": teams_data
        }

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching roster data: {e}")
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

    roster_data = fetch_rosters(league_id, swid, espn_s2)

    if roster_data:
        save_data(roster_data, 'team_rosters.json')
    else:
        logging.error("Failed to fetch roster data. Saving an empty list to prevent site breakage.")
        save_data([], 'team_rosters.json')
        sys.exit(1)

if __name__ == "__main__":
    main()
