import pandas as pd
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'docs', 'data', 'processed')
RAW_DATA_PATH = os.path.join(BASE_DIR, 'docs', 'data', 'raw', 'weekly_stats_raw.csv')

# --- Main Logic ---
def calculate_fantasy_points():
    print("--- Starting Fantasy Point Calculation ---")
    try:
        df = pd.read_csv(RAW_DATA_PATH)
        print(f"Successfully loaded raw data from: {RAW_DATA_PATH}")
    except FileNotFoundError:
        print(f"❌ Error: Raw data file not found at {RAW_DATA_PATH}. Aborting.")
        return

    # --- FIX: Use df.get('column_name', 0) for all stats ---
    # This safely handles any missing stat columns by treating them as 0.
    df['fantasy_points'] = (
        df.get('passing_yards', 0) * 0.04 +
        df.get('passing_tds', 0) * 4 +
        df.get('interceptions', 0) * -2 +
        df.get('rushing_yards', 0) * 0.1 +
        df.get('rushing_tds', 0) * 6 +
        df.get('receiving_yards', 0) * 0.1 +
        df.get('receiving_tds', 0) * 6 +
        df.get('receptions', 0) * 1.0 +  # PPR
        df.get('fumbles_lost', 0) * -2   # This specific line caused the error
    ).round(2)
    print("✅ Fantasy points calculated.")

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save to the correct, standardized path
    output_path = os.path.join(OUTPUT_DIR, 'weekly_data_processed.csv')
    df.to_csv(output_path, index=False)
    
    print(f"✅ Successfully saved processed data to: {output_path}")
    print("--- Fantasy Point Calculation Finished ---")

if __name__ == '__main__':
    calculate_fantasy_points()
