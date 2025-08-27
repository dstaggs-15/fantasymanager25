# pipeline/get_raw_data.py
import pandas as pd
import nfl_data_py as nfl
import os
import datetime

def get_raw_data():
    """
    Downloads raw NFL data (weekly stats and player rosters) for the last five seasons
    and saves them to separate CSV files in the 'docs/data/raw/' directory.
    This script is the foundational first step in our new data pipeline.
    """
    print("--- Phase 1, Step 1: Starting Raw Data Collection ---")

    # --- 1. Define Years and Output Paths ---
    current_year = datetime.date.today().year
    # Fetch last 4 completed seasons plus the current season for a 5-year historical window.
    # In August 2025, this will be 2021, 2022, 2023, 2024, 2025.
    YEARS = list(range(current_year - 4, current_year + 1))
    
    output_dir = os.path.join('docs', 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True) # Create the directory if it doesn't exist
    
    weekly_output_path = os.path.join(output_dir, 'weekly_stats_raw.csv')
    roster_output_path = os.path.join(output_dir, 'players_master.csv')

    print(f"Attempting to fetch data for seasons: {YEARS}")

    # --- 2. Download Weekly Player Stats ---
    try:
        print("Downloading weekly player stats...")
        # We explicitly add the necessary parquet engines to ensure this works.
        weekly_df = nfl.import_weekly_data(years=YEARS, engine='pyarrow')
        weekly_df.to_csv(weekly_output_path, index=False)
        print(f"✅ Successfully saved raw weekly stats to: {weekly_output_path}")
    except Exception as e:
        print(f"❌ ERROR: Failed to download or save weekly stats. Reason: {e}")

    # --- 3. Download Roster/Player Information (Our "Player Master List") ---
    try:
        print("Downloading player roster information to create Player Master List...")
        roster_df = nfl.import_rosters(years=YEARS)
        
        # We only need a clean list of players, so we'll drop duplicates
        # based on the player ID, keeping the most recent entry.
        roster_df.sort_values(by='season', ascending=False, inplace=True)
        master_list = roster_df.drop_duplicates(subset='player_id', keep='first')
        
        master_list.to_csv(roster_output_path, index=False)
        print(f"✅ Successfully saved Player Master List to: {roster_output_path}")
    except Exception as e:
        print(f"❌ ERROR: Failed to download or save roster data. Reason: {e}")

    print("--- Raw Data Collection Finished ---")

if __name__ == '__main__':
    get_raw_data()
