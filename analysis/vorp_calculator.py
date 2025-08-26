# analysis/vorp_calculator.py

import pandas as pd
import json
import os
import sys # Import the sys library to exit gracefully

def calculate_ppg():
    """
    Calculates the Points Per Game (PPG) for each player based on the master data file.
    It filters for players who have played a meaningful number of games.
    """
    print("Starting PPG calculation for VORP tool...")

    # Paths are relative to the project's root directory
    master_data_path = os.path.join('docs', 'data', 'master_data.csv')
    output_folder = os.path.join('docs', 'data', 'analysis')
    output_path = os.path.join(output_folder, 'player_ppg.json')

    os.makedirs(output_folder, exist_ok=True)

    # Load the master data
    try:
        df = pd.read_csv(master_data_path)
    except FileNotFoundError:
        print(f"Error: The input file {master_data_path} was not found.")
        sys.exit(1) # Exit the script with an error code

    # --- NEW: Check if the input dataframe is empty ---
    if df.empty:
        print(f"Error: The input file {master_data_path} is empty. Cannot calculate PPG.")
        sys.exit(1) # Exit the script with an error code

    print(f"Successfully loaded {master_data_path} with {len(df)} rows.")

    latest_season = df['season'].max()
    print(f"Analyzing data for the {latest_season} season.")
    df_season = df[df['season'] == latest_season]

    player_stats = df_season.groupby(['player_id', 'player_name', 'position', 'team']).agg(
        total_points=('fantasy_points', 'sum'),
        games_played=('fantasy_points', 'count')
    ).reset_index()

    min_games_played = 4
    player_stats = player_stats[player_stats['games_played'] >= min_games_played]

    if player_stats.empty:
        print("Warning: No players met the minimum game requirement. Output will be empty.")
    
    player_stats['ppg'] = round(player_stats['total_points'] / player_stats['games_played'], 2)
    final_data = player_stats[['player_name', 'team', 'position', 'ppg']].copy()
    final_data.sort_values(by='ppg', ascending=False, inplace=True)
    players_json = final_data.to_dict(orient='records')

    with open(output_path, 'w') as f:
        json.dump(players_json, f, indent=4)

    print(f"Successfully created PPG data at: {output_path}")

if __name__ == '__main__':
    calculate_ppg()
