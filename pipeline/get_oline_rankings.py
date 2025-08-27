# pipeline/get_oline_rankings.py
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import sys

def scrape_oline_rankings():
    """
    Scrapes the latest offensive line rankings from Sharp Football Analysis
    and saves them to a CSV file.
    """
    print("\n--- Starting O-Line Rankings Scraper (Sharp Football Analysis) ---")

    url = "https://www.sharpfootballanalysis.com/analysis/best-nfl-offensive-line-rankings/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    output_path = os.path.join('docs', 'data', 'raw', 'oline_rankings.csv')

    try:
        print(f"Fetching data from {url}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("Parsing the data table...")
        
        # Find the specific table used in their articles
        table = soup.find('table', class_='editor-table')
        if not table:
            print("❌ ERROR: Could not find the data table. The website structure may have changed.")
            sys.exit(1)
            
        rows = table.find_all('tr')
        team_data = []
        
        sharp_name_to_abbr_map = {
            'Arizona Cardinals': 'ARI', 'Atlanta Falcons': 'ATL', 'Baltimore Ravens': 'BAL', 'Buffalo Bills': 'BUF', 
            'Carolina Panthers': 'CAR', 'Chicago Bears': 'CHI', 'Cincinnati Bengals': 'CIN', 'Cleveland Browns': 'CLE', 
            'Dallas Cowboys': 'DAL', 'Denver Broncos': 'DEN', 'Detroit Lions': 'DET', 'Green Bay Packers': 'GB', 
            'Houston Texans': 'HOU', 'Indianapolis Colts': 'IND', 'Jacksonville Jaguars': 'JAC', 'Kansas City Chiefs': 'KC', 
            'Las Vegas Raiders': 'LV', 'Los Angeles Chargers': 'LAC', 'Los Angeles Rams': 'LAR', 'Miami Dolphins': 'MIA', 
            'Minnesota Vikings': 'MIN', 'New England Patriots': 'NE', 'New Orleans Saints': 'NO', 'New York Giants': 'NYG', 
            'New York Jets': 'NYJ', 'Philadelphia Eagles': 'PHI', 'Pittsburgh Steelers': 'PIT', 'San Francisco 49ers': 'SF', 
            'Seattle Seahawks': 'SEA', 'Tampa Bay Buccaneers': 'TB', 'Tennessee Titans': 'TEN', 'Washington Commanders': 'WAS'
        }

        for row in rows[1:]: # Skip header row
            cols = row.find_all('td')
            if len(cols) >= 2:
                rank = int(cols[0].get_text(strip=True))
                team_name = cols[1].get_text(strip=True)
                
                team_abbr = sharp_name_to_abbr_map.get(team_name)
                if team_abbr:
                    team_data.append({'team': team_abbr, 'rank': rank})

        if not team_data or len(team_data) < 32:
            print(f"❌ ERROR: Only found {len(team_data)}/32 teams. The article structure may have changed.")
            sys.exit(1)

        df = pd.DataFrame(team_data).sort_values(by='rank')
        df.to_csv(output_path, index=False)
        print(f"✅ Successfully scraped and saved {len(df)} O-line rankings.")

    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred. Reason: {e}")
        sys.exit(1)

if __name__ == '__main__':
    scrape_oline_rankings()
