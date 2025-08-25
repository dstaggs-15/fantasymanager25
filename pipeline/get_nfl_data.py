# pipeline/get_nfl_data.py

import pandas as pd
import nfl_data_py as nfl
import os
import datetime # Import the datetime library
from utils import calculate_fantasy_points

def main():
    """
    Main function to run the data collection and processing pipeline.
    This script is now dynamic and will always fetch the last 4 seasons of data.
    """
    print("Starting the NFL data pipeline...")

    # --- DYNAMIC YEAR CALCULATION ---
    # Get the current year (e.g., 2025)
    current_year = datetime.date.today().year
    # Create a list of the last 4 years including the current year
    # In 2025, this will be [2022, 2023, 2024, 2025]
    YEARS = list(range(current_year - 3, current_year + 1))
    
    # Define the output path for the final master CSV file
    output_folder = os.path.join('docs', 'data')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    master_data_path = os.path.join(output_folder, 'master_data.csv')

    print(f"Dynamically determined years to fetch: {YEARS}")
    
    # Use nfl-data-py to import weekly data for the specified years
    df = nfl.import_weekly_data(years=YEARS, columns=[
        'player_id', 'player_name', 'position', 'team', 'season', 'week',
        'passing_yards', 'passing_tds', 'interceptions', 'passing_2pt_conversions',
        'rushing_yards', 'rushing_tds', 'rushing_first_downs', 'rushing_2pt_conversions',
        'receptions', 'receiving_yards', 'receiving_tds', 'receiving_first_downs', 'receiving_2pt_conversions',
        'fumbles_lost', 'special_teams_tds'
    ])
    
    print("Data fetched successfully. Now calculating fantasy points...")

    # Filter for relevant fantasy positions
    positions_to_include = ['QB', 'RB', 'WR', 'TE']
    df = df[df['position'].isin(positions_to_include)]

    # Calculate custom fantasy points for each player-game
    df['fantasy_points'] = df.apply(calculate_fantasy_points, axis=1)

    # Clean up the data for easier use in the frontend
    columns_to_keep = [
        'player_id', 'player_name', 'position', 'team',
        'season', 'week', 'fantasy_points'
    ]
    final_df = df[columns_to_keep].copy()

    # Sort the data for better readability
    final_df.sort_values(by=['season', 'week', 'fantasy_points'], ascending=[False, True, False], inplace=True)
    
    print(f"Saving master data file to: {master_data_path}")
    
    # Save the processed data to the master CSV file
    final_df.to_csv(master_data_path, index=False)
    
    print("Data pipeline is now future-proof and finished successfully!")

if __name__ == '__main__':
    main()
