import pandas as pd
import numpy as np

def calculate_fantasy_points(df):
    """
    Calculates fantasy points based on your league's specific custom scoring rules.
    This is the master function used by all analysis scripts.
    """
    print("Calculating fantasy points using custom scoring rules...")
    
    df['fantasy_points_custom'] = 0.0

    # Define all possible scoring columns and their point values
    scoring_rules = {
        'passing_yards': 0.05, 'passing_tds': 4, 'interceptions': -2, 'passing_2pt_conversions': 2,
        'rushing_yards': 0.1, 'rushing_tds': 6, 'rushing_2pt_conversions': 2, 'rushing_first_downs': 1,
        'receptions': 1, 'receiving_yards': 0.1, 'receiving_tds': 6, 'receiving_2pt_conversions': 2,
        'receiving_first_downs': 0.5, 'fumbles_lost': -2, 'special_teams_tds': 6
    }

    # Apply scoring rules dynamically
    for column, points in scoring_rules.items():
        if column in df.columns:
            df['fantasy_points_custom'] += df[column].fillna(0) * points
    
    # Bonuses
    if 'passing_yards' in df.columns:
        df.loc[df['passing_yards'] >= 400, 'fantasy_points_custom'] += 1
    if 'rushing_yards' in df.columns:
        df.loc[df['rushing_yards'] >= 100, 'fantasy_points_custom'] += 1
    if 'receiving_yards' in df.columns:
        df.loc[df['receiving_yards'] >= 200, 'fantasy_points_custom'] += 1
    
    # D/ST Scoring
    dst_rules = {
        'sacks': 1, 'interceptions': 2, 'fumbles_recovered': 2,
        'safeties': 2, 'defensive_tds': 6, 'blocked_kicks': 2
    }
    for column, points in dst_rules.items():
        if column in df.columns:
            df.loc[df['position'] == 'DEF', 'fantasy_points_custom'] += df[column].fillna(0) * points

    if 'points_allowed' in df.columns:
        conditions_pa = [
            (df['points_allowed'] == 0), (df['points_allowed'] >= 1) & (df['points_allowed'] <= 6),
            (df['points_allowed'] >= 7) & (df['points_allowed'] <= 13), (df['points_allowed'] >= 14) & (df['points_allowed'] <= 17),
            (df['points_allowed'] >= 18) & (df['points_allowed'] <= 27), (df['points_allowed'] >= 28) & (df['points_allowed'] <= 34),
            (df['points_allowed'] >= 35) & (df['points_allowed'] <= 45), (df['points_allowed'] >= 46)
        ]
        points_pa = [5, 4, 3, 1, 0, -1, -3, -5]
        pa_points = np.select(conditions_pa, points_pa, default=0)
        df.loc[df['position'] == 'DEF', 'fantasy_points_custom'] += pa_points
    
    return df
