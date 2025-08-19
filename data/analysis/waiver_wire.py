import pandas as pd
import os
import numpy as np

# --- Configuration ---
DATA_FILE = os.path.join('data', 'analysis', 'nfl_data_with_weather.csv')

def calculate_fantasy_points(df):
    """
    Calculates fantasy points based on your league's specific custom scoring rules.
    """
    print("Calculating fantasy points using your league's custom scoring rules...")
    
    # Initialize points column
    df['fantasy_points_custom'] = 0.0

    # --- Offensive Players Scoring ---
    df['fantasy_points_custom'] += df['passing_yards'] * 0.05
    df['fantasy_points_custom'] += df['passing_tds'] * 4
    df['fantasy_points_custom'] += df['interceptions'] * -2
    df['fantasy_points_custom'] += df['passing_2pt_conversions'] * 2
    
    df['fantasy_points_custom'] += df['rushing_yards'] * 0.1
    df['fantasy_points_custom'] += df['rushing_tds'] * 6
    df['fantasy_points_custom'] += df['rushing_2pt_conversions'] * 2
    df['fantasy_points_custom'] += df['rushing_first_downs'] * 1
    
    df['fantasy_points_custom'] += df['receptions'] * 1
    df['fantasy_points_custom'] += df['receiving_yards'] * 0.1
    df['fantasy_points_custom'] += df['receiving_tds'] * 6
    df['fantasy_points_custom'] += df['receiving_2pt_conversions'] * 2
    df['fantasy_points_custom'] += df['receiving_first_downs'] * 0.5
    
    df['fantasy_points_custom'] += df['fumbles_lost'] * -2
    
    # Offensive player return TDs
    df['fantasy_points_custom'] += (df['special_teams_tds']) * 6

    # --- Bonuses ---
    df.loc[df['passing_yards'] >= 400, 'fantasy_points_custom'] += 1
    df.loc[df['rushing_yards'] >= 100, 'fantasy_points_custom'] += 1
    df.loc[df['receiving_yards'] >= 200, 'fantasy_points_custom'] += 1
    
    # --- Kicker Scoring ---
    df['fantasy_points_custom'] += df['pat_made'] * 1
    df['fantasy_points_custom'] += df['fg_made_0_39'] * 3
    df['fantasy_points_custom'] += df['fg_made_40_49'] * 4
    df['fantasy_points_custom'] += df['fg_made_50_59'] * 5
    df['fantasy_points_custom'] += df['fg_made_60_'] * 6
    df['fantasy_points_custom'] += (df['fg_missed']) * -1

    # --- D/ST Scoring ---
    df['fantasy_points_custom'] += df['sacks'] * 1
    df['fantasy_points_custom'] += df['interceptions'] * 2 # Note: 'interceptions' col is used for both offense and defense
    df['fantasy_points_custom'] += df['fumbles_recovered'] * 2
    df['fantasy_points_custom'] += df['safeties'] * 2
    df['fantasy_points_custom'] += df['defensive_tds'] * 6
    df['fantasy_points_custom'] += df['blocked_kicks'] * 2
    
    # Points Allowed (for D/ST position only)
    conditions_pa = [
        (df['points_allowed'] == 0),
        (df['points_allowed'] >= 1) & (df['points_allowed'] <= 6),
        (df['points_allowed'] >= 7) & (df['points_allowed'] <= 13),
        (df['points_allowed'] >= 14) & (df['points_allowed'] <= 17),
        (df['points_allowed'] >= 28) & (df['points_allowed'] <= 34),
        (df['points_allowed'] >= 35) & (df['points_allowed'] <= 45),
        (df['points_allowed'] >= 46)
    ]
    points_pa = [5, 4, 3, 1, -1, -3, -5]
    df['pa_points'] = np.select(conditions_pa, points_pa, default=0)
    df.loc[df['position'] == 'DEF', 'fantasy_points_custom'] += df['pa_points']
    
    return df

def main():
    print("--- Starting Waiver Wire Assistant ---")
    
    try:
        print(f"Loading data from {DATA_FILE}...")
        df = pd.read_csv(DATA_FILE)
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
        print(top_performers[display_cols].round(2).to_string(index=False))
        print("\n")

if __name__ == '__main__':
    main()
