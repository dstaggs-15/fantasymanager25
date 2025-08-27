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

    # --- 1. Define URL and Headers ---
    # PFF's offensive line rankings page
    url = "https://www.pff.com/nfl/grades/position/t" 
    
    # We need to send headers to mimic a real browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    output_path = os.path.join('docs', 'data', 'raw', 'oline_rankings.csv')

    # --- 2. Scrape the Webpage ---
    try:
        print(f"Fetching data from {url}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status() # This will raise an error for bad responses (4xx or 5xx)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the table containing the data
        table = soup.find('table') 
        if not table:
            print("❌ ERROR: Could not find the data table on the page. The website structure may have changed.")
            return

        # --- 3. Extract and Clean the Data ---
        print("Parsing the data table...")
        rows = table.find_all('tr')
        
        team_data = []
        for row in rows[1:]: # Skip the header row
            cols = row.find_all('td')
            if len(cols) > 1:
                team_name_div = cols[0].find('div', class_='text-div')
                if team_name_div:
                    team_name = team_name_div.get_text(strip=True)
                    team_data.append(team_name)

        if not team_data:
            print("❌ ERROR: No team data could be extracted. The website structure may have changed.")
            return

        # Create a DataFrame with ranks
        df = pd.DataFrame({'team': team_data})
        df['rank'] = df.index + 1
        
        # --- 4. Save to CSV ---
        df.to_csv(output_path, index=False)
        print(f"✅ Successfully scraped and saved O-line rankings to: {output_path}")

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to fetch the webpage. Reason: {e}")
    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred. Reason: {e}")

if __name__ == '__main__':
    scrape_oline_rankings()
