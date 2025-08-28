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

    # Download Roster/Player Information (with robust year-by-year error handling)
    all_seasonal_data = []
    print("Downloading player roster information...")
    for year in YEARS:
        try:
            seasonal_df_year = nfl.import_seasonal_data(years=[year], s_type='REG')
            all_seasonal_data.append(seasonal_df_year)
        except HTTPError:
            print(f"  -> INFO: Seasonal/Roster data for {year} not available. Skipping.")
            
    if all_seasonal_data:
        roster_df = pd.concat(all_seasonal_data, ignore_index=True)
        # Use the actual columns available in this dataset
        roster_cols = ['player_id', 'player_name', 'position', 'team_abbr', 'birth_date']
        cols_to_select = [col for col in roster_cols if col in roster_df.columns]
        master_list = roster_df[cols_to_select].drop_duplicates(subset='player_id', keep='first')
        master_list.rename(columns={'team_abbr': 'recent_team'}, inplace=True)
        master_list.to_csv(roster_output_path, index=False)
        print("✅ Successfully saved Player Master List.")
    else:
        print("❌ ERROR: No roster data could be downloaded.")

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
