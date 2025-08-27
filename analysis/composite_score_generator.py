# analysis/composite_score_generator.py
import pandas as pd
import json
import os
import sys

def generate_start_score():
    print("\n--- Starting 4-Factor 'Start Score' Generation ---")

    # --- 1. Define File Paths ---
    vorp_report_path = os.path.join('docs', 'data', 'reports', 'vorp_report.json')
    matchup_report_path = os.path.join('docs', 'data', 'reports', 'matchup_report.json')
    oline_rankings_path = os.path.join('docs', 'data', 'raw', 'oline_rankings.csv')
    schedule_path = os.path.join('docs', 'data', 'raw', 'schedule_raw.csv')
    processed_data_path = os.path.join('docs', 'data', 'processed', 'weekly_data_processed.csv')
    output_path = os.path.join('docs', 'data', 'reports', 'start_scores.json')

    # --- 2. Load All Data ---
    try:
        df_vorp = pd.DataFrame(json.load(open(vorp_report_path)))
        matchup_data = json.load(open(matchup_report_path))
        df_oline = pd.read_csv(oline_rankings_path)
        df_schedule = pd.read_csv(schedule_path)
        df_processed = pd.read_csv(processed_data_path)
        print("✅ Successfully loaded all data sources.")
    except FileNotFoundError as e:
        print(f"❌ CRITICAL ERROR: Could not find a required data file. {e}")
        sys.exit(1)

    # --- 3. Prep for Analysis ---
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
    
    # Get player IDs into the VORP report
    df_vorp = pd.merge(df_vorp, df_processed[['player_display_name', 'player_id']].drop_duplicates(), on='player_display_name', how='left')

    for index, player in df_vorp.iterrows():
        player_name = player['player_display_name']
        player_team = player['recent_team']
        player_pos = player['position']
        player_id = player['player_id']

        # --- Factor 1: Player Talent (PPG) ---
        max_ppg = df_vorp[df_vorp['position'] == player_pos]['ppg'].max()
        talent_score = (player['ppg'] / max_ppg) * 10 if max_ppg > 0 else 0

        matchup_info = upcoming_matchups[upcoming_matchups['team'] == player_team]
        if matchup_info.empty:
            start_scores.append({
                'player_display_name': player_name, 'position': player_pos, 'team': player_team,
                'start_score': 0, 'opponent': 'BYE', 'breakdown': 'On Bye Week'
            })
            continue
        
        opponent = matchup_info.iloc[0]['opponent']

        # --- Factor 2: Weekly Matchup ---
        matchup_rank = 16.5 # Default to average
        if player_pos in matchup_data and any(team['team'] == opponent for team in matchup_data[player_pos]):
            matchup_rank = [team['rank'] for team in matchup_data[player_pos] if team['team'] == opponent][0]
        matchup_score = ((32 - matchup_rank) / 31) * 10

        # --- Factor 3: Offensive Line ---
        oline_rank_row = df_oline[df_oline['team'] == player_team]
        oline_rank = oline_rank_row.iloc[0]['rank'] if not oline_rank_row.empty else 16.5
        oline_score = ((32 - oline_rank) / 31) * 10
        
        # --- Factor 4: Player Efficiency ---
        player_seasonal_stats = df_processed[df_processed['player_id'] == player_id].sum()
        efficiency_score = 5.0 # Default
        touches = player_seasonal_stats.get('rushing_attempts', 0) + player_seasonal_stats.get('receptions', 0)
        yards = player_seasonal_stats.get('rushing_yards', 0) + player_seasonal_stats.get('receiving_yards', 0)
        if touches > 20: # Min touches for meaningful data
            ypt = yards / touches
            norm_val = 8.0 if player_pos in ['WR', 'TE'] else 5.5 # Normalization values for YPT
            efficiency_score = min(10, (ypt / norm_val) * 10)

        # --- Final Weighted Score ---
        weights = {'talent': 0.40, 'matchup': 0.30, 'oline': 0.15, 'efficiency': 0.15}
        final_score = (talent_score * weights['talent']) + (matchup_score * weights['matchup']) + \
                      (oline_score * weights['oline']) + (efficiency_score * weights['efficiency'])

        start_scores.append({
            'player_display_name': player_name, 'position': player_pos, 'team': player_team, 'opponent': opponent,
            'start_score': round(final_score, 1),
            'breakdown': {
                'Talent (PPG)': round(talent_score, 1),
                'Matchup': round(matchup_score, 1),
                'O-Line': round(oline_score, 1),
                'Efficiency': round(efficiency_score, 1)
            }
        })
        
    with open(output_path, 'w') as f:
        json.dump(start_scores, f, indent=4)
        
    print(f"✅ Successfully created 4-Factor Start Score report at: {output_path}")

if __name__ == '__main__':
    generate_start_score()
