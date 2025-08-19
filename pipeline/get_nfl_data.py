import nfl_data_py as nfl
import pandas as pd
import requests
import time
import os

# --- Configuration ---
YEARS = [2024, 2023, 2022, 2021]
DATA_DIR = 'data/analysis'

# This function is no longer being called, but we'll leave it for later.
def get_weather(lat, lon, date):
    # ...
    pass

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

    # --------------------------------------------------------------------
    # --- WEATHER FETCHING DISABLED FOR NOW ---
    print("Skipping weather data collection to avoid network errors.")
    # 
    # print("Downloading stadium location data...")
    # STADIUM_COORDINATES = { ... } # Dictionary is still here but not used
    # data_df['stadium_latitude'] = data_df['home_team'].map(lambda x: STADIUM_COORDINATES.get(x, {}).get('lat'))
    # data_df['stadium_longitude'] = data_df['home_team'].map(lambda x: STADIUM_COORDINATES.get(x, {}).get('lon'))
    # data_df['gameday'] = pd.to_datetime(data_df['gameday'])
    #
    # print("Fetching historical weather for outdoor games...")
    # # ... entire weather fetching loop is skipped ...
    #
    # --------------------------------------------------------------------

    output_path = os.path.join(DATA_DIR, 'nfl_data_with_weather.csv')
    data_df.to_csv(output_path, index=False)
    
    print(f"\n✅ --- Data Collection Complete! ---")
    print(f"Final dataset saved to: {output_path}")

if __name__ == '__main__':
    main()
