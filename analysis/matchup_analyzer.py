import pandas as pd
import os
import numpy as np
import json
import nfl_data_py as nfl

# --- Configuration ---
DATA_FILE = os.path.join('docs', 'data', 'analysis', 'nfl_data.csv')
OUTPUT_DIR = 'docs/data/analysis'
ANALYSIS_SEASON = 2024
# How many top players at each position to include in the report
RELEVANT_PLAYER_COUNT = {'QB': 32, 'RB': 64, 'WR': 80, 'TE': 32}

def calculate_fantasy_points(df):
    """
    Calculates fantasy points based on your league's specific custom scoring rules.
    """
    df['fantasy_points_custom'] = 0.0
    scoring_rules = {
        'passing_yards': 0.05, 'passing_tds': 4, 'interceptions': -2, 'passing_2pt_conversions': 2,
        'rushing_yards': 0.1, 'rushing_tds': 6, 'rushing_2pt_conversions': 2, 'rushing_first_downs': 1,
        'receptions': 1, 'receiving_yards': 0.1, 'receiving_tds': 6, 'receiving_2pt_conversions': 2,
        'receiving_first_downs': 0.5, 'fumbles_lost': -2, 'special_teams_tds': 6
    }
    for column, points in scoring_rules.items():
        if column in df.columns:
            df['fantasy_points_custom'] += df[column].fillna(0) * points
    return df

def main():
    print("--- Starting Advanced Matchup Analyzer ---")
    
    try:
        df = pd.read_csv(DATA_FILE, low_memory=False)
    except FileNotFoundError:
        print(f"❌ ERROR: Data file not found.")
        return

    df = calculate_fantasy_points(df)

    # 1. Get a list of all fantasy-relevant players based on last season's PPG
    season_df = df[df['season'] == ANALYSIS_SEASON].copy()
    player_ppg = season_df.groupby(['player_id', 'player_display_name', 'position', 'recent_team'])['fantasy_points_custom'].mean().reset_index()
    player_ppg = player_ppg.rename(columns={'fantasy_points_custom': 'player_ppg'})
    
    relevant_players_list = []
    for pos, count in RELEVANT_PLAYER_COUNT.items():
        top_players = player_ppg[player_ppg['position'] == pos].sort_values(by='player_ppg', ascending=False).head(count)
        relevant_players_list.append(top_players)
    relevant_players_df = pd.concat(relevant_players_list)

    # 2. Calculate Defensive Rankings
    print(f"Calculating defensive rankings...")
    season_df['opponent'] = np.where(season_df['recent_team'] == season_df['home_team'], season_df['away_team'], season_df['home_team'])
    points_allowed = season_df.groupby(['opponent', 'position'])['fantasy_points_custom'].mean().reset_index()
    points_allowed = points_allowed.rename(columns={'opponent': 'team', 'fantasy_points_custom': 'ppg_allowed'})
    points_allowed['rank'] = points_allowed.groupby('position')['ppg_allowed'].rank(ascending=False, method='max')
    
    # 3. Get the upcoming schedule
    print("Fetching upcoming NFL schedule...")
    schedule = nfl.import_schedules(years=[2025])
    next_week = schedule[schedule['week'] > 0]['week'].min()
    upcoming_games = schedule[schedule['week'] == next_week]
    
    # 4. Analyze matchups for ALL relevant players
    print("Analyzing matchups for all relevant players...")
    matchup_report = []
    
    for index, player in relevant_players_df.iterrows():
        player_name = player['player_display_name']
        player_team = player['recent_team']
        player_pos = player['position']
        player_avg_ppg = player['player_ppg']
        
        game = upcoming_games[(upcoming_games['home_team'] == player_team) | (upcoming_games['away_team'] == player_team)]
        if game.empty: continue # Skip players on a bye week
            
        opponent_team = game['away_team'].iloc[0] if game['home_team'].iloc[0] == player_team else game['home_team'].iloc[0]
        def_rank_row = points_allowed[(points_allowed['team'] == opponent_team) & (points_allowed['position'] == player_pos)]
        
        if def_rank_row.empty:
            rating, details, ppg_allowed, projection = "Average", "No ranking data.", player_avg_ppg, player_avg_ppg
        else:
            rank = def_rank_row['rank'].iloc[0]
            ppg_allowed = def_rank_row['ppg_allowed'].iloc[0]
            league_avg_allowed = points_allowed[points_allowed['position'] == player_pos]['ppg_allowed'].mean()
            projection = player_avg_ppg * (ppg_allowed / league_avg_allowed) if league_avg_allowed > 0 else player_avg_ppg
            if rank <= 5: rating = "Great"
            elif rank <= 12: rating = "Good"
            elif rank <= 20: rating = "Average"
            elif rank <= 28: rating = "Bad"
            else: rating = "Very Bad"
            details = f"vs. #{
