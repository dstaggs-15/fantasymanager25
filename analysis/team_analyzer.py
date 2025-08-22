import pandas as pd
import os
import json
import numpy as np
import sys # Add sys import

# THE FIX: Add the project's root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from pipeline.utils import calculate_fantasy_points # This will now work

# --- Configuration ---
DATA_FILE = os.path.join('docs', 'data', 'analysis', 'nfl_data.csv')
OUTPUT_DIR = 'docs/data/analysis'
ANALYSIS_SEASON = 2024

def main():
    print("--- Starting Team Analyzer ---")
    try:
        df = pd.read_csv(DATA_FILE, low_memory=False)
    except FileNotFoundError:
        print(f"❌ ERROR: Data file not found.")
        return

    season_df = df[df['season'] == ANALYSIS_SEASON].copy()
    season_df = calculate_fantasy_points(season_df)
    season_df['opponent'] = np.where(season_df['recent_team'] == season_df['home_team'], season_df['away_team'], season_df['home_team'])
    
    # Calculate Fantasy Points Allowed by each defense, to each position
    fpa = season_df.groupby(['opponent', 'position'])['fantasy_points_custom'].mean().unstack().round(2)
    fpa = fpa.rename(columns={'opponent': 'team'}).fillna(0)
    
    # Calculate total points scored by each offense
    unique_games = season_df[['game_id', 'home_team', 'away_team', 'home_score', 'away_score']].drop_duplicates()
    home_scores = unique_games[['home_team', 'home_score']].rename(columns={'home_team': 'team', 'home_score': 'points'})
    away_scores = unique_games[['away_team', 'away_score']].rename(columns={'away_team': 'team', 'away_score': 'points'})
    all_scores = pd.concat([home_scores, away_scores])
    offense_scoring = all_scores.groupby('team')['points'].mean().round(2).sort_values(ascending=False)
    
    report = {
        'fantasy_points_allowed': fpa.to_dict('index'),
        'offensive_scoring_avg': offense_scoring.to_dict()
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'team_rankings.json')
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✅ Team analysis report saved to {output_path}")

if __name__ == '__main__':
    main()
