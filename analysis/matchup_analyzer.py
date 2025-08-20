import pandas as pd
import os
import numpy as np
import json
import nfl_data_py as nfl

# --- Configuration ---
DATA_FILE = os.path.join('docs', 'data', 'analysis', 'nfl_data.csv')
OUTPUT_DIR = 'docs/data/analysis'
ANALYSIS_SEASON = 2024 # Use the most recent full season for defensive rankings

# TODO: Update this with your real roster after the draft
YOUR_TEAM_ROSTER = [
    'Lamar Jackson', 'Derrick Henry', 'Christian McCaffrey',
    'Ja\'Marr Chase', 'A.J. Brown', 'Travis Kelce', 'Jahmyr Gibbs'
]

def calculate_fantasy_points(df):
    # This is the same custom scoring function from our other scripts
    df['fantasy_points_custom'] = 0.0
    scoring_rules = {
        'passing_yards': 0.05, 'passing_tds': 4, 'interceptions': -2, 'passing_2pt_conversions': 2,
        'rushing_yards': 0.1, 'rushing_tds': 6, 'rushing_2pt_conversions': 2, 'rushing_first_downs': 1,
        'receptions': 1, 'receiving_yards': 0.1, 'receiving_tds': 6, 'receiving_2pt_conversions': 2,
        'receiving_first_downs': 0.5, 'fumbles_lost': -2, 'special_teams_tds': 6
    }
    for column, points in scoring_rules.items():
        if column in df.columns:
            df['fantasy_points_custom'] += df[column].fillna(0) * points
    return df

def main():
    print("--- Starting Matchup Analyzer ---")
    
    try:
        df = pd.read_csv(DATA_FILE, low_memory=False)
    except FileNotFoundError:
        print(f"❌ ERROR: Data file not found.")
        return

    df = calculate_fantasy_points(df)

    # 1. Calculate Defensive Rankings (Points Allowed Per Game to each Position)
    print(f"Calculating defensive rankings based on {ANALYSIS_SEASON} data...")
    season_df = df[df['season'] == ANALYSIS_SEASON]
    
    # Figure out points allowed by each defense to each position
    points_allowed = season_df.groupby(['opponent', 'position'])['fantasy_points_custom'].mean().reset_index()
    points_allowed = points_allowed.rename(columns={'opponent': 'team', 'fantasy_points_custom': 'ppg_allowed'})

    # Rank the defenses
    points_allowed['rank'] = points_allowed.groupby('position')['ppg_allowed'].rank(ascending=False)
    
    # 2. Get the upcoming schedule
    print("Fetching upcoming NFL schedule...")
    # nfl-data-py automatically gets the next season's schedule if available
    schedule = nfl.import_schedules(years=[2025])
    next_week = schedule[schedule['week'] > 0]['week'].min()
    upcoming_games = schedule[schedule['week'] == next_week]
    print(f"Found schedule for Week {next_week}.")

    # 3. Analyze matchups for your team
    print("Analyzing matchups for your roster...")
    matchup_report = []
    player_info = df[['player_display_name', 'position', 'recent_team']].drop_duplicates(subset=['player_display_name'])

    for player_name in YOUR_TEAM_ROSTER:
        player = player_info[player_info['player_display_name'] == player_name]
        if player.empty:
            print(f"Warning: Could not find player '{player_name}' in dataset.")
            continue
        
        player_team = player['recent_team'].iloc[0]
        player_pos = player['position'].iloc[0]
        
        # Find the player's game this week
        game = upcoming_games[(upcoming_games['home_team'] == player_team) | (upcoming_games['away_team'] == player_team)]
        if game.empty:
            matchup_report.append({'player': player_name, 'opponent': 'BYE WEEK', 'rating': 'N/A'})
            continue
            
        # Determine opponent
        opponent = game['away_team'].iloc[0] if game['home_team'].iloc[0] == player_team else game['home_team'].iloc[0]
        
        # Get opponent's defensive rank against this position
        def_rank = points_allowed[(points_allowed['team'] == opponent) & (points_allowed['position'] == player_pos)]
        
        if def_rank.empty:
            rating = "Average"
        else:
            rank = def_rank['rank'].iloc[0]
            if rank <= 5: rating = "Great"
            elif rank <= 12: rating = "Good"
            elif rank <= 20: rating = "Average"
            elif rank <= 28: rating = "Bad"
            else: rating = "Very Bad"

        matchup_report.append({
            'player': player_name,
            'position': player_pos,
            'opponent': opponent,
            'rating': rating,
            'details': f"vs. the #{int(rank)} easiest defense for {player_pos}s" if not def_rank.empty else "No ranking data"
        })

    # 4. Save the report
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'matchup_report.json')
    final_report = {'week': int(next_week), 'matchups': matchup_report}
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    print(f"✅ Matchup analysis report saved to {output_path}")

if __name__ == '__main__':
    main()
