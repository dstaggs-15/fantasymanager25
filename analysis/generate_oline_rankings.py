# analysis/generate_oline_rankings.py
import pandas as pd
import nfl_data_py as nfl
import os
import sys
import datetime

def generate_oline_rankings():
    """
    Generates its own O-line rankings by analyzing play-by-play data from the
    most recent completed NFL season. It creates a composite score based on
    run blocking (EPA per rush) and pass blocking (sack rate).
    """
    print("\n--- Starting 'Homegrown' O-Line Rankings Generation ---")

    # --- 1. Define Season and Output Path ---
    current_year = datetime.date.today().year
    LATEST_SEASON = current_year - 1 if datetime.date.today().month < 9 else current_year
    
    print(f"Analyzing play-by-play data for the {LATEST_SEASON} season...")
    output_path = os.path.join('docs', 'data', 'raw', 'oline_rankings.csv')

    try:
        # --- 2. Download Play-by-Play Data ---
        pbp_df = nfl.import_pbp_data(years=[LATEST_SEASON])
        print("✅ Successfully downloaded play-by-play data.")

        # --- 3. Calculate Run Blocking Grade (EPA per Rush) ---
        print("Calculating run blocking grades using EPA per Rush...")
        run_plays = pbp_df[(pbp_df['play_type'] == 'run') & (pbp_df['epa'].notna())].copy()
        # Group by the offensive team (posteam) and calculate the average EPA on run plays
        run_blocking = run_plays.groupby('posteam')['epa'].mean().reset_index()
        run_blocking.rename(columns={'posteam': 'team', 'epa': 'avg_run_epa'}, inplace=True)
        # Rank teams: higher avg_run_epa is better (rank 1)
        run_blocking['run_rank'] = run_blocking['avg_run_epa'].rank(ascending=False, method='first').astype(int)

        # --- 4. Calculate Pass Blocking Grade (Sack Rate) ---
        print("Calculating pass blocking grades...")
        pass_plays = pbp_df[(pbp_df['play_type'] == 'pass') & (pbp_df['sack'].notna())].copy()
        pass_blocking = pass_plays.groupby('posteam').agg(
            pass_attempts=('play_id', 'count'),
            sacks=('sack', 'sum')
        ).reset_index()
        pass_blocking['sack_rate'] = pass_blocking['sacks'] / pass_blocking['pass_attempts']
        pass_blocking.rename(columns={'posteam': 'team'}, inplace=True)
        # Rank teams: lower sack_rate is better (rank 1)
        pass_blocking['pass_rank'] = pass_blocking['sack_rate'].rank(ascending=True, method='first').astype(int)

        # --- 5. Create Composite Score and Final Ranking ---
        print("Generating composite scores and final rankings...")
        df_merged = pd.merge(run_blocking[['team', 'run_rank']], pass_blocking[['team', 'pass_rank']], on='team')
        
        df_merged['composite_score'] = (df_merged['run_rank'] * 0.5) + (df_merged['pass_rank'] * 0.5)
        
        df_merged['rank'] = df_merged['composite_score'].rank(ascending=True, method='first').astype(int)
        
        final_rankings = df_merged[['team', 'rank']].sort_values(by='rank').copy()

        # --- 6. Save the Report ---
        final_rankings.to_csv(output_path, index=False)
        print(f"✅ Successfully created and saved O-line rankings to: {output_path}")

    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred. Reason: {e}")
        sys.exit(1)

if __name__ == '__main__':
    generate_oline_rankings()
