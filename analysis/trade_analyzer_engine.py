# analysis/trade_analyzer_engine.py
import pandas as pd
import json
import os
import sys
import datetime

def generate_trade_report():
    """
    Generates a comprehensive trade report. This version is rewritten to remove
    the dependency on the 'position' column to prevent KeyErrors.
    """
    print("\n--- Starting 8-Factor Trade Analyzer Engine (Rewritten) ---")

    # --- 1. Define File Paths ---
    ros_path = os.path.join('docs', 'data', 'reports', 'ros_projections.json')
    vorp_path = os.path.join('docs', 'data', 'reports', 'vorp_report.json')
    players_master_path = os.path.join('docs', 'data', 'raw', 'players_master.csv')
    processed_data_path = os.path.join('docs', 'data', 'processed', 'weekly_data_processed.csv')
    output_path = os.path.join('docs', 'data', 'reports', 'trade_report.json')

    # --- 2. Load and Validate Data Sources ---
    try:
        df_ros = pd.DataFrame(json.load(open(ros_path)))
        df_vorp = pd.DataFrame(json.load(open(vorp_path)))
        df_players = pd.read_csv(players_master_path)
        df_processed = pd.read_csv(processed_data_path)
        print("✅ Successfully loaded all data sources.")
    except FileNotFoundError as e:
        print(f"❌ CRITICAL ERROR: Could not find a required data file. {e}")
        sys.exit(1)

    # --- 3. MERGE AND PREPARE MASTER DATAFRAME ---
    # Merge data sources, ensuring player_display_name is the key
    df = pd.merge(df_vorp, df_ros, on='player_display_name', how='left')
    df = pd.merge(df, df_players[['player_display_name', 'age']], on='player_display_name', how='left', suffixes=('', '_player'))

    df.rename(columns={'rank': 'ros_rank'}, inplace=True)

    # --- 4. Calculate Additional Metrics ---
    team_offense = df_processed.groupby('recent_team')['fantasy_points'].sum().reset_index()
    team_offense['team_offense_rank'] = team_offense['fantasy_points'].rank(ascending=False, method='first')
    df = pd.merge(df, team_offense[['recent_team', 'team_offense_rank']], on='recent_team', how='left')

    # --- 5. Run the 7-Factor Model (No Position Dependency) ---
    trade_values = []
    
    # Pre-calculate max values across all players
    max_ppg_overall = df['ppg'].max()
    max_std_overall = df['consistency'].max()
    max_vorp_overall = df['vorp'].max()

    for index, player in df.iterrows():
        # Get position for display, but don't use it in calculations
        pos_display = player.get('position', 'N/A')

        ros_score = ((300 - player['ros_rank']) / 299) * 10 if pd.notna(player['ros_rank']) else 2.0
        ppg_score = (player['ppg'] / max_ppg_overall) * 10 if max_ppg_overall > 0 else 0
        
        if pd.notna(player['ros_rank']):
            if player['ros_rank'] <= 15: tier_score = 10
            elif player['ros_rank'] <= 30: tier_score = 9
            elif player['ros_rank'] <= 60: tier_score = 8
            elif player['ros_rank'] <= 90: tier_score = 7
            else: tier_score = 6
        else: tier_score = 5

        start_score = ppg_score # Use talent score as proxy for weekly upside
        consistency_score = (1 - (player['consistency'] / max_std_overall)) * 10 if pd.notna(player['consistency']) and max_std_overall > 0 else 5.0
        efficiency_score = (player['vorp'] / max_vorp_overall) * 10 if max_vorp_overall > 0 else 0
        offense_score = ((32 - player['team_offense_rank']) / 31) * 10 if pd.notna(player['team_offense_rank']) else 5.0

        weights = {'ros': 0.35, 'ppg': 0.20, 'tier': 0.15, 'start': 0.10, 'consistency': 0.10, 'efficiency': 0.05, 'offense': 0.05}
        final_value = (ros_score * weights['ros']) + (ppg_score * weights['ppg']) + (tier_score * weights['tier']) + \
                      (start_score * weights['start']) + (consistency_score * weights['consistency']) + \
                      (efficiency_score * weights['efficiency']) + (offense_score * weights['offense'])

        trade_values.append({
            'player_name': player['player_display_name'],
            'position': pos_display,
            'team': player['recent_team'],
            'trade_value': round(final_value * 10, 1),
            'breakdown': {
                'ROS Projection': round(ros_score, 1),
                'Proven Production': round(ppg_score, 1),
                'Player Tier': round(tier_score, 1),
                'Weekly Upside': round(start_score, 1),
                'Consistency': round(consistency_score, 1),
                'Efficiency': round(efficiency_score, 1),
                'Team Offense': round(offense_score, 1)
            }
        })
    
    with open(output_path, 'w') as f:
        json.dump(trade_values, f, indent=4)
        
    print(f"✅ Successfully created 7-Factor Trade Report at: {output_path}")

if __name__ == '__main__':
    generate_trade_report()
