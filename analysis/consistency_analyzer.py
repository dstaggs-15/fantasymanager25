import pandas as pd
import os
import json
import sys # Add sys import
# ... (imports)

# --- Configuration ---
# THE FIX: Ensure all scripts read from and write to the 'docs' folder
DATA_FILE = os.path.join('docs', 'data', 'analysis', 'nfl_data.csv')
OUTPUT_DIR = os.path.join('docs', 'data', 'analysis')

# ... (the rest of each script is unchanged)
# Add the project's root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from pipeline.utils import calculate_fantasy_points

DATA_FILE = os.path.join('docs', 'data', 'analysis', 'nfl_data.csv')
OUTPUT_DIR = 'docs/data/analysis'
ANALYSIS_SEASONS = [2024, 2023, 2022]
MIN_GAMES_PLAYED = 8

def main():
    print("--- Starting Consistency Analyzer ---")
    try:
        df = pd.read_csv(DATA_FILE, low_memory=False)
    except FileNotFoundError:
        print(f"❌ ERROR: Data file not found.")
        return

    df = calculate_fantasy_points(df)
    analysis_df = df[df['season'].isin(ANALYSIS_SEASONS)].copy()
    player_groups = analysis_df.groupby(['player_id', 'player_display_name', 'position'])

    player_stats = player_groups.agg(
        games_played=('week', 'count'),
        mean_ppg=('fantasy_points_custom', 'mean'),
        std_dev_ppg=('fantasy_points_custom', 'std'),
        ceiling_ppg=('fantasy_points_custom', lambda x: x.quantile(0.9)),
        floor_ppg=('fantasy_points_custom', lambda x: x.quantile(0.1))
    ).reset_index()

    thresholds = {'QB': 15, 'RB': 10, 'WR': 10, 'TE': 8}
    def get_consistency(group):
        pos = group['position'].iloc[0]
        threshold = thresholds.get(pos, 0)
        if threshold == 0: return 0
        good_games = (group['fantasy_points_custom'] >= threshold).sum()
        total_games = len(group)
        return (good_games / total_games) * 100 if total_games > 0 else 0

    consistency = player_groups.apply(get_consistency).reset_index(name='consistency_pct')
    final_df = pd.merge(player_stats, consistency, on=['player_id', 'player_display_name', 'position'])
    final_df = final_df[final_df['games_played'] >= MIN_GAMES_PLAYED]
    final_df = final_df.sort_values(by=['position', 'consistency_pct', 'mean_ppg'], ascending=[True, False, False])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'consistency_report.json')
    report = {'analysis_seasons': ANALYSIS_SEASONS, 'players': final_df.round(2).to_dict('records')}
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✅ Consistency analysis report saved to {output_path}")

if __name__ == '__main__':
    main()
