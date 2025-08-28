# analysis/trade_analyzer_engine.py
import pandas as pd
import json
import os
import sys
import datetime

def generate_trade_report():
    """
    Generates a comprehensive trade report by running all players through the
    advanced 8-Factor Model using only self-contained data.
    """
    print("\n--- Starting 8-Factor Trade Analyzer Engine (Self-Contained) ---")

    ros_path = os.path.join('docs', 'data', 'reports', 'ros_projections.json')
    vorp_path = os.path.join('docs', 'data', 'reports', 'vorp_report.json')
    consistency_path = os.path.join('docs', 'data', 'reports', 'consistency_report.json')
    start_score_path = os.path.join('docs', 'data', 'reports', 'start_scores.json')
    players_master_path = os.path.join('docs', 'data', 'raw', 'players_master.csv')
    processed_data_path = os.path.join('docs', 'data', 'processed', 'weekly_data_processed.csv')
    output_path = os.path.join('docs', 'data', 'reports', 'trade_report.json')

    try:
        df_ros = pd.DataFrame(json.load(open(ros_path)))
        df_vorp = pd.DataFrame(json.load(open(vorp_path)))
        df_consistency = pd.DataFrame(json.load(open(consistency_path)))
        df_start_score = pd.DataFrame(json.load(open(start_score_path)))
        df_players = pd.read_csv(players_master_path)
        df_processed = pd.read_csv(processed_data_path)
        print("✅ Successfully loaded all data sources.")
    except FileNotFoundError as e:
        print(f"❌ CRITICAL ERROR: Could not find a required data file. {e}")
        sys.exit(1)

    # --- MERGE AND PREPARE MASTER DATAFRAME ---
    df = pd.merge(df_vorp, df_ros, on='player_display_name', how='left')
    df = pd.merge(df, df_consistency[['player_display_name', 'std_dev']], on='player_display_name', how='left')
    df = pd.merge(df, df_start_score[['player_display_name', 'start_score']], on='player_display_name', how='left')
    
    # DEFINITIVE FIX: Explicitly merge using the different column names from each file.
    # This tells pandas to join where 'player_display_name' (from the left df) matches 'player_name' (from the right df).
    df = pd.merge(df, df_players[['player_name', 'birth_date']], left_on='player_display_name', right_on='player_name', how='left')
    
    df.rename(columns={'rank': 'ros_rank'}, inplace=True)

    df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce')
    df['age'] = (datetime.datetime.now() - df['birth_date']).dt.days / 365.25
    
    team_offense = df_processed.groupby('recent_team')['fantasy_points'].sum().reset_index()
    team_offense['team_offense_rank'] = team_offense['fantasy_points'].rank(ascending=False, method='first')
    df = pd.merge(df, team_offense[['recent_team', 'team_offense_rank']], on='recent_team', how='left')

    # --- RUN THE 8-FACTOR MODEL ---
    trade_values = []
    for index, player in df.iterrows():
        pos = player['position']
        
        ros_score = ((300 - player['ros_rank']) / 299) * 10 if pd.notna(player['ros_rank']) else 2.0
        max_ppg = df[df['position'] == pos]['ppg'].max()
        ppg_score = (player['ppg'] / max_ppg) * 10 if max_ppg > 0 else 0
        
        if pd.notna(player['ros_rank']):
            if player['ros_rank'] <= 12: tier_score = 10
            elif player['ros_rank'] <= 24: tier_score = 9
            elif player['ros_rank'] <= 48: tier_score = 8
            elif player['ros_rank'] <= 72: tier_score = 7
            else: tier_score = 6
        else: tier_score = 5

        start_score = (player['start_score'] / 10) * 10 if pd.notna(player['start_score']) else 5.0
        max_std = df[df['position'] == pos]['std_dev'].max()
        consistency_score = (1 - (player['std_dev'] / max_std)) * 10 if pd.notna(player['std_dev']) and max_std > 0 else 5.0
        max_vorp = df[df['position'] == pos]['vorp'].max()
        efficiency_score = (player['vorp'] / max_vorp) * 10 if max_vorp > 0 else 0
        age_score = 10 - min(10, (max(0, player['age'] - 23) / 10) * 10) if pd.notna(player['age']) else 5.0
        offense_score = ((32 - player['team_offense_rank']) / 31) * 10 if pd.notna(player['team_offense_rank']) else 5.0

        weights = {'ros': 0.30, 'ppg': 0.15, 'tier': 0.15, 'start': 0.10, 'consistency': 0.10, 'efficiency': 0.05, 'age': 0.05, 'offense': 0.05}
        final_value = (ros_score * weights['ros']) + (ppg_score * weights['ppg']) + (tier_score * weights['tier']) + \
                      (start_score * weights['start']) + (consistency_score * weights['consistency']) + (efficiency_score * weights['efficiency']) + \
                      (age_score * weights['age']) + (offense_score * weights['offense'])

        trade_values.append({
            'player_name': player['player_display_name'],
            'position': pos,
            'team': player['recent_team'],
            'trade_value': round(final_value * 10, 1),
            'breakdown': {
                'ROS Projection': round(ros_score, 1),
                'Proven Production': round(ppg_score, 1),
                'Player Tier': round(tier_score, 1),
                'Weekly Upside': round(start_score, 1),
                'Consistency': round(consistency_score, 1),
                'Efficiency': round(efficiency_score, 1),
                'Age': round(age_score, 1),
                'Team Offense': round(offense_score, 1)
            }
        })
    
    with open(output_path, 'w') as f:
        json.dump(trade_values, f, indent=4)
        
    print(f"✅ Successfully created 8-Factor Trade Report at: {output_path}")

if __name__ == '__main__':
    generate_trade_report()
