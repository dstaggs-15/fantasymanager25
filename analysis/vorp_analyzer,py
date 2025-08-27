# analysis/vorp_analyzer.py
import pandas as pd
import json
import os
import sys

def analyze_vorp_and_consistency():
    """
    Analyzes the processed weekly data to calculate season-long PPG and consistency
    metrics for each player. This data will power the VORP tool on the website.
    """
    print("\n--- Phase 2, Step 1: Starting VORP & Consistency Analysis ---")

    # --- 1. Define File Paths ---
    processed_data_path = os.path.join('docs', 'data', 'processed', 'weekly_data_processed.csv')
    reports_dir = os.path.join('docs', 'data', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    output_path = os.path.join(reports_dir, 'vorp_report.json')

    # --- 2. Load Processed Data ---
    try:
        df = pd.read_csv(processed_data_path)
        print(f"Successfully loaded processed data from: {processed_data_path}")
    except FileNotFoundError:
        print(f"❌ CRITICAL ERROR: Processed data file not found at '{processed_data_path}'.")
        sys.exit(1)

    # --- 3. Determine Most Recent Completed Season ---
    latest_season = df['season'].max()
    if df[df['season'] == latest_season]['week'].max() < 4:
        latest_season = latest_season - 1
    
    print(f"Analyzing player performance for the {latest_season} season.")
    df_season = df[df['season'] == latest_season].copy()

    # --- 4. Calculate PPG and Consistency Metrics ---
    player_agg = df_season.groupby('player_id').agg(
        player_display_name=('player_display_name', 'first'),
        position=('position', 'first'),
        recent_team=('recent_team', 'first'),
        total_points=('fantasy_points', 'sum'),
        games_played=('fantasy_points', 'count'),
        std_dev=('fantasy_points', 'std'),
        avg_points=('fantasy_points', 'mean')
    ).reset_index()

    player_agg['std_dev'] = player_agg['std_dev'].fillna(0)
    
    min_games = 3
    player_agg = player_agg[player_agg['games_played'] >= min_games]

    # --- 6. Format for JSON Output ---
    final_data = player_agg[['player_display_name', 'position', 'recent_team', 'games_played', 'avg_points', 'std_dev', 'total_points']].copy()
    final_data.rename(columns={'avg_points': 'ppg', 'std_dev': 'consistency'}, inplace=True)
    
    final_data['ppg'] = final_data['ppg'].round(2)
    final_data['consistency'] = final_data['consistency'].round(2)

    final_data.sort_values(by='ppg', ascending=False, inplace=True)
    
    report_json = final_data.to_dict(orient='records')

    # --- 7. Save the Report ---
    with open(output_path, 'w') as f:
        json.dump(report_json, f, indent=4)

    print(f"✅ Successfully created VORP analysis report at: {output_path}")
    print("--- VORP & Consistency Analysis Finished ---")

if __name__ == '__main__':
    analyze_vorp_and_consistency()
