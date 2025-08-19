import nfl_data_py as nfl
import pandas as pd
import requests
import time
import os

# --- Configuration ---
YEARS = [2024, 2023, 2022, 2021]
DATA_DIR = 'data/analysis'

# THE FIX: A self-contained dictionary of stadium coordinates.
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
        url = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={lat}&longitude={lon}&start
