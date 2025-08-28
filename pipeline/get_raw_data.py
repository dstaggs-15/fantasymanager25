# pipeline/get_raw_data.py
import pandas as pd
import nfl_data_py as nfl
import os
import datetime
import sys

def get_raw_data():
    """
    Downloads raw NFL data. This version is rewritten from scratch to use the
    correct, stable column names from the nfl-data-py library.
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
    print(f"Downloading weekly player stats for {YEARS}...")
    for year in YEARS:
        try:
            yearly_df = nfl.import_weekly_data(years=[year])
            all_weekly_data.append(yearly_df)
        except Exception:
            print(f"  -> INFO: Weekly data for {year} not available. Skipping.")
    if all_weekly_data:
        weekly_df = pd.concat(all_weekly_data, ignore_index=True)
        weekly_df.to_csv(weekly_output_path, index=False)
        print("✅ Successfully saved raw weekly stats.")

    # --- Download Player Master List (Definitive Method) ---
    try:
        print("Downloading master player list...")
        players_df = nfl.import_players()
        
        # DEFINITIVE FIX: Use the correct column names revealed by the debug log.
        required_cols = ['gsis_id', 'display_name', 'position', 'latest_team', 'birth_date']
        
        # Validate that these columns exist
        missing_cols = [col for col in required_cols if col not in players_df.columns]
        if missing_cols:
            print(f"❌ CRITICAL ERROR: The players data is missing required columns: {missing_cols}")
            sys.exit(1)

        master_list = players_df[required_cols].copy()
        
        # Standardize column names for the rest of our project
        master_list.rename(columns={
            'gsis_id': 'player_id',
            'display_name': 'player_display_name',
            'latest_team': 'recent_team'
        }, inplace=True)
        
        master_list.to_csv(roster_output_path, index=False)
        print(f"✅ Successfully saved Player Master List with columns: {master_list.columns.tolist()}")
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Failed to create Player Master List. Reason: {e}")
        sys.exit(1)

    # --- Download Schedule ---
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
