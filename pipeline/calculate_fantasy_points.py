# pipeline/calculate_fantasy_points.py
import pandas as pd
import os
import sys

# This is our custom scoring function based on your league rules.
def scoring_function(row):
    points = 0.0
    points += row.get('passing_yards', 0) * 0.05
    points += row.get('passing_tds', 0) * 4
    points += row.get('interceptions', 0) * -2
    points += row.get('passing_2pt_conversions', 0) * 2
    if row.get('passing_yards', 0) >= 400: points += 1
    
    points += row.get('rushing_yards', 0) * 0.1
    points += row.get('rushing_tds', 0) * 6
    points += row.get('rushing_first_downs', 0) * 1
    points += row.get('rushing_2pt_conversions', 0) * 2
    if 100 <= row.get('rushing_yards', 0) < 200: points += 1

    points += row.get('receptions', 0) * 1.0 # Full PPR
    points += row.get('receiving_yards', 0) * 0.1
    points += row.get('receiving_tds', 0) * 6
    points += row.get('receiving_first_downs', 0) * 0.5
    points += row.get('receiving_2pt_conversions', 0) * 2
    if row.get('receiving_yards', 0) >= 200: points += 1

    points += row.get('fumbles_lost', 0) * -2
    points += row.get('special_teams_tds', 0) * 6
    
    return round(points, 2)

def process_data():
    """
    Loads raw weekly stats, calculates fantasy points, and saves a new processed
    CSV file containing both real and fantasy stats.
    """
    print("\n--- Phase 1, Step 2: Starting Fantasy Point Calculation ---")

    # --- 1. Define File Paths ---
    raw_stats_path = os.path.join('docs', 'data', 'raw', 'weekly_stats_raw.csv')
    processed_output_dir = os.path.join('docs', 'data', 'processed')
    os.makedirs(processed_output_dir, exist_ok=True)
    processed_output_path = os.path.join(processed_output_dir, 'weekly_data_processed.csv')

    # --- 2. Load Raw Data ---
    try:
        df = pd.read_csv(raw_stats_path)
        print(f"Successfully loaded raw data from: {raw_stats_path}")
    except FileNotFoundError:
        print(f"❌ CRITICAL ERROR: Raw data file not found at '{raw_stats_path}'.")
        print("Cannot proceed. Make sure 'get_raw_data.py' ran successfully first.")
        sys.exit(1)

    # --- 3. Calculate Fantasy Points ---
    print("Calculating fantasy points for each player-game...")
    df['fantasy_points'] = df.apply(scoring_function, axis=1)
    print("✅ Fantasy points calculated.")

    # --- 4. Select and Organize Columns ---
    columns_to_keep = [
        'player_id', 'player_display_name', 'position', 'recent_team', 'season', 'week',
        'passing_yards', 'passing_tds', 'interceptions', 'rushing_yards', 'rushing_tds',
        'receptions', 'receiving_yards', 'receiving_tds', 'fantasy_points'
    ]
    df_processed = df[[col for col in columns_to_keep if col in df.columns]].copy()
    
    # --- 5. Save Processed Data ---
    df_processed.to_csv(processed_output_path, index=False)
    print(f"✅ Successfully saved processed data to: {processed_output_path}")
    print("--- Fantasy Point Calculation Finished ---")

if __name__ == '__main__':
    process_data()
