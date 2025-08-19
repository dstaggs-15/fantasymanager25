import pandas as pd
import os

# --- Configuration ---
DATA_FILE = os.path.join('data', 'analysis', 'nfl_data_with_weather.csv')

def calculate_fantasy_points(df):
    """
    Calculates fantasy points based on standard PPR scoring.
    """
    print("Calculating fantasy points...")
    # Standard PPR scoring rules
    df['fantasy_points_ppr'] = (
        df['passing_yards'] * 0.04 +
        df['passing_tds'] * 4 +
        df['rushing_yards'] * 0.1 +
        df['rushing_tds'] * 6 +
        df['receiving_yards'] * 0.1 +
        df['receiving_tds'] * 6 +
        df['receptions'] * 1 +
        df['interceptions'] * -2 +
        df['fumbles_lost'] * -2
    )
    return df

def main():
    print("--- Starting Waiver Wire Assistant ---")
    
    # 1. Load the dataset
    try:
        print(f"Loading data from {DATA_FILE}...")
        df = pd.read_csv(DATA_FILE)
        print("Data loaded successfully.")
    except FileNotFoundError:
        print(f"❌ ERROR: Data file not found. Please run the get_nfl_data.py script first.")
        return

    # 2. Calculate fantasy points for all players
    df = calculate_fantasy_points(df)

    # 3. Find the most recent week in the dataset
    latest_season = df['season'].max()
    latest_week = df[df['season'] == latest_season]['week'].max()
    print(f"\nAnalyzing top performers for Season: {latest_season}, Week: {latest_week}\n")

    # 4. Filter for the latest week
    latest_week_df = df[(df['season'] == latest_season) & (df['week'] == latest_week)]

    # 5. Find and print the top performers for each position
    positions = {'QB': 10, 'RB': 15, 'WR': 15, 'TE': 10}
    for pos, num_players in positions.items():
        print("-" * 30)
        print(f"Top {num_players} {pos}s for Week {latest_week}")
        print("-" * 30)
        
        top_performers = (
            latest_week_df[latest_week_df['position'] == pos]
            .sort_values(by='fantasy_points_ppr', ascending=False)
            .head(num_players)
        )
        
        # Select and display key columns
        display_cols = ['player_display_name', 'recent_team', 'fantasy_points_ppr']
        print(top_performers[display_cols].round(2).to_string(index=False))
        print("\n")

if __name__ == '__main__':
    main()
