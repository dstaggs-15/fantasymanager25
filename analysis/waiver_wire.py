import pandas as pd
import os
import numpy as np

# --- Configuration ---
DATA_FILE = os.path.join('data', 'analysis', 'nfl_data_with_weather.csv')

def calculate_fantasy_points(df):
    """
    Calculates fantasy points based on your league's specific custom scoring rules.
    This version is robust and checks for the existence of each column before using it.
    """
    print("Calculating fantasy points using your league's custom scoring rules...")
    
    df['fantasy_points_custom'] = 0.0

    # Define all possible scoring columns and their point values
    scoring_rules = {
        'passing_yards': 0.05, 'passing_tds': 4, 'interceptions': -2,
        'passing_2pt_conversions': 2, 'rushing_yards': 0.1, 'rushing_tds': 6,
        'rushing_2pt_conversions': 2, 'rushing_first_downs': 1, 'receptions': 1,
        'receiving_yards': 0.1, 'receiving_tds': 6, 'receiving_2pt_conversions': 2,
        'receiving_first_downs': 0.5, 'fumbles_lost': -2, 'special_teams_tds': 6,
        'pat_made': 1, 'fg_made_0_39': 3, 'fg_made_40_49': 4, 'fg_made_50_59': 5,
        'fg_made_60_': 6, 'fg_missed': -1
    }

    # Apply scoring rules dynamically
    for column, points in scoring_rules.items():
        if column in df.columns:
            df['fantasy_points_custom'] += df[column].fillna(0) * points
        else:
            print(f"Warning: Column '{column}' not found in data. Skipping.")

    # --- Bonuses ---
    if 'passing_yards' in df.columns:
        df.loc[df['passing_yards'] >= 400, 'fantasy_points_custom'] += 1
    if 'rushing_yards' in df.columns:
        df.loc[df['rushing_yards'] >= 100, 'fantasy_points_custom'] += 1
    if 'receiving_yards' in df.columns:
        df.loc[df['receiving_yards'] >= 200, 'fantasy_points_custom'] += 1
    
    # --- D/ST Scoring ---
    dst_rules = {
        'sacks': 1, 'interceptions': 2, 'fumbles_recovered': 2,
        'safeties': 2, 'defensive_tds': 6, 'blocked_kicks': 2
    }
    for column, points in dst_rules.items():
        if column in df.columns:
            df.loc[df['position'] == 'DEF', 'fantasy_points_custom'] += df[column].fillna(0) * points

    # THE FIX: Rewritten D/ST Points Allowed logic to be correct and avoid syntax errors.
    if 'points_allowed' in df.columns:
        conditions = [
            (df['points_allowed'] == 0),
            (df['points_allowed'] >= 1) & (df['points_allowed'] <= 6),
            (df['points_allowed'] >= 7) & (df['points_allowed'] <= 13),
            (df['points_allowed'] >= 14) & (df['points_allowed'] <= 17),
            (df['points_allowed'] >= 18) & (df['points_allowed'] <= 27),
            (df['points_allowed'] >= 28) & (df['points_allowed'] <= 34),
            (df['points_allowed'] >= 35) & (df['points_allowed'] <= 45),
            (df['points_allowed'] >= 46)
        ]
        points = [5, 4, 3, 1, 0, -1, -3, -5]
        
        # Use np.select to apply points based on the conditions
        pa_points = np.select(conditions, points, default=0)
        
        # Apply these points only to rows where the position is DEF
        df.loc[df['position'] == 'DEF', 'fantasy_points_custom'] += pa_points

    return df

def main():
    print("--- Starting Waiver Wire Assistant ---")
    
    try:
        print(f"Loading data from {DATA_FILE}...")
        df = pd.read_csv(DATA_FILE, low_memory=False)
        print("Data loaded successfully.")
    except FileNotFoundError:
        print(f"❌ ERROR: Data file not found. Please run the 'Fetch NFL Data' workflow first.")
        return

    df = calculate_fantasy_points(df)

    latest_season = df['season'].max()
    latest_week = df[df['season'] == latest_season]['week'].max()
    print(f"\n🔥 Analyzing Top Performers for Season: {latest_season}, Week: {latest_week} 🔥\n")

    latest_week_df = df[(df['season'] == latest_season) & (df['week'] == latest_week)]

    positions = {'QB': 10, 'RB': 15, 'WR': 15, 'TE': 10, 'K': 5, 'DEF': 5}
    for pos, num_players in positions.items():
        print("-" * 40)
        print(f"Top {num_players} {pos}s for Week {latest_week}")
        print("-" * 40)
        
        top_performers = (
            latest_week_df[latest_week_df['position'] == pos]
            .sort_values(by='fantasy_points_custom', ascending=False)
            .head(num_players)
        )
        
        display_cols = ['player_display_name', 'recent_team', 'fantasy_points_custom']
        top_performers_display = top_performers[display_cols].fillna('N/A')
        print(top_performers_display.round(2).to_string(index=False))
        print("\n")

if __name__ == '__main__':
    main()
