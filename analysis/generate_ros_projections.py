import pandas as pd
import json
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, 'docs', 'data', 'processed', 'weekly_data_processed.csv')
REPORTS_DIR = os.path.join(BASE_DIR, 'docs', 'data', 'reports')
RAW_DATA_DIR = os.path.join(BASE_DIR, 'docs', 'data', 'raw')
CURRENT_SEASON = 2025
TOTAL_WEEKS = 18 # Standard NFL season length

def generate_ros_projections():
    """
    Generates Rest-of-Season (ROS) projections by blending a player's weighted recent
    performance with their future strength of schedule.
    """
    print("--- Starting Advanced 'Homegrown' ROS Projection Generation ---")
    
    # --- 1. Load All Necessary Data ---
    try:
        df_weekly = pd.read_csv(PROCESSED_DATA_PATH)
        df_schedule = pd.read_csv(os.path.join(RAW_DATA_DIR, 'schedule_raw.csv'))
        
        # --- FIX: Manually load and flatten the nested matchup.json file ---
        matchup_path = os.path.join(REPORTS_DIR, 'matchup_report.json')
        with open(matchup_path, 'r') as f:
            nested_matchup_data = json.load(f)
        
        flat_matchup_list = []
        # Iterate through each position (e.g., 'QB', 'RB') in the JSON
        for position, teams in nested_matchup_data.items():
            # Iterate through the list of teams for that position
            for team_data in teams:
                team_data['position'] = position # Add the position to each team's dictionary
                flat_matchup_list.append(team_data)
        
        # Convert the flattened list of dictionaries into a DataFrame
        df_matchups = pd.DataFrame(flat_matchup_list)
        df_matchups.rename(columns={'rank': 'matchup_rank'}, inplace=True) # Rename for clarity
        
        print("✅ Successfully loaded all data sources (weekly, schedule, matchups).")
    except FileNotFoundError as e:
        print(f"❌ Error: A required data file was not found. {e}. Aborting.")
        return

    # --- 2. Establish Performance Baseline ---
    player_info_cols = ['player_id', 'player_name', 'position', 'recent_team']
    if not all(col in df_weekly.columns for col in player_info_cols):
        print(f"❌ Error: Input file is missing required columns. Needed: {player_info_cols}")
        return
        
    player_info = df_weekly[player_info_cols].drop_duplicates(subset=['player_id'])
    player_info.rename(columns={'recent_team': 'team'}, inplace=True)
    
    df_weekly.sort_values(by=['player_id', 'season', 'week'], inplace=True)
    df_weekly['last_4_games_avg'] = df_weekly.groupby('player_id')['fantasy_points'].transform(lambda x: x.rolling(4, min_periods=2).mean())
    df_weekly['last_8_games_avg'] = df_weekly.groupby('player_id')['fantasy_points'].transform(lambda x: x.rolling(8, min_periods=4).mean())
    latest_stats = df_weekly.loc[df_weekly.groupby('player_id')['week'].idxmax()].copy()

    latest_stats['baseline_ppg'] = (
        latest_stats['last_4_games_avg'].fillna(0) * 0.60 +
        latest_stats['last_8_games_avg'].fillna(0) * 0.40
    ).round(2)

    # --- 3. Analyze Future Schedule and Bye Week ---
    last_completed_week = df_weekly['week'].max()
    df_future_schedule = df_schedule[df_schedule['week'] > last_completed_week]
    
    player_futures = []
    for index, player in player_info.iterrows():
        team = player['team']
        pos = player['position']
        
        team_schedule = df_future_schedule[(df_future_schedule['home_team'] == team) | (df_future_schedule['away_team'] == team)]
        
        bye_week_df = df_schedule[(df_schedule['game_type'] == 'BYE') & (df_schedule['home_team'] == team)]
        bye_week = bye_week_df['week'].max() if not bye_week_df.empty else 0

        opponents = []
        for _, game in team_schedule.iterrows():
            opponents.append(game['away_team'] if game['home_team'] == team else game['home_team'])
        
        games_remaining = TOTAL_WEEKS - last_completed_week
        if last_completed_week < bye_week <= TOTAL_WEEKS:
            games_remaining -= 1

        # --- 4. Calculate Strength of Schedule (SOS) Modifier ---
        avg_opponent_rank = df_matchups[(df_matchups['team'].isin(opponents)) & (df_matchups['position'] == pos)]['matchup_rank'].mean()
        
        sos_modifier = 1 + ((16.5 - avg_opponent_rank) * 0.015) if not pd.isna(avg_opponent_rank) else 1.0

        player_futures.append({
            'player_id': player['player_id'],
            'games_remaining': games_remaining,
            'sos_modifier': sos_modifier
        })

    df_futures = pd.DataFrame(player_futures)

    # --- 5. Calculate Final ROS Projection ---
    final_df = pd.merge(latest_stats, df_futures, on='player_id')
    final_df = pd.merge(player_info, final_df, on='player_id', suffixes=('', '_y'))

    final_df['ros_projection_ppg'] = final_df['baseline_ppg'] * final_df['sos_modifier']
    final_df['ros_total_points'] = (final_df['ros_projection_ppg'] * final_df['games_remaining']).round(2)
    
    final_df['ros_rank'] = final_df.groupby('position')['ros_total_points'].rank(method='dense', ascending=False)
    
    # --- 6. Save the Report ---
    report_df = final_df[['player_id', 'player_name', 'position', 'team', 'ros_total_points', 'ros_rank']].sort_values(by='ros_total_points', ascending=False)
    report_df.rename(columns={'ros_total_points': 'ros_projection'}, inplace=True)
    
    output_path = os.path.join(REPORTS_DIR, 'ros_projections.json')
    report_df.to_json(output_path, orient='records', indent=4)
    
    print("✅ Successfully created and saved advanced ROS projections report.")

if __name__ == '__main__':
    generate_ros_projections()
