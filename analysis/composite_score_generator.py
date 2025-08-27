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
        print("Successfully loaded all data sources.")
    except FileNotFoundError as e:
        print(f"❌ CRITICAL ERROR: Could not find a required data file. {e}")
        sys.exit(1)

    # --- 3. Find the Upcoming Week's Matchups ---
    latest_season = df_schedule['season'].max()
    games_played_in_latest_season = df_schedule[(df_schedule['season'] == latest_season) & (df_schedule['result'].notna())]
    last_week_played = games_played_in_latest_season['week'].max() if not games_played_in_latest_season.empty else 0
    upcoming_week = last_week_played + 1
    
    print(f"Generating scores for Season {latest_season}, Week {upcoming_week}")
    
    upcoming_games = df_schedule[(df_schedule['season'] == latest_season) & (df_schedule['week'] == upcoming_week)]
    
    home_teams = upcoming_games[['home_team', 'away_team']].rename(columns={'home_team': 'team', 'away_team': 'opponent'})
    away_teams = upcoming_games[['away_team', 'home_team']].rename(columns={'away_team': 'team', 'home_team': 'opponent'})
    upcoming_matchups = pd.concat([home_teams, away_teams])

    # --- 4. Calculate Scores for Each Player ---
    start_scores = []
    
    # Normalize O-line ranks to a 0-1 scale (1 is best)
    df_oline['oline_score'] = (32 - df_oline['rank']) / 31

    for index, player in df_vorp.iterrows():
        player_team = player['recent_team']
        player_pos = player['position']
        
        # --- Factor 1: Baseline Talent (PPG) ---
        # Normalize PPG to a 0-10 scale based on max PPG for that position
        max_ppg = df_vorp[df_vorp['position'] == player_pos]['ppg'].max()
        talent_score = (player['ppg'] / max_ppg) * 10 if max_ppg > 0 else 0

        # --- Get Matchup Info ---
        matchup_info = upcoming_matchups[upcoming_matchups['team'] == player_team]
        if matchup_info.empty: # Player is on a bye week
            start_scores.append({
                'player_display_name': player['player_display_name'],
                'start_score': 0,
                'breakdown': 'On Bye Week'
            })
            continue
        
        opponent = matchup_info.iloc[0]['opponent']
        
        # --- Factor 2: Matchup ---
        matchup_rank = 16 # Default to average matchup
        if player_pos in matchup_data and opponent in [team['team'] for team in matchup_data[player_pos]]:
            matchup_rank = [team['rank'] for team in matchup_data[player_pos] if team['team'] == opponent][0]
        matchup_score = ((32 - matchup_rank) / 31) * 10 # Normalize rank (1-32) to a 0-10 scale

        # --- Factor 3: O-Line ---
        oline_rank_row = df_oline[df_oline['team'] == player_team]
        oline_score = oline_rank_row.iloc[0]['oline_score'] * 10 if not oline_rank_row.empty else 5 # Default to average if not found

        # --- Calculate Final Weighted Score ---
        weights = {'talent': 0.40, 'matchup': 0.45, 'oline': 0.15}
        
        final_score = (talent_score * weights['talent']) + \
                      (matchup_score * weights['matchup']) + \
                      (oline_score * weights['oline'])

        start_scores.append({
            'player_display_name': player['player_display_name'],
            'team': player_team,
            'position': player_pos,
            'opponent': opponent,
            'start_score': round(final_score, 1),
            'breakdown': {
                'Player Talent (PPG)': round(talent_score, 1),
                'Matchup vs. ' + opponent: round(matchup_score, 1),
                'O-Line Rank': round(oline_score, 1)
            }
        })
        
    # --- 5. Save the Report ---
    with open(output_path, 'w') as f:
        json.dump(start_scores, f, indent=4)
        
    print(f"✅ Successfully created Start Score report at: {output_path}")

if __name__ == '__main__':
    generate_start_score()
