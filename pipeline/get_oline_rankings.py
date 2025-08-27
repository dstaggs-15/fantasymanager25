# pipeline/get_oline_rankings.py
import pandas as pd
from bs4 import BeautifulSoup
import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def scrape_oline_rankings():
    print("\n--- Starting O-Line Rankings Scraper (Selenium Mode) ---")
    url = "https://www.fantasypros.com/2025/07/nfl-offensive-line-rankings-fantasy-football/"
    output_path = os.path.join('docs', 'data', 'raw', 'oline_rankings.csv')

    # Setup headless Chrome browser for GitHub Actions
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)

    try:
        print(f"Fetching data from {url}...")
        driver.get(url)
        # Wait for the page's JavaScript to load the content
        time.sleep(5) 
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        print("Parsing the data table...")
        table = soup.find('table', class_='mobile-table')
        if not table:
            print("❌ ERROR: Could not find the table with class 'mobile-table' after loading the page.")
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
    finally:
        # Important to quit the browser session
        driver.quit()

if __name__ == '__main__':
    scrape_oline_rankings()
