import pandas as pd
import json
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, 'docs', 'data', 'processed', 'weekly_data_processed.csv')
RAW_DATA_DIR = os.path.join(BASE_DIR, 'docs', 'data', 'raw')
REPORTS_DIR = os.path.join(BASE_DIR, 'docs', 'data', 'reports')

def analyze_matchups():
    """
    Analyzes points allowed by each defense to each offensive position and saves a flat report.
    """
    print("--- Starting Matchup Analysis ---")
    try:
        df_weekly = pd.read_csv(PROCESSED_DATA_PATH)
        df_schedule = pd.read_csv(os.path.join(RAW_DATA_DIR, 'schedule_raw.csv'))
        print("Successfully loaded processed stats and schedule data.")
    except FileNotFoundError as e:
        print(f"❌ Error loading data: {e}. Aborting.")
        return

    # Determine opponent for each player in each game
    opponent_map = {}
    for _, row in df_schedule.iterrows():
        game_key_home = f"{row['season']}_{row['week']}_{row['home_team']}"
        game_key_away = f"{row['season']}_{row['week']}_{row['away_team']}"
        opponent_map[game_key_home] = row['away_team']
        opponent_map[game_key_away] = row['home_team']
    
    df_weekly['game_key'] = df_weekly['season'].astype(str) + '_' + df_weekly['week'].astype(str) + '_' + df_weekly['recent_team']
    df_weekly['opponent'] = df_weekly['game_key'].map(opponent_map)
    
    # Calculate average points allowed by each defense (opponent) to each position
    df_matchups = df_weekly.groupby(['opponent', 'position'])['fantasy_points'].mean().reset_index()
    
    # Rank defenses: A higher rank (closer to 1) means they allow MORE points (an easier matchup)
    df_matchups['matchup_rank'] = df_matchups.groupby('position')['fantasy_points'].rank(ascending=False, method='dense')
    
    # Rename 'opponent' to 'team' for consistency
    df_matchups.rename(columns={'opponent': 'team'}, inplace=True)

    # Prepare and save the final, simple, flat report
    report_df = df_matchups[['team', 'position', 'matchup_rank']].dropna()
    
    output_path = os.path.join(REPORTS_DIR, 'matchup_report.json')
    report_df.to_json(output_path, orient='records', indent=4)

    print(f"✅ Successfully created matchup analysis report at: {output_path}")
    print("--- Matchup Analysis Finished ---")

if __name__ == '__main__':
    analyze_matchups()
