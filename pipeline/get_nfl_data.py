import nfl_data_py as nfl
import pandas as pd
import requests
import time
import os

# --- Configuration ---
YEARS = [2024, 2023, 2022, 2021]
DATA_DIR = 'data/analysis'

# A self-contained dictionary of stadium coordinates.
STADIUM_COORDINATES = {
    'ARI': {'lat': 33.5275, 'lon': -112.2625}, 'ATL': {'lat': 33.7556, 'lon': -84.4000},
    'BAL': {'lat': 39.2781, 'lon': -76.6228}, 'BUF': {'lat': 42.7736, 'lon': -78.7869},
    'CAR': {'lat': 35.2258, 'lon': -80.8528}, 'CHI': {'lat': 41.8625, 'lon': -87.6167},
    'CIN': {'lat': 39.0956, 'lon': -84.5161}, 'CLE': {'lat': 41.5061, 'lon': -81.6994},
    'DAL': {'lat': 32.7478, 'lon': -97.0928}, 'DEN': {'lat': 39.7439, 'lon': -105.0200},
    'DET': {'lat': 42.3400, 'lon': -83.0456}, 'GB': {'lat': 44.5014, 'lon': -88.0622},
    'HOU': {'lat': 29.6847, 'lon': -95.4108}, 'IND': {'lat': 39.7600, 'lon': -86.1639},
    'JAX': {'lat': 30.3239, 'lon': -81.6375}, 'KC': {'lat': 39.0489, 'lon': -94.4839},
    'LAC': {'lat': 33.9533, 'lon': -118.2614}, 'LA': {'lat': 33.9533, 'lon': -118.2614},
    'LV': {'lat': 36.0908, 'lon': -115.1836}, 'MIA': {'lat': 25.9581, 'lon': -80.2389},
    'MIN': {'lat': 44.9736, 'lon': -93.2581}, 'NE': {'lat': 42.0908, 'lon': -71.2644},
    'NO': {'lat': 29.9508, 'lon': -90.0811}, 'NYG': {'lat': 40.8136, 'lon': -74.0744},
    'NYJ': {'lat': 40.8136, 'lon': -74.0744}, 'PHI': {'lat': 39.9008, 'lon': -75.1675},
    'PIT': {'lat': 40.4467, 'lon': -80.0158}, 'SEA': {'lat': 47.5953, 'lon': -122.3317},
    'SF': {'lat': 37.4031, 'lon': -121.9694}, 'TB': {'lat': 27.9758, 'lon': -82.5033},
    'TEN': {'lat': 36.1664, 'lon': -86.7714}, 'WAS': {'lat': 38.9078, 'lon': -76.8644},
}

def get_weather(lat, lon, date):
    """
    Fetches historical weather data for a specific location and date from Open-Meteo.
    """
    try:
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={date}&end_date={date}&daily=weathercode,temperature_2m_max,precipitation_sum,windspeed_10m_max"
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
    
    print("Merging weekly data with schedule data...")
    merged_df = pd.merge(weekly_df, schedule_df, on=['season', 'week'], how='left')
    data_df = merged_df[
        (merged_df['recent_team'] == merged_df['home_team']) |
        (merged_df['recent_team'] == merged_df['away_team'])
    ].copy()
    print("Successfully merged player and schedule data.")

    data_df['stadium_latitude'] = data_df['home_team'].map(lambda x: STADIUM_COORDINATES.get(x, {}).get('lat'))
    data_df['stadium_longitude'] = data_df['home_team'].map(lambda x: STADIUM_COORDINATES.get(x, {}).get('lon'))

    # THE FIX: Convert the 'gameday' column to a proper datetime format.
    data_df['gameday'] = pd.to_datetime(data_df['gameday'])

    print("Fetching historical weather for outdoor games. This will take several minutes...")
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
            time.sleep(0.5)
        else:
            print(f" - Skipping weather for game {game['game_id']} (team: {game['home_team']}) due to missing location data.")

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
