import pandas as pd
import json
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'weekly_data_processed.csv')
REPORTS_DIR = os.path.join(BASE_DIR, 'data', 'reports')

def generate_ros_projections():
    """
    Generates Rest-of-Season (ROS) projections based on a weighted average
    of recent player performance.
    """
    print("--- Starting 'Homegrown' ROS Projection Generation ---")
    
    try:
        df = pd.read_csv(PROCESSED_DATA_PATH)
        print("✅ Successfully loaded processed data.")
    except FileNotFoundError:
        print(f"❌ Error: Processed data file not found at {PROCESSED_DATA_PATH}. Aborting.")
        return

    # Sort data to ensure correct chronological order for rolling averages
    df.sort_values(by=['player_id', 'season', 'week'], inplace=True)

    # Calculate rolling averages for last 4, 8, and 16 games
    # The 'min_periods=1' ensures we get a value even if a player has played fewer than the window size
    df['last_4_games_avg'] = df.groupby('player_id')['fantasy_points'].transform(lambda x: x.rolling(4, min_periods=1).mean())
    df['last_8_games_avg'] = df.groupby('player_id')['fantasy_points'].transform(lambda x: x.rolling(8, min_periods=1).mean())
    df['last_16_games_avg'] = df.groupby('player_id')['fantasy_points'].transform(lambda x: x.rolling(16, min_periods=1).mean())
    
    # Get the most recent performance entry for each player
    latest_stats = df.loc[df.groupby('player_id')['week'].idxmax()]

    # Calculate the weighted ROS Projection
    # Weights: Last 4 games (50%), Last 8 games (30%), Last 16 games (20%)
    latest_stats['ros_projection'] = (
        latest_stats['last_4_games_avg'] * 0.50 +
        latest_stats['last_8_games_avg'] * 0.30 +
        latest_stats['last_16_games_avg'] * 0.20
    ).round(2)

    # Create ROS ranks by position
    latest_stats['ros_rank'] = latest_stats.groupby('position')['ros_projection'].rank(method='dense', ascending=False)
    
    # Select final columns for the report
    report_df = latest_stats[['player_id', 'player_name', 'position', 'team', 'ros_projection', 'ros_rank']]

    # --- FIX: Save the report with the correct filename ---
    output_path = os.path.join(REPORTS_DIR, 'ros_projections.json')
    
    report_json = report_df.to_dict(orient='records')
    with open(output_path, 'w') as f:
        json.dump(report_json, f, indent=4)

    print("✅ Successfully created and saved ROS projections report.")

if __name__ == '__main__':
    generate_ros_projections()
