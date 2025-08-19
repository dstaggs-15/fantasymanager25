import pandas as pd
import os
import numpy as np

# --- Configuration ---
DATA_FILE = os.path.join('data', 'analysis', 'nfl_data_with_weather.csv')

def calculate_fantasy_points(df):
    """
    Calculates fantasy points based on your league's specific custom scoring rules.
    This version is robust and checks for the existence of each column before using it.
    """
    print("Calculating fantasy points using your league's custom scoring rules...")
    
    df['fantasy_points_custom'] = 0.0

    # Define all possible scoring columns and their point values
    scoring_rules = {
        'passing_yards': 0.05, 'passing_tds': 4, 'interceptions': -2,
        'passing_2pt_conversions': 2, 'rushing_yards': 0.1, 'rushing_tds': 6,
        'rushing_2pt_conversions': 2, 'rushing_first_downs': 1, 'receptions': 1,
        'receiving_yards': 0.1, 'receiving_tds': 6, 'receiving_2pt_conversions': 2,
        'receiving_first_downs': 0.5, 'fumbles_lost': -2, 'special_teams_tds': 6,
        'pat_made': 1, 'fg_made_0_39': 3, 'fg_made_40_49': 4, 'fg_made_50_59': 5,
        'fg_made_60_': 6, 'fg_missed': -1
    }

    # Apply scoring rules dynamically
    for column, points in scoring_rules.items():
        if column in df.columns:
            # Fill NaN (Not a Number) with 0 to prevent errors
            df['fantasy_points_custom'] += df[column].fillna(0) * points
        else:
            print(f"Warning: Column '{column}' not found in data. Skipping.")

    # --- Bonuses ---
    if 'passing_yards' in df.columns:
        df.loc[df['passing_yards'] >= 400, 'fantasy_points_custom'] += 1
    if 'rushing_yards' in df.columns:
        df.loc[df['rushing_yards'] >= 100, 'fantasy_points_custom'] += 1
    if 'receiving_yards' in df.columns:
        df.loc[df['receiving_yards'] >= 200, 'fantasy_points_custom'] += 1
    
    # --- D/ST Scoring ---
    dst_rules = {
        'sacks': 1, 'interceptions': 2, 'fumbles_recovered': 2,
        'safeties': 2, 'defensive_tds': 6, 'blocked_kicks': 2
    }
    for column, points in dst_rules.items():
        if column in df.columns:
            # Apply these points only to rows where the position is DEF
            df.loc[df['position'] == 'DEF', 'fantasy_points_custom'] += df[column].fillna(0) * points

    # Points Allowed (for D/ST position only)
    if 'points_allowed' in df.columns:
        conditions_pa = [
            (df['points_allowed'] == 0), (df['points_allowed'] <= 6), (df['points_allowed'] <= 13),
            (df['points_allowed'] <= 17), (df['points_allowed'] <= 34), (df['points_allowed'] <= 45),
