# analysis/consistency_analyzer.py
import pandas as pd
import json
import os
import sys
import numpy as np

def analyze_consistency():
    """
    Analyzes player performance to calculate consistency metrics like standard
    deviation, ceiling games, and floor games.
    """
    print("\n--- Starting Consistency Analysis ---")

    processed_data_path = os.path.join('docs', 'data', 'processed', 'weekly_data_processed.csv')
    reports_dir = os.path.join('docs', 'data', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    output_path = os.path.join(reports_dir, 'consistency_report.json')

    try:
        df = pd.read_csv(processed_data_path)
        print(f"Successfully loaded processed data from: {processed_data_path}")
    except FileNotFoundError:
        print(f"❌ CRITICAL ERROR: Processed data file not found.")
        sys.exit(1)

    latest_season = df['season'].max()
    if df[df['season'] == latest_season]['week'].max() < 4:
        latest_season = latest_season - 1
    
    print(f"Analyzing player consistency for the {latest_season} season.")
    df_season = df[df['season'] == latest_season].copy()

    player_ids = df_season['player_id'].unique()
    consistency_data = []
    for player_id in player_ids:
        player_df = df_season[df_season['player_id'] == player_id].copy()
        games_played = len(player_df)
        if games_played < 5:
            continue
        player_info = player_df.iloc[0]
        avg_points = player_df['fantasy_points'].mean()
        std_dev = player_df['fantasy_points'].std()
        ceiling_threshold = np.percentile(player_df['fantasy_points'], 75)
        floor_threshold = np.percentile(player_df['fantasy_points'], 25)
        avg_ceiling = player_df[player_df['fantasy_points'] >= ceiling_threshold]['fantasy_points'].mean()
        avg_floor = player_df[player_df['fantasy_points'] <= floor_threshold]['fantasy_points'].mean()
        good_game_threshold = avg_points * 1.2
        bust_game_threshold = avg_points * 0.8
        good_games_pct = (len(player_df[player_df['fantasy_points'] > good_game_threshold]) / games_played) * 100
        bust_games_pct = (len(player_df[player_df['fantasy_points'] < bust_game_threshold]) / games_played) * 100

        consistency_data.append({
            'player_display_name': player_info['player_display_name'],
            'position': player_info['position'],
            'recent_team': player_info['recent_team'],
            'games_played': games_played,
            'ppg': round(avg_points, 2),
            'std_dev': round(std_dev, 2),
            'avg_ceiling': round(avg_ceiling, 2),
            'avg_floor': round(avg_floor, 2),
            'good_games_pct': round(good_games_pct, 1),
            'bust_games_pct': round(bust_games_pct, 1)
        })

    consistency_data.sort(key=lambda x: x['ppg'], reverse=True)

    with open(output_path, 'w') as f:
        json.dump(consistency_data, f, indent=4)

    print(f"✅ Successfully created consistency analysis report at: {output_path}")
    # CORRECTED: Added the closing parenthesis and quote.
    print("--- Consistency Analysis Finished ---")

if __name__ == '__main__':
    analyze_consistency()
