import pandas as pd
import os
import numpy as np
import json

# --- Configuration ---
DATA_FILE = os.path.join('docs', 'data', 'analysis', 'nfl_data.csv')
OUTPUT_DIR = 'docs/data/analysis'
ANALYSIS_SEASONS = [2024, 2023, 2022] # Use a multi-year sample for consistency
MIN_GAMES_PLAYED = 8 # Minimum games a player must have played in a season to be included

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
    print("--- Starting Consistency Analyzer ---")
    
    try:
        df = pd.read_csv(DATA_FILE, low_memory=False)
    except FileNotFoundError:
        print(f"❌ ERROR: Data file not found.")
        return

    df = calculate_fantasy_points(df)

    # Filter for the seasons we want to analyze
    analysis_df = df[df['season'].isin(ANALYSIS_SEASONS)].copy()
    
    # Group by player to perform calculations
    player_groups = analysis_df.groupby(['player_id', 'player_display_name', 'position'])

    # Aggregate various stats for each player
    player_stats = player_groups.agg(
        games_played=('week', 'count'),
        mean_ppg=('fantasy_points_custom', 'mean'),
        std_dev_ppg=('fantasy_points_custom', 'std'),
        ceiling_ppg=('fantasy_points_custom', lambda x: x.quantile(0.9)), # 90th percentile score
        floor_ppg=('fantasy_points_custom', lambda x: x.quantile(0.1))   # 10th percentile score
    ).reset_index()

    # Calculate consistency rating: % of games above a certain threshold
    # Define thresholds by position
    thresholds = {'QB': 15, 'RB': 10, 'WR': 10, 'TE': 8}
    
    def get_consistency(group):
        pos = group['position'].iloc[0]
        threshold = thresholds.get(pos, 0)
        if threshold == 0:
            return 0
        good_games = (group['fantasy_points_custom'] >= threshold).sum()
        total_games = len(group)
        return (good_games / total_games) * 100 if total_games > 0 else 0

    consistency = player_groups.apply(get_consistency).reset_index(name='consistency_pct')
    
    # Merge all calculated stats together
    final_df = pd.merge(player_stats, consistency, on=['player_id', 'player_display_name', 'position'])
    
    # Filter for players who have played a reasonable number of games
    final_df = final_df[final_df['games_played'] >= MIN_GAMES_PLAYED]
    
    # Sort by consistency and then by mean PPG
    final_df = final_df.sort_values(by=['position', 'consistency_pct', 'mean_ppg'], ascending=[True, False, False])

    # Save the report to a JSON file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'consistency_report.json')
    
    report = {
        'analysis_seasons': ANALYSIS_SEASONS,
        'players': final_df.round(2).to_dict('records')
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✅ Consistency analysis report saved to {output_path}")

if __name__ == '__main__':
    main()
