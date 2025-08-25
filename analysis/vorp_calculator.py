# analysis/vorp_calculator.py

import pandas as pd
import json
import os

def calculate_ppg():
    """
    Calculates the Points Per Game (PPG) for each player based on the master data file.
    It filters for players who have played a meaningful number of games.
    """
    print("Starting PPG calculation for VORP tool...")

    # --- CORRECTED FILE PATHS ---
    # Paths are now relative to the project's root directory, where the workflow runs.
    master_data_path = os.path.join('docs', 'data', 'master_data.csv')
    output_folder = os.path.join('docs', 'data', 'analysis')
    output_path = os.path.join(output_folder, 'player_ppg.json')

    # Create the output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Load the master data
    try:
        df = pd.read_csv(master_data_path)
    except FileNotFoundError:
        print(f"Error: The file {master_data_path} was not found.")
        print("Please run the `pipeline/get_nfl_data.py` script first.")
        return

    # --- PPG Calculation Logic ---
    latest_season = df['season'].max()
    print(f"Analyzing data for the {latest_season} season.")
    df_season = df[df['season'] == latest_season]

    player_stats = df_season.groupby(['player_id', 'player_name', 'position', 'team']).agg(
        total_points=('fantasy_points', 'sum'),
        games_played=('fantasy_points', 'count')
    ).reset_index()

    min_games_played = 4
    player_stats = player_stats[player_stats['games_played'] >= min_games_played]

    player_stats['ppg'] = round(player_stats['total_points'] / player_stats['games_played'], 2)

    final_data = player_stats[['player_name', 'team', 'position', 'ppg']].copy()
    final_data.sort_values(by='ppg', ascending=False, inplace=True)

    players_json = final_data.to_dict(orient='records')

    with open(output_path, 'w') as f:
        json.dump(players_json, f, indent=4)

    print(f"Successfully created PPG data at: {output_path}")
    print("You can now open the vorp.html page.")

if __name__ == '__main__':
    calculate_ppg()
