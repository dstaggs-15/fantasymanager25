import pandas as pd
import json
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, 'docs', 'data', 'reports')
RAW_DATA_DIR = os.path.join(BASE_DIR, 'docs', 'data', 'raw')
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, 'docs', 'data', 'processed', 'weekly_data_processed.csv')
CURRENT_SEASON = 2025
CURRENT_WEEK = 1

def normalize_score(series):
    """Normalizes a pandas Series to a 0-10 scale."""
    if series.max() == series.min(): return 5.0
    return 10 * (series - series.min()) / (series.max() - series.min())

def calculate_start_scores():
    """
    Generates the 4-Factor 'Start Score' for the upcoming week.
    """
    print("--- Starting Final 4-Factor 'Start Score' Generation ---")

    try:
        vorp_df = pd.read_json(os.path.join(REPORTS_DIR, 'vorp_analyzer_report.json'))
        matchup_df = pd.read_json(os.path.join(REPORTS_DIR, 'matchup_report.json'))
        oline_df = pd.read_csv(os.path.join(RAW_DATA_DIR, 'oline_rankings.csv'))
        schedule_df = pd.read_csv(os.path.join(RAW_DATA_DIR, 'schedule_raw.csv'))
        # Load processed data for efficiency calculation
        processed_df = pd.read_csv(PROCESSED_DATA_PATH)
        print("✅ Successfully loaded all data sources.")
    except Exception as e:
        print(f"❌ Error loading a source file: {e}. Aborting.")
        return
        
    # --- FIX: Calculate QB and Skill Position Efficiency ---
    # Filter for relevant positions and stats
    pos_to_keep = ['QB', 'RB', 'WR', 'TE']
    player_season_stats = processed_df[processed_df['position'].isin(pos_to_keep)].groupby('player_id').agg({
        'passing_att': 'sum', 'passing_tds': 'sum', 'interceptions': 'sum',
        'carries': 'sum', 'rushing_tds': 'sum',
        'receptions': 'sum', 'receiving_tds': 'sum',
        'fumbles_lost': 'sum'
    }).reset_index()

    # QB Efficiency Calculation
    qbs = player_season_stats[player_season_stats['passing_att'] > 50].copy() # Min 50 attempts
    qbs['td_rate'] = qbs['passing_tds'] / qbs['passing_att']
    qbs['int_rate'] = qbs['interceptions'] / qbs['passing_att']
    # Normalize and combine. Higher TD rate is good, lower INT rate is good.
    qbs['efficiency_score'] = (normalize_score(qbs['td_rate']) - normalize_score(qbs['int_rate']) + 10) / 2
    
    # RB/WR/TE Efficiency Calculation
    skill_players = player_season_stats[player_season_stats['carries'] + player_season_stats['receptions'] > 20].copy() # Min 20 touches
    skill_players['total_touches'] = skill_players['carries'] + skill_players['receptions']
    skill_players['total_tds'] = skill_players['rushing_tds'] + skill_players['receiving_tds']
    skill_players['td_per_touch'] = skill_players['total_tds'] / skill_players['total_touches']
    skill_players['efficiency_score'] = normalize_score(skill_players['td_per_touch'])

    # Combine efficiency scores
    efficiency_scores = pd.concat([
        qbs[['player_id', 'efficiency_score']],
        skill_players[['player_id', 'efficiency_score']]
    ])
    
    # Merge efficiency scores into the main dataframe
    base_df = pd.merge(vorp_df, efficiency_scores, on='player_id', how='left')
    base_df['efficiency_score'].fillna(5.0, inplace=True) # Default for low-volume players

    # Filter schedule for the upcoming week
    weekly_schedule = schedule_df[(schedule_df['season'] == CURRENT_SEASON) & (schedule_df['week'] == CURRENT_WEEK)]
    opponent_map = {row['home_team']: row['away_team'] for _, row in weekly_schedule.iterrows()}
    opponent_map.update({row['away_team']: row['home_team'] for _, row in weekly_schedule.iterrows()})
    base_df['opponent'] = base_df['team'].map(opponent_map)
    
    # Calculate Talent, Matchup, and O-Line Scores
    max_ppg = base_df.groupby('position')['ppg'].transform('max')
    base_df['talent_score'] = 10 * (base_df['ppg'] / max_ppg)
    
    merged_df = pd.merge(base_df, matchup_df, left_on=['opponent', 'position'], right_on=['team', 'position'], how='left')
    merged_df['matchup_rank'].fillna(16, inplace=True)
    merged_df['matchup_score'] = 10 * ((32 - merged_df['matchup_rank']) / 31)
    
    merged_df = pd.merge(merged_df, oline_df, left_on='team_x', right_on='team', how='left')
    merged_df['rank'].fillna(16, inplace=True)
    merged_df['oline_score'] = 10 * ((32 - merged_df['rank']) / 31)
    
    score_cols = ['talent_score', 'matchup_score', 'oline_score', 'efficiency_score']
    merged_df[score_cols] = merged_df[score_cols].fillna(5.0) # Neutral default
    
    # Calculate Final Weighted 'Start Score'
    merged_df['start_score'] = (
        merged_df['talent_score'] * 0.40 +
        merged_df['matchup_score'] * 0.30 +
        merged_df['oline_score'] * 0.15 +
        merged_df['efficiency_score'] * 0.15
    ).round(2)
    
    print(f"Generating scores for Season {CURRENT_SEASON}, Week {CURRENT_WEEK}")
    
    final_report = merged_df[['player_id', 'player_name', 'position_x', 'team_x', 'start_score']]
    final_report.rename(columns={'position_x': 'position', 'team_x': 'team'}, inplace=True)

    output_path = os.path.join(REPORTS_DIR, 'start_score_report.json')
    final_report.to_json(output_path, orient='records', indent=4)

    print(f"✅ Successfully created final Start Score report at: {output_path}")

if __name__ == '__main__':
    calculate_start_scores()
