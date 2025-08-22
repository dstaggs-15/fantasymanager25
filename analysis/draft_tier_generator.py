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
POSITIONS_TO_TIER = ['QB', 'RB', 'WR', 'TE']

def generate_tiers(player_data, position, num_tiers=6):
    pos_df = player_data[player_data['position'] == position].copy()
    if pos_df.empty: return {}
    ppg_std = pos_df['ppg'].std()
    top_ppg = pos_df['ppg'].max()
    tier_thresholds = [top_ppg - (i * ppg_std * 0.75) for i in range(1, num_tiers + 1)]
    def assign_tier(ppg):
        for i, threshold in enumerate(tier_thresholds):
            if ppg >= threshold: return i + 1
        return num_tiers
    pos_df['tier'] = pos_df['ppg'].apply(assign_tier)
    
    tiers = {}
    for tier_num in range(1, num_tiers + 1):
        tier_players = pos_df[pos_df['tier'] == tier_num]
        if not tier_players.empty:
            tiers[f'Tier {tier_num}'] = tier_players[['player_display_name', 'ppg']].round(2).to_dict('records')
    return tiers

def main():
    print("--- Starting Draft Tier Generator ---")
    try:
        df = pd.read_csv(DATA_FILE, low_memory=False)
    except FileNotFoundError:
        print(f"❌ ERROR: Data file not found.")
        return

    df = calculate_fantasy_points(df)
    active_players = df[df['fantasy_points_custom'] > 0]
    ppg = active_players.groupby(['player_id', 'player_display_name', 'position'])['fantasy_points_custom'].mean().reset_index()
    ppg = ppg.rename(columns={'fantasy_points_custom': 'ppg'})
    last_season_df = df[df['season'] == ANALYSIS_SEASON]
    relevant_players = ppg[ppg['player_id'].isin(last_season_df['player_id'])]
    
    report_data = {'season': ANALYSIS_SEASON, 'positions': {}}
    print(f"\nGenerating draft tiers based on PPG from the {ANALYSIS_SEASON} season...\n")
    for pos in POSITIONS_TO_TIER:
        report_data['positions'][pos] = generate_tiers(relevant_players, pos)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'draft_tiers_report.json')
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    print(f"✅ Draft tiers report saved to {output_path}")

if __name__ == '__main__':
    main()
