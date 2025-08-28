# pipeline/get_raw_data.py
import pandas as pd
import nfl_data_py as nfl
import os
import datetime
import sys

def get_raw_data():
    """
    Downloads raw NFL data. This version is rewritten from scratch to be fully
    resilient to changes in the source data's column names.
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

    # --- Download Player Master List (Definitive, Robust Method) ---
    try:
        print("Downloading master player list...")
        players_df = nfl.import_players()
        
        # For debugging, let's see what columns we actually get
        print(f"DEBUG: Columns available in players data: {players_df.columns.tolist()}")

        # Define our standard names and potential aliases from the library
        column_map = {
            'player_display_name': ['player_display_name', 'player_name', 'name'],
            'player_id': ['player_id'],
            'position': ['position', 'pos'],
            'recent_team': ['team_abbr', 'team'],
            'birth_date': ['birth_date']
        }

        master_list = pd.DataFrame()
        found_cols = {}

        for standard_name, potential_aliases in column_map.items():
            for alias in potential_aliases:
                if alias in players_df.columns:
                    master_list[standard_name] = players_df[alias]
                    found_cols[standard_name] = alias
                    break # Move to the next standard name once an alias is found
        
        print(f"INFO: Mapped columns as follows: {found_cols}")
        
        # Validate that we found the critical columns
        if 'player_id' not in master_list.columns or 'player_display_name' not in master_list.columns:
            print("❌ CRITICAL ERROR: Could not find required 'player_id' or a valid player name column.")
            sys.exit(1)
        
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
