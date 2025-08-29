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
        df_matchups = pd.read_json(os.path.join(REPORTS_DIR, 'matchup_report.json'))
        print("✅ Successfully loaded all data sources (weekly, schedule, matchups).")
    except FileNotFoundError as e:
        print(f"❌ Error: A required data file was not found. {e}. Aborting.")
        return

    # --- 2. Establish Performance Baseline ---
    player_info = df_weekly[['player_id', 'player_name', 'position', 'team']].drop_duplicates(subset=['player_id'])
    
    df_weekly.sort_values(by=['player_id', 'season', 'week'], inplace=True)
    df_weekly['last_4_games_avg'] = df_weekly.groupby('player_id')['fantasy_points'].transform(lambda x: x.rolling(4, min_periods=2).mean())
    df_weekly['last_8_games_avg'] = df_weekly.groupby('player_id')['fantasy_points'].transform(lambda x: x.rolling(8, min_periods=4).mean())
    latest_stats = df_weekly.loc[df_weekly.groupby('player_id')['week'].idxmax()].copy()

    latest_stats['baseline_ppg'] = (
        latest_stats['last_4_games_avg'].fillna(0) * 0.60 + # Heavier weight on most recent performance
        latest_stats['last_8_games_avg'].fillna(0) * 0.40
    ).round(2)

    # --- 3. Analyze Future Schedule and Bye Week ---
    last_completed_week = df_weekly['week'].max()
    df_future_schedule = df_schedule[df_schedule['week'] > last_completed_week]
    
    player_futures = []
    for index, player in player_info.iterrows():
        team = player['team']
        pos = player['position']
        
        # Find remaining games and bye week
        team_schedule = df_future_schedule[(df_future_schedule['home_team'] == team) | (df_future_schedule['away_team'] == team)]
        bye_week = df_schedule[df_schedule['game_type'] == 'BYE']['week'].max() if team in df_schedule[df_schedule['game_type'] == 'BYE']['team'].values else 0

        # Find opponents
        opponents = []
        for _, game in team_schedule.iterrows():
            opponents.append(game['away_team'] if game['home_team'] == team else game['home_team'])
        
        games_remaining = TOTAL_WEEKS - last_completed_week
        if last_completed_week < bye_week <= TOTAL_WEEKS:
            games_remaining -= 1

        # --- 4. Calculate Strength of Schedule (SOS) Modifier ---
        avg_opponent_rank = df_matchups[df_matchups['team'].isin(opponents) & (df_matchups['position'] == pos)]['matchup_rank'].mean()
        
        # Create a modifier: 16.5 is the league average rank. Facing easier teams (rank < 16.5) gives a bonus.
        # The 0.015 factor controls the strength of the adjustment.
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
    
    # Create final ranks
    final_df['ros_rank'] = final_df.groupby('position')['ros_total_points'].rank(method='dense', ascending=False)
    
    # --- 6. Save the Report ---
    report_df = final_df[['player_id', 'player_name', 'position', 'team', 'ros_total_points', 'ros_rank']].sort_values(by='ros_total_points', ascending=False)
    report_df.rename(columns={'ros_total_points': 'ros_projection'}, inplace=True) # Use original column name for consistency
    
    output_path = os.path.join(REPORTS_DIR, 'ros_projections.json')
    report_df.to_json(output_path, orient='records', indent=4)
    
    print("✅ Successfully created and saved advanced ROS projections report.")

if __name__ == '__main__':
    generate_ros_projections()
