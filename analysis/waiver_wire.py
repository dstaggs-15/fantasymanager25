import pandas as pd
import os
import numpy as np
import json

# --- Configuration ---
DATA_FILE = os.path.join('data', 'analysis', 'nfl_data_with_weather.csv')
OUTPUT_DIR = 'docs/data/analysis'

def calculate_fantasy_points(df):
    # ... (calculation logic is unchanged)
    df['fantasy_points_custom'] = 0.0
    scoring_rules = {
        'passing_yards': 0.05, 'passing_tds': 4, 'interceptions': -2, 'passing_2pt_conversions': 2,
        'rushing_yards': 0.1, 'rushing_tds': 6, 'rushing_2pt_conversions': 2, 'rushing_first_downs': 1,
        'receptions': 1, 'receiving_yards': 0.1, 'receiving_tds': 6, 'receiving_2pt_conversions': 2,
        'receiving_first_downs': 0.5, 'fumbles_lost': -2, 'special_teams_tds': 6,
        'pat_made': 1, 'fg_made_0_39': 3, 'fg_made_40_49': 4, 'fg_made_50_59': 5,
        'fg_made_60_': 6, 'fg_missed': -1
    }
    for column, points in scoring_rules.items():
        if column in df.columns:
            df['fantasy_points_custom'] += df[column].fillna(0) * points
    if 'passing_yards' in df.columns:
        df.loc[df['passing_yards'] >= 400, 'fantasy_points_custom'] += 1
    if 'rushing_yards' in df.columns:
        df.loc[df['rushing_yards'] >= 100, 'fantasy_points_custom'] += 1
    if 'receiving_yards' in df.columns:
        df.loc[df['receiving_yards'] >= 200, 'fantasy_points_custom'] += 1
    dst_rules = {
        'sacks': 1, 'interceptions': 2, 'fumbles_recovered': 2,
        'safeties': 2, 'defensive_tds': 6, 'blocked_kicks': 2
    }
    for column, points in dst_rules.items():
        if column in df.columns:
            df.loc[df['position'] == 'DEF', 'fantasy_points_custom'] += df[column].fillna(0) * points
    if 'points_allowed' in df.columns:
        conditions = [
            (df['points_allowed'] == 0), (df['points_allowed'] >= 1) & (df['points_allowed'] <= 6),
            (df['points_allowed'] >= 7) & (df['points_allowed'] <= 13), (df['points_allowed'] >= 14) & (df['points_allowed'] <= 17),
            (df['points_allowed'] >= 18) & (df['points_allowed'] <= 27), (df['points_allowed'] >= 28) & (df['points_allowed'] <= 34),
            (df['points_allowed'] >= 35) & (df['points_allowed'] <= 45), (df['points_allowed'] >= 46)
        ]
        points = [5, 4, 3, 1, 0, -1, -3, -5]
        pa_points = np.select(conditions, points, default=0)
        df.loc[df['position'] == 'DEF', 'fantasy_points_custom'] += pa_points
    return df

def main():
    print("--- Starting Waiver Wire Assistant ---")
    try:
        df = pd.read_csv(DATA_FILE, low_memory=False)
    except FileNotFoundError:
        print(f"❌ ERROR: Data file not found.")
        return

    df = calculate_fantasy_points(df)
    latest_season = df['season'].max()
    latest_week = df[df['season'] == latest_season]['week'].max()
    print(f"\n🔥 Analyzing Top Performers for Season: {latest_season}, Week: {latest_week} 🔥\n")

    latest_week_df = df[(df['season'] == latest_season) & (df['week'] == latest_week)]
    
    report_data = {'season': int(latest_season), 'week': int(latest_week), 'positions': {}}
    positions = {'QB': 10, 'RB': 15, 'WR': 15, 'TE': 10, 'K': 5, 'DEF': 5}

    for pos, num_players in positions.items():
        top_performers = (
            latest_week_df[latest_week_df['position'] == pos]
            .sort_values(by='fantasy_points_custom', ascending=False)
            .head(num_players)
        )
        display_cols = ['player_display_name', 'recent_team', 'fantasy_points_custom']
        report_data['positions'][pos] = top_performers[display_cols].round(2).to_dict('records')

    # Save the report to a JSON file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'waiver_wire_report.json')
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    print(f"✅ Waiver wire report saved to {output_path}")

if __name__ == '__main__':
    main()
