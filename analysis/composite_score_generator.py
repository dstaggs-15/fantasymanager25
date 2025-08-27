# analysis/composite_score_generator.py
import pandas as pd
import json
import os
import sys
import datetime

def generate_start_score():
    """
    Combines player PPG, matchup data, and O-line rankings to create a single,
    weighted "Start Score" for each player for the upcoming week.
    """
    print("\n--- Starting Composite 'Start Score' Generation ---")

    # --- 1. Define File Paths ---
    vorp_report_path = os.path.join('docs', 'data', 'reports', 'vorp_report.json')
    matchup_report_path = os.path.join('docs', 'data', 'reports', 'matchup_report.json')
    oline_rankings_path = os.path.join('docs', 'data', 'raw', 'oline_rankings.csv')
    schedule_path = os.path.join('docs', 'data', 'raw', 'schedule_raw.csv')
    output_path = os.path.join('docs', 'data', 'reports', 'start_scores.json')

    # --- 2. Load All Necessary Data ---
    try:
        with open(vorp_report_path, 'r') as f:
            df_vorp = pd.DataFrame(json.load(f))
        with open(matchup_report_path, 'r') as f:
            matchup_data = json.load(f)
        df_oline = pd.read_csv(oline_rankings_path)
        df_schedule = pd.read_csv(schedule_path)
        print("✅ Successfully loaded all data sources.")
    except FileNotFoundError as e:
        print(f"❌ CRITICAL ERROR: Could not find a required data file. {e}")
        sys.exit(1)

    # --- 3. Find the Upcoming Week's Matchups ---
    latest_season = df_schedule['season'].max()
    games_played = df_schedule[(df_schedule['season'] == latest_season) & (df_schedule['result'].notna())]
    last_week_played = games_played['week'].max() if not games_played.empty else 0
    upcoming_week = int(last_week_played + 1)
    
    print(f"Generating scores for Season {latest_season}, Week {upcoming_week}")
    
    upcoming_games = df_schedule[(df_schedule['season'] == latest_season) & (df_schedule['week'] == upcoming_week)]
    home_teams = upcoming_games[['home_team', 'away_team']].rename(columns={'home_team': 'team', 'away_team': 'opponent'})
    away_teams = upcoming_games[['away_team', 'home_team']].rename(columns={'away_team': 'team', 'home_team': 'opponent'})
    upcoming_matchups = pd.concat([home_teams, away_teams])

    # --- 4. Calculate Scores for Each Player ---
    start_scores = []
    
    for index, player in df_vorp.iterrows():
        player_team = player['recent_team']
        player_pos = player['position']
        
        # --- Factor 1: Baseline Talent (PPG) ---
        max_ppg = df_vorp[df_vorp['position'] == player_pos]['ppg'].max()
        talent_score = (player['ppg'] / max_ppg) * 10 if max_ppg > 0 else 0

        # --- Get Matchup Info ---
        matchup_info = upcoming_matchups[upcoming_matchups['team'] == player_team]
        if matchup_info.empty:
            start_scores.append({
                'player_display_name': player['player_display_name'], 'position': player_pos, 'team': player_team,
                'start_score': 0, 'opponent': 'BYE', 'breakdown': 'On Bye Week'
            })
            continue
        
        opponent = matchup_info.iloc[0]['opponent']
        
        # --- Factor 2: Matchup ---
        matchup_rank = 16 # Default to average
        if player_pos in matchup_data and any(team['team'] == opponent for team in matchup_data[player_pos]):
            matchup_rank = [team['rank'] for team in matchup_data[player_pos] if team['team'] == opponent][0]
        matchup_score = ((32 - matchup_rank) / 31) * 10

        # --- Factor 3: O-Line ---
        oline_rank_row = df_oline[df_oline['team'] == player_team]
        oline_rank = oline_rank_row.iloc[0]['rank'] if not oline_rank_row.empty else 16
        oline_score = ((32 - oline_rank) / 31) * 10

        # --- Final Weighted Score ---
        weights = {'talent': 0.45, 'matchup': 0.40, 'oline': 0.15}
        final_score = (talent_score * weights['talent']) + (matchup_score * weights['matchup']) + (oline_score * weights['oline'])

        start_scores.append({
            'player_display_name': player['player_display_name'], 'position': player_pos, 'team': player_team,
            'opponent': opponent, 'start_score': round(final_score, 1),
            'breakdown': {
                'Player Talent (PPG)': round(talent_score, 1),
                'Matchup vs. ' + opponent: round(matchup_score, 1),
                'O-Line Rank': round(oline_score, 1)
            }
        })
        
    with open(output_path, 'w') as f:
        json.dump(start_scores, f, indent=4)
        
    print(f"✅ Successfully created Start Score report at: {output_path}")

if __name__ == '__main__':
    generate_start_score()
