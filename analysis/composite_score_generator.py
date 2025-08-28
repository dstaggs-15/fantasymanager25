import pandas as pd
import json
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, 'data', 'reports')
CURRENT_SEASON = 2025 # Projecting for the upcoming season
CURRENT_WEEK = 1

def generate_start_scores():
    """
    Generates the 4-Factor 'Start Score' for the upcoming week by ingesting
    VORP, Matchup, and O-Line reports.
    """
    print("--- Starting Final 4-Factor 'Start Score' Generation ---")

    # Load prerequisite reports
    try:
        vorp_df = pd.read_json(os.path.join(REPORTS_DIR, 'vorp_analyzer_report.json'))
        matchup_df = pd.read_json(os.path.join(REPORTS_DIR, 'matchup_report.json'))
        oline_df = pd.read_json(os.path.join(REPORTS_DIR, 'oline_rankings.json')) # Assuming oline script saves a JSON report
        schedule_df = pd.read_csv(os.path.join(BASE_DIR, 'data', 'raw', 'schedule_raw.csv'))
    except Exception as e:
        print(f"❌ Error loading a source file: {e}. Aborting.")
        return
        
    print("✅ Successfully loaded all data sources.")

    # Filter schedule for the upcoming week
    weekly_schedule = schedule_df[(schedule_df['season'] == CURRENT_SEASON) & (schedule_df['week'] == CURRENT_WEEK)]
    
    # Map opponent for each team
    opponent_map = {}
    for index, row in weekly_schedule.iterrows():
        opponent_map[row['home_team']] = row['away_team']
        opponent_map[row['away_team']] = row['home_team']

    vorp_df['opponent'] = vorp_df['team'].map(opponent_map)
    
    # 1. Player Talent Score (40%)
    max_ppg = vorp_df.groupby('position')['ppg'].transform('max')
    vorp_df['talent_score'] = 10 * (vorp_df['ppg'] / max_ppg)

    # 2. Weekly Matchup Score (30%)
    # Merge matchup ranks onto the main dataframe
    merged_df = pd.merge(vorp_df, matchup_df, left_on=['opponent', 'position'], right_on=['team', 'position'], how='left', suffixes=('', '_matchup'))
    merged_df['matchup_rank'].fillna(16, inplace=True) # Neutral rank for missing data
    merged_df['matchup_score'] = 10 * ((32 - merged_df['matchup_rank']) / 31)

    # 3. Offensive Line Score (15%)
    # Merge O-line ranks
    merged_df = pd.merge(merged_df, oline_df, left_on='team', right_on='team', how='left')
    merged_df['oline_rank'].fillna(16, inplace=True) # Neutral rank
    merged_df['oline_score'] = 10 * ((32 - merged_df['oline_rank']) / 31)

    # 4. Efficiency Score (15%) - Using VORP as a proxy for overall efficiency
    max_vorp = merged_df.groupby('position')['vorp'].transform('max')
    min_vorp = merged_df.groupby('position')['vorp'].transform('min')
    merged_df['efficiency_score'] = 10 * (merged_df['vorp'] - min_vorp) / (max_vorp - min_vorp)

    # Handle NaNs that might have appeared
    score_cols = ['talent_score', 'matchup_score', 'oline_score', 'efficiency_score']
    merged_df[score_cols] = merged_df[score_cols].fillna(0)
    
    # Calculate Final Weighted 'Start Score'
    merged_df['start_score'] = (
        merged_df['talent_score'] * 0.40 +
        merged_df['matchup_score'] * 0.30 +
        merged_df['oline_score'] * 0.15 +
        merged_df['efficiency_score'] * 0.15
    ).round(2)
    
    print(f"Generating scores for Season {CURRENT_SEASON}, Week {CURRENT_WEEK}")
    
    # Prepare final report
    final_report = merged_df[['player_id', 'player_name', 'position', 'team', 'start_score']]

    # --- FIX: Save the report with the correct filename ---
    output_path = os.path.join(REPORTS_DIR, 'start_score_report.json')

    report_json = final_report.to_dict(orient='records')
    with open(output_path, 'w') as f:
        json.dump(report_json, f, indent=4)

    print(f"✅ Successfully created final Start Score report at: {output_path}")

if __name__ == '__main__':
    generate_start_scores()
