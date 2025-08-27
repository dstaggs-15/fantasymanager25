# pipeline/get_oline_rankings.py
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import sys

def scrape_oline_rankings():
    """
    Scrapes the latest offensive line rankings from a FantasyPros article
    by targeting the specific table in the HTML.
    """
    print("\n--- Starting O-Line Rankings Scraper ---")

    url = "https://www.fantasypros.com/2025/07/nfl-offensive-line-rankings-fantasy-football/"
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
        
        # DEFINITIVE FIX: Find the table using the class 'mobile-table' from your screenshot.
        table = soup.find('table', class_='mobile-table')
        if not table:
            print("❌ ERROR: Could not find the table with class 'mobile-table'. The website structure may have changed.")
            sys.exit(1)
            
        rows = table.find_all('tr')
        team_data = []
        fp_name_to_abbr_map = {
            'ARIZONA CARDINALS': 'ARI', 'ATLANTA FALCONS': 'ATL', 'BALTIMORE RAVENS': 'BAL', 'BUFFALO BILLS': 'BUF', 
            'CAROLINA PANTHERS': 'CAR', 'CHICAGO BEARS': 'CHI', 'CINCINNATI BENGALS': 'CIN', 'CLEVELAND BROWNS': 'CLE', 
            'DALLAS COWBOYS': 'DAL', 'DENVER BRONCOS': 'DEN', 'DETROIT LIONS': 'DET', 'GREEN BAY PACKERS': 'GB', 
            'HOUSTON TEXANS': 'HOU', 'INDIANAPOLIS COLTS': 'IND', 'JACKSONVILLE JAGUARS': 'JAC', 'KANSAS CITY CHIEFS': 'KC', 
            'LAS VEGAS RAIDERS': 'LV', 'LOS ANGELES CHARGERS': 'LAC', 'LOS ANGELES RAMS': 'LAR', 'MIAMI DOLPHINS': 'MIA', 
            'MINNESOTA VIKINGS': 'MIN', 'NEW ENGLAND PATRIOTS': 'NE', 'NEW ORLEANS SAINTS': 'NO', 'NEW YORK GIANTS': 'NYG', 
            'NEW YORK JETS': 'NYJ', 'PHILADELPHIA EAGLES': 'PHI', 'PITTSBURGH STEELERS': 'PIT', 'SAN FRANCISCO 49ERS': 'SF', 
            'SEATTLE SEAHAWKS': 'SEA', 'TAMPA BAY BUCCANEERS': 'TB', 'TENNESSEE TITANS': 'TEN', 'WASHINGTON COMMANDERS': 'WAS'
        }

        for row in rows[1:]: # Skip header row
            cols = row.find_all('td')
            if len(cols) == 2:
                rank = int(cols[0].get_text(strip=True))
                team_name_fp = cols[1].get_text(strip=True).upper()
                team_abbr = fp_name_to_abbr_map.get(team_name_fp)
                if team_abbr:
                    team_data.append({'team': team_abbr, 'rank': rank})

        if not team_data:
            print("❌ ERROR: No team data could be extracted from the table rows.")
            sys.exit(1)

        df = pd.DataFrame(team_data).sort_values(by='rank')
        df.to_csv(output_path, index=False)
        print(f"✅ Successfully scraped and saved {len(df)} O-line rankings.")

    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred. Reason: {e}")
        sys.exit(1)

if __name__ == '__main__':
    scrape_oline_rankings()
