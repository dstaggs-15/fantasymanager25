import pandas as pd
import os
import json
import sys # Add sys import

# Add the project's root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from pipeline.utils import calculate_fantasy_points

DATA_FILE = os.path.join('docs', 'data', 'analysis', 'nfl_data.csv')
OUTPUT_DIR = 'docs/data/analysis'

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
        top_performers = latest_week_df[latest_week_df['position'] == pos].sort_values(by='fantasy_points_custom', ascending=False).head(num_players)
        display_cols = ['player_display_name', 'recent_team', 'fantasy_points_custom']
        report_data['positions'][pos] = top_performers[display_cols].round(2).to_dict('records')

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'waiver_wire_report.json')
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    print(f"✅ Waiver wire report saved to {output_path}")

if __name__ == '__main__':
    main()
