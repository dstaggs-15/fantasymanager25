# pipeline/get_raw_data.py
import pandas as pd
import nfl_data_py as nfl
import os
import datetime
import sys

def get_raw_data():
    """
    Downloads raw NFL data. This version is simplified to only download the
    weekly stats and schedule data, which are known to be reliable.
    """
    print("--- Starting Raw Data Collection ---")
    current_year = datetime.date.today().year
    YEARS = list(range(current_year - 4, current_year + 1))
    output_dir = os.path.join('docs', 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True)
    weekly_output_path = os.path.join(output_dir, 'weekly_stats_raw.csv')
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
    else:
        print("❌ CRITICAL ERROR: No weekly stats could be downloaded.")
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
