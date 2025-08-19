import nfl_data_py as nfl
import pandas as pd
import requests
import time
import os

# --- Configuration ---
YEARS = [2024, 2023, 2022, 2021]
DATA_DIR = 'docs/data/analysis'

def main():
    print("--- Starting NFL Data Collection Engine ---")
    os.makedirs(DATA_DIR, exist_ok=True)

    print(f"Downloading weekly player data for seasons: {YEARS}...")
    weekly_df = nfl.import_weekly_data(years=YEARS, downcast=True)
    
    print("Downloading schedule data...")
    schedule_df = nfl.import_schedules(years=YEARS)
    
    print("Merging weekly data with schedule data...")
    merged_df = pd.merge(weekly_df, schedule_df, on=['season', 'week'], how='left')
    data_df = merged_df[
        (merged_df['recent_team'] == merged_df['home_team']) |
        (merged_df['recent_team'] == merged_df['away_team'])
    ].copy()
    print("Successfully merged player and schedule data.")

    # --- WEATHER FETCHING IS DISABLED ---
    print("Skipping weather data collection as requested.")

    output_path = os.path.join(DATA_DIR, 'nfl_data.csv') # Renamed for clarity
    data_df.to_csv(output_path, index=False)
    
    print(f"\n✅ --- Data Collection Complete! ---")
    print(f"Final dataset saved to: {output_path}")

if __name__ == '__main__':
    main()
