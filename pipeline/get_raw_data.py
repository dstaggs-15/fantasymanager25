# pipeline/get_raw_data.py
import pandas as pd
import nfl_data_py as nfl
import os
import datetime
from urllib.error import HTTPError

def get_raw_data():
    """
    Downloads raw NFL data (weekly stats, player rosters, and schedules) for the last five seasons
    and saves them to separate CSV files in the 'docs/data/raw/' directory.
    """
    print("--- Phase 1, Step 1: Starting Raw Data Collection ---")

    current_year = datetime.date.today().year
    YEARS = list(range(current_year - 4, current_year + 1))
    
    output_dir = os.path.join('docs', 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True)
    
    weekly_output_path = os.path.join(output_dir, 'weekly_stats_raw.csv')
    roster_output_path = os.path.join(output_dir, 'players_master.csv')
    schedule_output_path = os.path.join(output_dir, 'schedule_raw.csv')

    print(f"Attempting to fetch data for seasons: {YEARS}")

    # --- Download Weekly Player Stats ---
    all_weekly_data = []
    print("Downloading weekly player stats...")
    for year in YEARS:
        try:
            yearly_df = nfl.import_weekly_data(years=[year])
            all_weekly_data.append(yearly_df)
        except HTTPError:
            print(f"  -> INFO: Weekly data for {year} not available yet. Skipping.")

    if all_weekly_data:
        weekly_df = pd.concat(all_weekly_data, ignore_index=True)
        weekly_df.to_csv(weekly_output_path, index=False)
        print(f"✅ Successfully saved raw weekly stats to: {weekly_output_path}")

    # --- Download Roster/Player Information ---
    try:
        print("Downloading player roster information...")
        # CORRECTED: Using the older, more stable function name 'import_rosters'.
        roster_df = nfl.import_rosters(years=YEARS)
        roster_df.sort_values(by='season', ascending=False, inplace=True)
        master_list = roster_df.drop_duplicates(subset='player_id', keep='first')
        master_list.to_csv(roster_output_path, index=False)
        print(f"✅ Successfully saved Player Master List to: {roster_output_path}")
    except Exception as e:
        print(f"❌ ERROR: Failed to download or save roster data. Reason: {e}")

    # --- Download Schedule Information ---
    try:
        print("Downloading schedule information...")
        schedule_df = nfl.import_schedules(years=YEARS)
        schedule_df.to_csv(schedule_output_path, index=False)
        print(f"✅ Successfully saved raw schedule data to: {schedule_output_path}")
    except Exception as e:
        print(f"❌ ERROR: Failed to download or save schedule data. Reason: {e}")

    print("--- Raw Data Collection Finished ---")

if __name__ == '__main__':
    get_raw_data()
