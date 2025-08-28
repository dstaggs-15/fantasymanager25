import pandas as pd
import nfl_data_py as nfl
import os
import datetime
from urllib.error import HTTPError
import sys

def get_raw_data():
    """
    Downloads raw NFL data and saves it. This version standardizes all player
    name columns to 'player_display_name' at the source to prevent downstream errors.
    """
    print("--- Starting Raw Data Collection ---")
    current_year = datetime.date.today().year
    YEARS = list(range(current_year - 4, current_year + 1))
    output_dir = os.path.join('docs', 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True)
    weekly_output_path = os.path.join(output_dir, 'weekly_stats_raw.csv')
    roster_output_path = os.path.join(output_dir, 'players_master.csv')
    schedule_output_path = os.path.join(output_dir, 'schedule_raw.csv')

    # --- Download Weekly Stats ---
    all_weekly_data = []
    print(f"📊 Downloading weekly player stats for {YEARS}...")
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
    else:
        print("❌ ERROR: No weekly stats downloaded.")
        sys.exit(1)

    # --- Download Roster/Player Information (only from valid years) ---
    all_rosters = []
    print("📋 Downloading player roster information...")
    for year in YEARS:
        try:
            df = nfl.import_seasonal_data(years=[year], s_type='REG')
            print(f"  {year} roster columns:", df.columns.tolist())
            if all(col in df.columns for col in ['player_id', 'player_name', 'birth_date']):
                all_rosters.append(df)
            else:
                print(f"  ⚠️ Skipping {year}: Missing required columns.")
        except HTTPError:
            print(f"  -> INFO: Roster data for {year} not available. Skipping.")

    if not all_rosters:
        print("❌ ERROR: No valid roster data found. Cannot continue.")
        sys.exit(1)

    # --- Process and Save Player Master List ---
    roster_df = pd.concat(all_rosters, ignore_index=True)

    # Standardize column names
    roster_df = roster_df.rename(columns={
        'player_name': 'player_display_name',
        'team_abbr': 'recent_team'
    })

    # Select final columns (only if they exist)
    final_cols = [col for col in ['player_id', 'player_display_name', 'position', 'recent_team', 'birth_date'] if col in roster_df.columns]
    master_list = roster_df[final_cols].drop_duplicates(subset='player_id', keep='first').copy()

    # Sanity check
    print("🧪 Final columns in players_master.csv:", master_list.columns.tolist())
    master_list.to_csv(roster_output_path, index=False)
    print("✅ Successfully saved Player Master List.")

    # --- Download Schedule ---
    try:
        print("🗓️ Downloading schedule information...")
        schedule_df = nfl.import_schedules(years=YEARS)
        schedule_df.to_csv(schedule_output_path, index=False)
        print("✅ Successfully saved raw schedule data.")
    except Exception as e:
        print(f"❌ ERROR: Failed to download schedule data. Reason: {e}")

    print("--- Raw Data Collection Finished ---")

if __name__ == '__main__':
    get_raw_data()
