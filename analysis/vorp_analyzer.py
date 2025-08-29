import pandas as pd
import numpy as np
import json
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, 'docs', 'data', 'processed', 'weekly_data_processed.csv')
REPORTS_DIR = os.path.join(BASE_DIR, 'data', 'reports')
CURRENT_SEASON = 2024 # Assuming this is the season being analyzed

def analyze_vorp_and_consistency():
    """
    Loads processed weekly data to calculate season-long PPG, Standard Deviation,
    and VORP for each player.
    """
    print("--- Phase 2, Step 1: Starting VORP & Consistency Analysis ---")

    try:
        df = pd.read_csv(PROCESSED_DATA_PATH)
        print(f"Successfully loaded processed data from: {PROCESSED_DATA_PATH}")
    except FileNotFoundError:
        print(f"❌ Error: Processed data file not found at {PROCESSED_DATA_PATH}. Aborting.")
        return

    # Filter for the current season
    df_season = df[df['season'] == CURRENT_SEASON].copy()
    print(f"Analyzing player performance for the {CURRENT_SEASON} season.")

    # Calculate PPG and Standard Deviation for players who played at least 4 games
    player_stats = df_season.groupby('player_id').agg(
        games_played=('week', 'nunique'),
        ppg=('fantasy_points', 'mean'),
        std_dev=('fantasy_points', 'std')
    ).reset_index()

    player_stats = player_stats[player_stats['games_played'] >= 4]
    player_stats['std_dev'] = player_stats['std_dev'].fillna(0) # Fill NaN for players with no variance

    # Get player metadata (name, position, team, etc.)
    player_info = df_season[['player_id', 'player_name', 'position', 'team', 'birth_date']].drop_duplicates(subset='player_id')
    
    # Merge stats with info
    final_stats = pd.merge(player_info, player_stats, on='player_id')

    # Calculate VORP (Value Over Replacement Player)
    # Define simple replacement-level PPG thresholds by position
    replacement_levels = {
        'QB': final_stats[final_stats['position'] == 'QB']['ppg'].quantile(0.6), # Approx QB13-15
        'RB': final_stats[final_stats['position'] == 'RB']['ppg'].quantile(0.7), # Approx RB25-30
        'WR': final_stats[final_stats['position'] == 'WR']['ppg'].quantile(0.7), # Approx WR30-36
        'TE': final_stats[final_stats['position'] == 'TE']['ppg'].quantile(0.6), # Approx TE12-14
    }

    def calculate_vorp(row):
        pos = row['position']
        if pos in replacement_levels:
            replacement_ppg = replacement_levels[pos]
            return (row['ppg'] - replacement_ppg) * row['games_played']
        return 0

    final_stats['vorp'] = final_stats.apply(calculate_vorp, axis=1)

    # Round numeric columns for cleaner output
    numeric_cols = ['ppg', 'std_dev', 'vorp']
    final_stats[numeric_cols] = final_stats[numeric_cols].round(2)

    # --- FIX: Save the report with the correct filename ---
    output_path = os.path.join(REPORTS_DIR, 'vorp_analyzer_report.json')
    
    report_json = final_stats.to_dict(orient='records')
    with open(output_path, 'w') as f:
        json.dump(report_json, f, indent=4)

    print(f"✅ Successfully created VORP analysis report at: {output_path}")
    print("--- VORP & Consistency Analysis Finished ---")


if __name__ == '__main__':
    analyze_vorp_and_consistency()
