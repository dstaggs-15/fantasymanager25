# pipeline/get_raw_data.py
import pandas as pd
import nfl_data_py as nfl
import os
import datetime
from urllib.error import HTTPError

def get_raw_data():
    """
    Downloads raw NFL data (weekly stats and player rosters) for the last five seasons
    and saves them to separate CSV files in the 'docs/data/raw/' directory.
    This script is the foundational first step in our new data pipeline.
    """
    print("--- Phase 1, Step 1: Starting Raw Data Collection ---")

    # --- 1. Define Years and Output Paths ---
    current_year = datetime.date.today().year
    YEARS = list(range(current_year - 4, current_year + 1))
    
    output_dir = os.path.join('docs', 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True)
    
    weekly_output_path = os.path.join(output_dir, 'weekly_stats_raw.csv')
    roster_output_path = os.path.join(output_dir, 'players_master.csv')

    print(f"Attempting to fetch data for seasons: {YEARS}")

    # --- 2. Download Weekly Player Stats (with robust error handling for each year) ---
    all_weekly_data = []
    print("Downloading weekly player stats...")
    for year in YEARS:
        try:
            print(f"  -> Fetching weekly data for {year}...")
            yearly_df = nfl.import_weekly_data(years=[year])
            all_weekly_data.append(yearly_df)
        except HTTPError:
            print(f"  -> INFO: Weekly data for {year} not available yet. Skipping.")
        except Exception as e:
            print(f"  -> ❌ ERROR: An unexpected error occurred for year {year}: {e}. Skipping.")

    if all_weekly_data:
        weekly_df = pd.concat(all_weekly_data, ignore_index=True)
        weekly_df.to_csv(weekly_output_path, index=False)
        print(f"✅ Successfully saved raw weekly stats to: {weekly_output_path}")
    else:
        print("❌ CRITICAL: No weekly data could be downloaded.")


    # --- 3. Download Roster/Player Information (Our "Player Master List") ---
    try:
        print("Downloading player roster information to create Player Master List...")
        # CORRECTED: Using the definitive function name for modern library versions.
        roster_df = nfl.import_roster_data(years=YEARS)
        
        roster_df.sort_values(by='season', ascending=False, inplace=True)
        master_list = roster_df.drop_duplicates(subset='player_id', keep='first')
        
        master_list.to_csv(roster_output_path, index=False)
        print(f"✅ Successfully saved Player Master List to: {roster_output_path}")
    except Exception as e:
        print(f"❌ ERROR: Failed to download or save roster data. Reason: {e}")

    print("--- Raw Data Collection Finished ---")

if __name__ == '__main__':
    get_raw_data()
