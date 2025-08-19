import nfl_data_py as nfl
import pandas as pd
import requests
import time
import os

# --- Configuration ---
YEARS = [2023, 2022, 2021] # The seasons we want to analyze
DATA_DIR = 'data/analysis' # A new folder to store our analysis data

# --- Main Functions ---
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
        response.raise_for_status() # Raise an exception for bad status codes
        weather_data = response.json().get('daily', {})
        
        # We only want the first day's data
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
    
    # Create directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. Download weekly player data
    print(f"Downloading weekly player data for seasons: {YEARS}...")
    weekly_df = nfl.import_weekly_data(years=YEARS, downcast=True)
    
    # 2. Download schedule data to get game locations
    print("Downloading schedule data...")
    schedule_df = nfl.import_schedules(years=YEARS)
    
    # 3. Download team descriptions to get stadium info
    print("Downloading team description data...")
    teams_df = nfl.import_team_desc()

    # 4. Merge data to find game locations and dome status
    print("Merging datasets...")
    # Select only the columns we need from the schedule
    schedule_subset = schedule_df[['game_id', 'gameday', 'location', 'roof']]
    # Merge weekly data with the schedule to get game info for each player's performance
    data_df = pd.merge(weekly_df, schedule_subset, on='game_id', how='left')

    # 5. Get stadium locations (latitude/longitude)
    stadiums_df = nfl.import_stadiums()
    stadium_locations = stadiums_df[['stadium_location', 'stadium_latitude', 'stadium_longitude']].rename(columns={'stadium_location': 'location'})
    data_df = pd.merge(data_df, stadium_locations, on='location', how='left')

    # 6. Fetch weather for outdoor games
    print("Fetching historical weather for outdoor games. This will take several minutes...")
    outdoor_games = data_df[data_df['roof'] != 'dome'].copy()
    
    weather_cache = {}
    weather_results = []

    # Iterate through each outdoor game to get its weather
    for index, game in outdoor_games.iterrows():
        game_id = game['game_id']
        if game_id in weather_cache:
            weather_results.append(weather_cache[game_id])
        else:
            date_str = game['gameday'].strftime('%Y-%m-%d')
            lat, lon = game['stadium_latitude'], game['stadium_longitude']
            
            if pd.notna(lat) and pd.notna(lon):
                print(f" - Getting weather for game {game_id} on {date_str}")
                weather = get_weather(lat, lon, date_str)
                if weather:
                    weather['game_id'] = game_id
                    weather_cache[game_id] = weather
                    weather_results.append(weather)
                time.sleep(0.5) # Be respectful to the API and avoid rate limiting
            else:
                print(f" - Skipping weather for game {game_id} due to missing location data.")

    # 7. Merge weather data back into the main dataset
    if weather_results:
        weather_df = pd.DataFrame(weather_results).drop_duplicates()
        data_df = pd.merge(data_df, weather_df, on='game_id', how='left')
        print("Successfully merged weather data.")
    else:
        print("No weather data was fetched.")

    # 8. Save the final, enriched dataset
    output_path = os.path.join(DATA_DIR, 'nfl_data_with_weather.csv')
    data_df.to_csv(output_path, index=False)
    
    print(f"\n✅ --- Data Collection Complete! ---")
    print(f"Final dataset saved to: {output_path}")

if __name__ == '__main__':
    main()
