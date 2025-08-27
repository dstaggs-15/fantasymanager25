# analysis/matchup_analyzer.py
import pandas as pd
import json
import os
import sys

def analyze_matchups():
    """
    Analyzes historical data to determine how many fantasy points each NFL team's
    defense allows to each position. Ranks defenses from easiest (most points allowed)
    to hardest (fewest points allowed).
    """
    print("\n--- Starting Matchup Analysis ---")

    # --- 1. Define File Paths ---
    processed_data_path = os.path.join('docs', 'data', 'processed', 'weekly_data_processed.csv')
    schedule_path = os.path.join('docs', 'data', 'raw', 'schedule_raw.csv')
    reports_dir = os.path.join('docs', 'data', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    output_path = os.path.join(reports_dir, 'matchup_report.json')

    # --- 2. Load Data ---
    try:
        df_stats = pd.read_csv(processed_data_path)
        df_schedule = pd.read_csv(schedule_path)
        print("Successfully loaded processed stats and schedule data.")
    except FileNotFoundError as e:
        print(f"❌ CRITICAL ERROR: Could not find a required data file. {e}")
        sys.exit(1)

    # --- 3. Determine Opponent for Each Player Game ---
    # Select only necessary columns from the schedule
    df_schedule_slim = df_schedule[['season', 'week', 'away_team', 'home_team']].copy()
    
    # Create a mapping of each team to its opponent for every game
    home_opponents = df_schedule_slim.rename(columns={'home_team': 'team', 'away_team': 'opponent'})
    away_opponents = df_schedule_slim.rename(columns={'away_team': 'team', 'home_team': 'opponent'})
    opponent_map = pd.concat([home_opponents, away_opponents])

    # Merge this opponent map into our main stats dataframe
    df_merged = pd.merge(df_stats, opponent_map, on=['season', 'week'], left_on='recent_team', right_on='team', how='left')

    # --- 4. Calculate Fantasy Points Allowed by each Defense ---
    # Group by the opponent and position to find the average points allowed
    points_allowed = df_merged.groupby(['opponent', 'position'])['fantasy_points'].mean().reset_index()
    points_allowed.rename(columns={'opponent': 'team', 'fantasy_points': 'points_allowed'}, inplace=True)
    
    print("Calculating average fantasy points allowed by each defense...")

    # --- 5. Rank the Defenses ---
    # A higher rank means an easier matchup (more points allowed)
    points_allowed['rank'] = points_allowed.groupby('position')['points_allowed'].rank(ascending=False, method='first').astype(int)
    points_allowed.sort_values(by=['position', 'rank'], inplace=True)

    # --- 6. Format for JSON and Save ---
    report = {}
    for pos in points_allowed['position'].unique():
        pos_df = points_allowed[points_allowed['position'] == pos]
        report[pos] = pos_df[['team', 'points_allowed', 'rank']].to_dict(orient='records')

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=4)

    print(f"✅ Successfully created matchup analysis report at: {output_path}")
    print("--- Matchup Analysis Finished ---")

if __name__ == '__main__':
    analyze_matchups()
