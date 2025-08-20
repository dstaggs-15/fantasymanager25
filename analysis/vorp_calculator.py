import pandas as pd
import os
import numpy as np
import json

# --- Configuration ---
DATA_FILE = os.path.join('docs', 'data', 'analysis', 'nfl_data.csv')
OUTPUT_DIR = 'docs/data/analysis'
ANALYSIS_SEASON = 2024
# Baselines for a 10-team league (e.g., the 11th QB is replacement level)
REPLACEMENT_LEVELS = {'QB': 11, 'RB': 21, 'WR': 21, 'TE': 11}

def calculate_fantasy_points(df):
    """
    Calculates fantasy points based on your league's specific custom scoring rules.
    """
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
    print("--- Starting VORP Calculator ---")
    
    try:
        df = pd.read_csv(DATA_FILE, low_memory=False)
    except FileNotFoundError:
        print(f"❌ ERROR: Data file not found.")
        return

    df = calculate_fantasy_points(df)
    
    # Calculate average points per game (PPG)
    active_players = df[df['fantasy_points_custom'] > 0]
    ppg = active_players.groupby(['player_id', 'player_display_name', 'position'])['fantasy_points_custom'].mean().reset_index()
    ppg = ppg.rename(columns={'fantasy_points_custom': 'ppg'})
    
    # We only want to analyze players who were active in the most recent season
    last_season_df = df[df['season'] == ANALYSIS_SEASON]
    relevant_players = ppg[ppg['player_id'].isin(last_season_df['player_id'])].copy()

    vorp_data = []
    print("Calculating VORP for each position...")

    for pos, rank_cutoff in REPLACEMENT_LEVELS.items():
        pos_df = relevant_players[relevant_players['position'] == pos].sort_values(by='ppg', ascending=False).reset_index()
        
        if len(pos_df) > rank_cutoff:
            replacement_value = pos_df.loc[rank_cutoff, 'ppg']
        else:
            replacement_value = 0 # Not enough players to establish a baseline
            
        print(f"Replacement level value for {pos} (player at rank {rank_cutoff}) is {replacement_value:.2f} PPG.")
        
        pos_df['vorp'] = pos_df['ppg'] - replacement_value
        vorp_data.append(pos_df)

    # Combine all positions back into a single dataframe
    final_df = pd.concat(vorp_data).sort_values(by='vorp', ascending=False)
    
    # Save the report to a JSON file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'vorp_analysis.json')
    
    report = {
        'season': ANALYSIS_SEASON,
        'players': final_df[['player_display_name', 'position', 'ppg', 'vorp']].round(2).to_dict('records')
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✅ VORP analysis report saved to {output_path}")

if __name__ == '__main__':
    main()
