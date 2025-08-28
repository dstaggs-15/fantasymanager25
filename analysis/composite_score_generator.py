# analysis/composite_score_generator.py
import pandas as pd
import json
import os
import sys

def generate_start_score():
    """
    Generates a definitive 4-Factor "Start Score" for each player, now including
    key seasonal stats for display on the frontend.
    """
    print("\n--- Starting Final 4-Factor 'Start Score' Generation ---")

    # (File paths and data loading remain the same as before)
    vorp_report_path = os.path.join('docs', 'data', 'reports', 'vorp_report.json')
    matchup_report_path = os.path.join('docs', 'data', 'reports', 'matchup_report.json')
    oline_rankings_path = os.path.join('docs', 'data', 'raw', 'oline_rankings.csv')
    schedule_path = os.path.join('docs', 'data', 'raw', 'schedule_raw.csv')
    processed_data_path = os.path.join('docs', 'data', 'processed', 'weekly_data_processed.csv')
    output_path = os.path.join('docs', 'data', 'reports', 'start_scores.json')

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

    # (Prep for Analysis remains the same)
    latest_season = df_schedule['season'].max()
    games_played_df = df_schedule[(df_schedule['season'] == latest_season) & (df_schedule['result'].notna())]
    last_week_played = games_played_df['week'].max() if not games_played_df.empty else 0
    upcoming_week = int(last_week_played + 1)
    print(f"Generating scores for Season {latest_season}, Week {upcoming_week}")
    upcoming_games = df_schedule[(df_schedule['season'] == latest_season) & (df_schedule['week'] == upcoming_week)]
    home_teams = upcoming_games[['home_team', 'away_team']].rename(columns={'home_team': 'team', 'away_team': 'opponent'})
    away_teams = upcoming_games[['away_team', 'home_team']].rename(columns={'away_team': 'team', 'home_team': 'opponent'})
    upcoming_matchups = pd.concat([home_teams, away_teams])

    start_scores = []
    df_vorp = pd.merge(df_vorp, df_processed[['player_display_name', 'player_id']].drop_duplicates(), on='player_display_name', how='left')
    df_vorp.dropna(subset=['player_id'], inplace=True)

    for index, player in df_vorp.iterrows():
        # (Factor calculations remain the same)
        player_name = player['player_display_name']
        player_team = player['recent_team']
        player_pos = player['position']
        player_id = player['player_id']
        
        max_ppg = df_vorp[df_vorp['position'] == player_pos]['ppg'].max()
        talent_score = (player['ppg'] / max_ppg) * 10 if max_ppg > 0 else 0

        matchup_info = upcoming_matchups[upcoming_matchups['team'] == player_team]
        if matchup_info.empty:
            start_scores.append({'player_display_name': player_name, 'start_score': 0, 'breakdown': 'On Bye Week'})
            continue
        
        opponent = matchup_info.iloc[0]['opponent']

        matchup_rank = 16.5
        if player_pos in matchup_data and any(team['team'] == opponent for team in matchup_data[player_pos]):
            matchup_rank = [team['rank'] for team in matchup_data[player_pos] if team['team'] == opponent][0]
        matchup_score = ((32 - matchup_rank) / 31) * 10

        oline_rank_row = df_oline[df_oline['team'] == player_team]
        oline_rank = oline_rank_row.iloc[0]['rank'] if not oline_rank_row.empty else 16.5
        oline_score = ((32 - oline_rank) / 31) * 10
        
        player_history = df_processed[df_processed['player_id'] == player_id]
        player_seasonal_stats = player_history.sum()
        games_played = len(player_history)
        efficiency_score = 5.0

        if player_pos == 'RB':
            # ... (efficiency logic is the same)
        elif player_pos in ['WR', 'TE']:
            # ... (efficiency logic is the same)

        weights = {'talent': 0.40, 'matchup': 0.30, 'oline': 0.15, 'efficiency': 0.15}
        final_score = (talent_score * weights['talent']) + (matchup_score * weights['matchup']) + \
                      (oline_score * weights['oline']) + (efficiency_score * weights['efficiency'])

        # --- NEW: Calculate and add key seasonal stats ---
        stats_breakdown = {}
        if games_played > 0:
            if player_pos == 'QB':
                stats_breakdown['Pass Yds/G'] = round(player_seasonal_stats.get('passing_yards', 0) / games_played, 1)
                stats_breakdown['Pass TDs'] = int(player_seasonal_stats.get('passing_tds', 0))
                stats_breakdown['INTs'] = int(player_seasonal_stats.get('interceptions', 0))
            elif player_pos == 'RB':
                stats_breakdown['Rush Yds/G'] = round(player_seasonal_stats.get('rushing_yards', 0) / games_played, 1)
                stats_breakdown['Rec/G'] = round(player_seasonal_stats.get('receptions', 0) / games_played, 1)
                total_tds = player_seasonal_stats.get('rushing_tds', 0) + player_seasonal_stats.get('receiving_tds', 0)
                stats_breakdown['Total TDs'] = int(total_tds)
            elif player_pos in ['WR', 'TE']:
                stats_breakdown['Rec Yds/G'] = round(player_seasonal_stats.get('receiving_yards', 0) / games_played, 1)
                stats_breakdown['Rec/G'] = round(player_seasonal_stats.get('receptions', 0) / games_played, 1)
                stats_breakdown['Total TDs'] = int(player_seasonal_stats.get('receiving_tds', 0))

        start_scores.append({
            'player_display_name': player_name, 'position': player_pos, 'team': player_team, 'opponent': opponent,
            'start_score': round(final_score, 1),
            'breakdown': {
                'Talent (PPG)': round(talent_score, 1),
                'Matchup': round(matchup_score, 1),
                'O-Line': round(oline_score, 1),
                'Efficiency': round(efficiency_score, 1)
            },
            'stats': stats_breakdown # Add the new stats object
        })
        
    with open(output_path, 'w') as f:
        json.dump(start_scores, f, indent=4)
        
    print(f"✅ Successfully created final Start Score report at: {output_path}")

if __name__ == '__main__':
    generate_start_score()
