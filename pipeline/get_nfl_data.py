import nfl_data_py as nfl
import pandas as pd
import requests
import time
import os

# --- Configuration ---
YEARS = [2024, 2023, 2022, 2021] # THE CHANGE: Added the 2024 season
DATA_DIR = 'data/analysis'

def get_weather(lat, lon, date):
    """
    Fetches historical weather data for a specific location and date from Open-Meteo.
    """
    try:
        url = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={lat}&longitude={lon}&start_date={date}&end_date={date}"
            f"&daily=weathercode,temperature_2m_max,precipitation_sum,windspeed_10m_max"
        )
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        weather_data = response.json().get('daily', {})
        
        return {
            'weather_code': weather_data.get('weathercode', [None])[0],
            'temp_max_c': weather_data.get('temperature_2m_max', [None])[0],
            'precipitation_mm': weather_data.get('precipitation_sum', [None])[0],
            'wind_speed_kmh': weather_data.get('windspeed_10m_max', [None])[0]
        }
    except Exception as e:
        print(f"  - Could not fetch weather for {date} at ({lat}, {lon}). Error: {e}")
        return None

def main():
    print("--- Starting NFL Data Collection Engine ---")
    os.makedirs(DATA_DIR, exist_ok=True)

    print(f"Downloading weekly player data for seasons: {YEARS}...")
    weekly_df = nfl.import_weekly_data(years=YEARS, downcast=True)
    
    print("Downloading schedule data...")
    schedule_df = nfl.import_schedules(years=YEARS)

    # A more robust way to merge the datasets
    print("Merging weekly data with schedule data...")
    # First, merge the two big tables on the columns they share: season and week
    merged_df = pd.merge(weekly_df, schedule_df, on=['season', 'week'], how='left')

    # Now, filter the merged results to only keep rows where the player's team
    # matches either the home or away team for the game.
    data_df = merged_df[
        (merged_df['recent_team'] == merged_df['home_team']) |
        (merged_df['recent_team'] == merged_df['away_team'])
    ].copy()
    print("Successfully merged player and schedule data.")
    
    print("Downloading stadium location data...")
    stadiums_df = nfl.import_stadiums()
    stadium_locations = stadiums_df[['stadium_location', 'stadium_latitude', 'stadium_longitude']].rename(columns={'stadium_location': 'location'})
    data_df = pd.merge(data_df, stadium_locations, on='location', how='left')

    print("Fetching historical weather for outdoor games. This will take several minutes...")
    # Get unique games to avoid redundant weather API calls
    outdoor_games = data_df[data_df['roof'] != 'dome'].drop_duplicates(subset=['game_id']).copy()
    
    weather_cache = {}
    
    for index, game in outdoor_games.iterrows():
        game_id = game['game_id']
        date_str = game['gameday'].strftime('%Y-%m-%d')
        lat, lon = game['stadium_latitude'], game['stadium_longitude']
        
        if pd.notna(lat) and pd.notna(lon):
            print(f" - Getting weather for game {game_id} on {date_str}")
            weather = get_weather(lat, lon, date_str)
            if weather:
                weather_cache[game_id] = weather
            time.sleep(0.5) # Be respectful to the API
        else:
            print(f" - Skipping weather for game {game_id} due to missing location data.")

    if weather_cache:
        weather_df = pd.DataFrame.from_dict(weather_cache, orient='index')
        weather_df.index.name = 'game_id'
        data_df = pd.merge(data_df, weather_df, on='game_id', how='left')
        print("Successfully merged weather data.")
    else:
        print("No weather data was fetched.")

    output_path = os.path.join(DATA_DIR, 'nfl_data_with_weather.csv')
    data_df.to_csv(output_path, index=False)
    
    print(f"\n✅ --- Data Collection Complete! ---")
    print(f"Final dataset saved to: {output_path}")

if __name__ == '__main__':
    main()
