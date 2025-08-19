import pandas as pd
import os
import numpy as np

# --- Configuration ---
DATA_FILE = os.path.join('data', 'analysis', 'nfl_data_with_weather.csv')
ANALYSIS_SEASON = 2024 # The most recent full season in our dataset
POSITIONS_TO_TIER = ['QB', 'RB', 'WR', 'TE']

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

def generate_tiers(player_data, position, num_tiers=6):
    """
    Uses a simple clustering method to separate players into tiers.
    """
    pos_df = player_data[player_data['position'] == position].copy()
    if pos_df.empty:
        return
        
    # Simple tiering based on standard deviation of PPG
    ppg_std = pos_df['ppg'].std()
    top_ppg = pos_df['ppg'].max()
    
    tier_thresholds = [top_ppg - (i * ppg_std * 0.75) for i in range(1, num_tiers + 1)]
    
    def assign_tier(ppg):
        for i, threshold in enumerate(tier_thresholds):
            if ppg >= threshold:
                return i + 1
        return num_tiers
    
    pos_df['tier'] = pos_df['ppg'].apply(assign_tier)
    
    print("-" * 50)
    print(f"DRAFT TIERS FOR: {position}")
    print("-" * 50)
    for tier_num in range(1, num_tiers + 1):
        tier_players = pos_df[pos_df['tier'] == tier_num]
        if not tier_players.empty:
            player_names = [f"{row['player_display_name']} ({row['ppg']:.1f})" for index, row in tier_players.iterrows()]
            print(f"Tier {tier_num}: {', '.join(player_names)}")
    print("\n")


def main():
    print("--- Starting Draft Tier Generator ---")
    
    try:
        df = pd.read_csv(DATA_FILE, low_memory=False)
    except FileNotFoundError:
        print(f"❌ ERROR: Data file not found. Please run the 'Fetch NFL Data' workflow first.")
        return

    df = calculate_fantasy_points(df)
    
    # Calculate average points per game (PPG)
    # We only want to average over games where the player actually played a significant amount
    active_players = df[df['fantasy_points_custom'] > 0]
    ppg = active_players.groupby(['player_id', 'player_display_name', 'position'])['fantasy_points_custom'].mean().reset_index()
    ppg = ppg.rename(columns={'fantasy_points_custom': 'ppg'})
    
    # Get last season's data for tiering
    last_season_df = df[df['season'] == ANALYSIS_SEASON]
    # We only care about players who played last season
    relevant_players = ppg[ppg['player_id'].isin(last_season_df['player_id'])]

    print(f"\nGenerating draft tiers based on PPG from the {ANALYSIS_SEASON} season...\n")
    
    for pos in POSITIONS_TO_TIER:
        generate_tiers(relevant_players, pos)


if __name__ == '__main__':
    main()
