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
    print("--- Starting Raw Data Collection ---")
    current_year = datetime.date.today().year
    YEARS = list(range(current_year - 4, current_year + 1))
    output_dir = os.path.join('docs', 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True)
    weekly_output_path = os.path.join(output_dir, 'weekly_stats_raw.csv')
    roster_output_path = os.path.join(output_dir, 'players_master.csv')
    schedule_output_path = os.path.join(output_dir, 'schedule_raw.csv')

    # Download Weekly Stats
    all_weekly_data = []
    print(f"Downloading weekly player stats for {YEARS}...")
    for year in YEARS:
        try:
            yearly_df = nfl.import_weekly_data(years=[year])
            all_weekly_data.append(yearly_df)
        except HTTPError:
            print(f"  -> INFO: Weekly data for {year} not available. Skipping.")
    if all_weekly_data:
        weekly_df = pd.concat(all_weekly_data, ignore_index=True)
        weekly_df.to_csv(weekly_output_path, index=False)
        print("✅ Successfully saved raw weekly stats.")

    # Download Roster/Player Information (Reliable Method)
    try:
        print("Downloading player roster information...")
        # CORRECTED: Using a more stable function to get player info.
        seasonal_df = nfl.import_seasonal_data(years=YEARS, s_type='REG')
        roster_cols = ['player_id', 'player_display_name', 'position', 'team_abbr']
        master_list = seasonal_df[roster_cols].drop_duplicates(subset='player_id', keep='first')
        master_list.rename(columns={'team_abbr': 'recent_team'}, inplace=True)
        master_list.to_csv(roster_output_path, index=False)
        print("✅ Successfully saved Player Master List.")
    except Exception as e:
        print(f"❌ ERROR: Failed to download roster data. Reason: {e}")

    # Download Schedule
    try:
        print("Downloading schedule information...")
        schedule_df = nfl.import_schedules(years=YEARS)
        schedule_df.to_csv(schedule_output_path, index=False)
        print("✅ Successfully saved raw schedule data.")
    except Exception as e:
        print(f"❌ ERROR: Failed to download schedule data. Reason: {e}")
    print("--- Raw Data Collection Finished ---")

if __name__ == '__main__':
    get_raw_data()
