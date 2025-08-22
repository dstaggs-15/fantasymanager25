import pandas as pd
import os
import numpy as np
import json

# --- Configuration ---
DATA_FILE = os.path.join('docs', 'data', 'analysis', 'nfl_data.csv')
OUTPUT_DIR = 'docs/data/analysis'
ANALYSIS_SEASON = 2024
REPLACEMENT_LEVELS = {'QB': 11, 'RB': 21, 'WR': 21, 'TE': 11}

def calculate_fantasy_points(df):
    # (This function is unchanged)
    df['fantasy_points_custom'] = 0.0
    scoring_rules = {
        'passing_yards': 0.05, 'passing_tds': 4, 'interceptions': -2, 'passing_2pt_conversions': 2,
        'rushing_yards': 0.1, 'rushing_tds': 6, 'rushing_2pt_conversions': 2, 'rushing_first_downs': 1,
        'receptions': 1, 'receiving_yards': 0.1, 'receiving_tds': 6, 'receiving_2pt_conversions': 2,
        'receiving_first_downs': 0.5, 'fumbles_lost': -2, 'special_teams_tds': 6
    }
    for column, points in scoring_rules.items():
        if column in df.columns:
            df['fantasy_points_custom'] += df[column].fillna(0) * points
    return df

def main():
    print("--- Starting VORP and Stats Calculator ---")
    
    try:
        df = pd.read_csv(DATA_FILE, low_memory=False)
    except FileNotFoundError:
        print(f"❌ ERROR: Data file not found.")
        return

    df = calculate_fantasy_points(df)
    
    # Calculate per-game averages for key stats
    stats_to_average = [
        'fantasy_points_custom', 'passing_yards', 'passing_tds', 'interceptions',
        'rushing_yards', 'rushing_tds', 'receptions', 'receiving_yards', 'receiving_tds'
    ]
    
    # Group by player to get their season-long stats
    player_season_stats = df.groupby(['player_id', 'player_display_name', 'position', 'season']).agg(
        games_played=('week', 'nunique'),
        **{stat: (stat, 'sum') for stat in stats_to_average}
    ).reset_index()

    # Calculate per-game stats
    for stat in stats_to_average:
        player_season_stats[f'{stat}_pg'] = player_season_stats[stat] / player_season_stats['games_played']

    # Filter for the most recent season for our main analysis
    last_season_stats = player_season_stats[player_season_stats['season'] == ANALYSIS_SEASON].copy()
    last_season_stats = last_season_stats.rename(columns={'fantasy_points_custom_pg': 'ppg'})

    vorp_data = []
    print("Calculating VORP for each position...")
    for pos, rank_cutoff in REPLACEMENT_LEVELS.items():
        pos_df = last_season_stats[last_season_stats['position'] == pos].sort_values(by='ppg', ascending=False).reset_index(drop=True)
        
        if len(pos_df) > rank_cutoff:
            replacement_value = pos_df.loc[rank_cutoff - 1, 'ppg'] # -1 because index is 0-based
        else:
            replacement_value = 0
            
        pos_df['vorp'] = pos_df['ppg'] - replacement_value
        vorp_data.append(pos_df)

    final_df = pd.concat(vorp_data).sort_values(by='vorp', ascending=False)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'vorp_analysis.json')
    
    report = {
        'season': ANALYSIS_SEASON,
        'players': final_df.round(2).to_dict('records')
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✅ VORP analysis report with detailed stats saved to {output_path}")

if __name__ == '__main__':
    main()
