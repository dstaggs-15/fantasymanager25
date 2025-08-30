import pandas as pd
import json
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, 'docs', 'data', 'processed', 'weekly_data_processed.csv')
REPORTS_DIR = os.path.join(BASE_DIR, 'docs', 'data', 'reports')
CURRENT_SEASON = 2024

def analyze_consistency():
    """
    Analyzes player consistency and saves a complete report with player metadata.
    """
    print("--- Starting Consistency Analysis ---")
    try:
        df = pd.read_csv(PROCESSED_DATA_PATH)
        print(f"Successfully loaded processed data from: {PROCESSED_DATA_PATH}")
    except FileNotFoundError:
        print(f"❌ Error: Processed data file not found at {PROCESSED_DATA_PATH}. Aborting.")
        return

    df_season = df[df['season'] == CURRENT_SEASON].copy()
    print(f"Analyzing player consistency for the {CURRENT_SEASON} season.")

    # --- FIX: Create a separate DataFrame for player info ---
    player_info = df_season[['player_id', 'player_name', 'position', 'recent_team']].drop_duplicates(subset=['player_id'])
    player_info.rename(columns={'recent_team': 'team'}, inplace=True)

    # Calculate consistency stats
    player_stats = df_season.groupby('player_id')['fantasy_points'].agg([
        'mean',      # Average points (PPG)
        'std',       # Standard Deviation (volatility)
        lambda x: x.quantile(0.8), # Ceiling (80th percentile score)
        lambda x: x.quantile(0.2), # Floor (20th percentile score)
        lambda x: (x > x.mean() + x.std()).mean(), # "Boom" or Good %
        lambda x: (x < x.mean() - x.std()).mean()  # "Bust" or Bust %
    ]).reset_index()

    # Rename the aggregated columns for clarity
    player_stats.columns = [
        'player_id', 'ppg', 'std_dev', 'ceiling', 
        'floor', 'good_pct', 'bust_pct'
    ]

    # --- FIX: Merge the calculated stats back with the player info ---
    final_report = pd.merge(player_info, player_stats, on='player_id')
    
    # Fill any potential NaN values for players with low game counts
    final_report.fillna(0, inplace=True)

    output_path = os.path.join(REPORTS_DIR, 'consistency_report.json')
    final_report.to_json(output_path, orient='records', indent=4)

    print(f"✅ Successfully created consistency analysis report at: {output_path}")
    print("--- Consistency Analysis Finished ---")

if __name__ == '__main__':
    analyze_consistency()
