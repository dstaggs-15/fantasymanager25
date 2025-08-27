# pipeline/get_oline_rankings.py
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import sys

def scrape_oline_rankings():
    """
    Scrapes the latest offensive line unit rankings from Pro Football Focus (PFF)
    and saves them to a CSV file.
    """
    print("\n--- Starting O-Line Rankings Scraper ---")

    # Using a more direct URL for unit grades
    url = "https://www.pff.com/nfl/grades/unit/offensive-line" 
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    output_path = os.path.join('docs', 'data', 'raw', 'oline_rankings.csv')

    try:
        print(f"Fetching data from {url}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        table = soup.find('table')
        if not table:
            print("❌ ERROR: Could not find the data table on the page. The website structure may have changed.")
            sys.exit(1)

        print("Parsing the data table...")
        rows = table.find_all('tr')
        team_data = []
        # PFF uses 3-letter abbreviations. We'll map them to the abbreviations nfl-data-py uses.
        pff_to_nfl_map = {
            'ARZ': 'ARI', 'BLT': 'BAL', 'CLV': 'CLE', 'HST': 'HOU', 
            'LA': 'LAR', 'LV': 'LV', 'SD': 'LAC', 'SF': 'SF', 'TB': 'TB',
            'GB': 'GB', 'KC': 'KC', 'IND': 'IND', 'DAL': 'DAL', 'NO': 'NO',
            'NE': 'NE', 'NYJ': 'NYJ', 'WSH': 'WAS', 'ATL': 'ATL', 'CAR': 'CAR',
            'CHI': 'CHI', 'CIN': 'CIN', 'BUF': 'BUF', 'DEN': 'DEN', 'DET': 'DET',
            'JAX': 'JAC', 'MIA': 'MIA', 'MIN': 'MIN', 'NYG': 'NYG', 'PHI': 'PHI',
            'PIT': 'PIT', 'SEA': 'SEA', 'TEN': 'TEN'
        }

        for row in rows[1:]: # Skip header
            cols = row.find_all('td')
            if len(cols) > 1:
                team_abbr_pff = cols[0].get_text(strip=True)
                team_abbr_nfl = pff_to_nfl_map.get(team_abbr_pff, team_abbr_pff) # Convert to our standard abbreviation
                team_data.append(team_abbr_nfl)

        if not team_data:
            print("❌ ERROR: No team data could be extracted.")
            sys.exit(1)

        df = pd.DataFrame({'team': team_data})
        df['rank'] = df.index + 1
        
        df.to_csv(output_path, index=False)
        print(f"✅ Successfully scraped and saved O-line rankings to:
