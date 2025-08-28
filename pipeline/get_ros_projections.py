# pipeline/get_ros_projections.py
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import sys

def scrape_ros_projections():
    """
    Scrapes the Rest-of-Season (ROS) PPR Flex rankings from FantasyPros
    and saves them to a CSV file.
    """
    print("\n--- Starting ROS Projections Scraper ---")

    # URL for FantasyPros' standard PPR Flex ROS rankings
    url = "https://www.fantasypros.com/nfl/rankings/ros-ppr-flex.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    output_path = os.path.join('docs', 'data', 'raw', 'ros_projections.csv')

    try:
        print(f"Fetching data from {url}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        print("Parsing the rankings table...")
        
        # The main data table on FantasyPros has an id of 'data'
        table = soup.find('table', {'id': 'data'})
        if not table:
            print("❌ ERROR: Could not find the rankings table with id='data'. The website structure may have changed.")
            sys.exit(1)
            
        rows = table.find_all('tr')
        player_data = []

        for row in rows:
            # Look for player rows, which have a specific 'mpb-player-' id format
            if 'id' in row.attrs and 'mpb-player-' in row['id']:
                rank = row.find('td', class_='center').get_text(strip=True)
                player_cell = row.find('td', class_='player-label')
                player_name = player_cell.find('a').get_text(strip=True)
                team_abbr = player_cell.find('small').get_text(strip=True)

                # Small cleanups for team abbreviations
                if team_abbr == 'JAC': team_abbr = 'JAX'

                player_data.append({
                    'rank': int(rank),
                    'player_name': player_name,
                    'team': team_abbr
                })

        if not player_data:
            print("❌ ERROR: No player data could be extracted from the table.")
            sys.exit(1)

        df = pd.DataFrame(player_data)
        df.to_csv(output_path, index=False)
        print(f"✅ Successfully scraped and saved {len(df)} ROS player projections.")

    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred. Reason: {e}")
        sys.exit(1)

if __name__ == '__main__':
    scrape_ros_projections()
