# pipeline/get_nfl_data.py

import pandas as pd
import nfl_data_py as nfl
import os
import datetime
from urllib.error import HTTPError  # Import the specific error we need to catch
from utils import calculate_fantasy_points

def main():
    """
    Main function to run the data collection and processing pipeline.
    This script is now robust and will skip years with no available data.
    """
    print("Starting the NFL data pipeline...")

    # --- DYNAMIC YEAR CALCULATION ---
    current_year = datetime.date.today().year
    YEARS = list(range(current_year - 3, current_year + 1))
    
    output_folder = os.path.join('docs', 'data')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    master_data_path = os.path.join(output_folder, 'master_data.csv')

    print(f"Dynamically determined years to fetch: {YEARS}")
    
    # --- ROBUST DATA FETCHING LOGIC ---
    all_years_data = []
    for year in YEARS:
        try:
            print(f"Fetching data for {year}...")
            # Attempt to fetch data for a single year
            df_year = nfl.import_weekly_data(years=[year], columns=[
                'player_id', 'player_name', 'position', 'team', 'season', 'week',
                'passing_yards', 'passing_tds', 'interceptions', 'passing_2pt_conversions',
                'rushing_yards', 'rushing_tds', 'rushing_first_downs', 'rushing_2pt_conversions',
                'receptions', 'receiving_yards', 'receiving_tds', 'receiving_first_downs', 'receiving_2pt_conversions',
                'fumbles_lost', 'special_teams_tds'
            ])
            all_years_data.append(df_year)
            print(f"Successfully fetched data for {year}.")
        except HTTPError:
            # If a 404 error occurs, print a warning and continue
            print(f"Warning: Data for {year} not available yet. Skipping.")
        except Exception as e:
            # Catch any other potential errors
            print(f"An unexpected error occurred for year {year}: {e}. Skipping.")

    if not all_years_data:
        print("No data could be fetched. Exiting pipeline.")
        return

    # Combine all successfully fetched years into one DataFrame
    df = pd.concat(all_years_data, ignore_index=True)
    
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
    
    final_df.to_csv(master_data_path, index=False)
    
    print("Data pipeline is now robust and finished successfully!")

if __name__ == '__main__':
    main()
