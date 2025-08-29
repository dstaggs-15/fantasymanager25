import pandas as pd
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Corrected path to save the processed file
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

    # Apply fantasy scoring rules (example)
    df['fantasy_points'] = (
        df['passing_yards'] * 0.04 +
        df['passing_tds'] * 4 +
        df['interceptions'] * -2 +
        df['rushing_yards'] * 0.1 +
        df['rushing_tds'] * 6 +
        df['receiving_yards'] * 0.1 +
        df['receiving_tds'] * 6 +
        df['receptions'] * 1.0 +  # PPR
        df['fumbles_lost'] * -2
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
