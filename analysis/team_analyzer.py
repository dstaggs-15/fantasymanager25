import pandas as pd
import os
import json

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
    season_df['opponent'] = np.where(season_df['recent_team'] == season_df['home_team'], season_df['away_team'], season_df['home_team'])
    
    # Calculate Fantasy Points Allowed by each defense, to each position
    fpa = season_df.groupby(['opponent', 'position'])['fantasy_points_ppr'].mean().unstack().round(2)
    fpa = fpa.rename(columns={'opponent': 'team'}).fillna(0)
    
    # Calculate total points scored by each offense
    offense_scoring = season_df.groupby('recent_team')['weekly_points'].mean().round(2).sort_values(ascending=False)
    
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
