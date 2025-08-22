import pandas as pd
import os
import json
import sys # Add sys import

# Add the project's root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from pipeline.utils import calculate_fantasy_points

DATA_FILE = os.path.join('docs', 'data', 'analysis', 'nfl_data.csv')
OUTPUT_DIR = 'docs/data/analysis'
ANALYSIS_SEASON = 2024
REPLACEMENT_LEVELS = {'QB': 11, 'RB': 21, 'WR': 21, 'TE': 11}

def main():
    print("--- Starting VORP and Stats Calculator ---")
    try:
        df = pd.read_csv(DATA_FILE, low_memory=False)
    except FileNotFoundError:
        print(f"❌ ERROR: Data file not found.")
        return

    df = calculate_fantasy_points(df)
    
    stats_to_average = [
        'fantasy_points_custom', 'passing_yards', 'passing_tds', 'interceptions',
        'rushing_yards', 'rushing_tds', 'receptions', 'receiving_yards', 'receiving_tds'
    ]
    player_season_stats = df.groupby(['player_id', 'player_display_name', 'position', 'season']).agg(
        games_played=('week', 'nunique'),
        **{stat: (stat, 'sum') for stat in stats_to_average}
    ).reset_index()

    for stat in stats_to_average:
        player_season_stats[f'{stat}_pg'] = player_season_stats[stat] / player_season_stats['games_played']
    
    last_season_stats = player_season_stats[player_season_stats['season'] == ANALYSIS_SEASON].copy()
    last_season_stats = last_season_stats.rename(columns={'fantasy_points_custom_pg': 'ppg'})

    vorp_data = []
    print("Calculating VORP for each position...")
    for pos, rank_cutoff in REPLACEMENT_LEVELS.items():
        pos_df = last_season_stats[last_season_stats['position'] == pos].sort_values(by='ppg', ascending=False).reset_index(drop=True)
        if len(pos_df) > rank_cutoff:
            replacement_value = pos_df.loc[rank_cutoff - 1, 'ppg']
        else:
            replacement_value = 0
        pos_df['vorp'] = pos_df['ppg'] - replacement_value
        vorp_data.append(pos_df)

    final_df = pd.concat(vorp_data).sort_values(by='vorp', ascending=False)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'vorp_analysis.json')
    report = {'season': ANALYSIS_SEASON, 'players': final_df.round(2).to_dict('records')}
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✅ VORP analysis report with detailed stats saved to {output_path}")

if __name__ == '__main__':
    main()
