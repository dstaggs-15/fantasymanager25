# pipeline/get_oline_rankings.py
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

def scrape_oline_rankings():
    """
    Scrapes the latest offensive line rankings from Pro Football Focus (PFF)
    and saves them to a CSV file.
    """
    print("\n--- Starting O-Line Rankings Scraper ---")

    url = "https://www.pff.com/nfl/grades/position/t" 
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    output_path = os.path.join('docs', 'data', 'raw', 'oline_rankings.csv')

    try:
        print(f"Fetching data from {url}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # CORRECTED: Using a more specific selector to find the table container
        table_container = soup.find('div', class_='g-container--grades')
        if not table_container:
            print("❌ ERROR: Could not find the data table container. The website structure may have changed.")
            return
            
        table = table_container.find('table')
        if not table:
            print("❌ ERROR: Could not find the data table within the container.")
            return

        print("Parsing the data table...")
        rows = table.find_all('tr')
        team_data = []
        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) > 1:
                team_name_div = cols[0].find('div', class_='text-div')
                if team_name_div:
                    team_data.append(team_name_div.get_text(strip=True))

        df = pd.DataFrame({'team': team_data})
        df['rank'] = df.index + 1
        
        df.to_csv(output_path, index=False)
        print(f"✅ Successfully scraped and saved O-line rankings to: {output_path}")

    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred. Reason: {e}")

if __name__ == '__main__':
    scrape_oline_rankings()
