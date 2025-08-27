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
    run blocking (yards before contact) and pass blocking (sack rate).
    """
    print("\n--- Starting 'Homegrown' O-Line Rankings Generation ---")

    # --- 1. Define Season and Output Path ---
    current_year = datetime.date.today().year
    # Analyze the most recent fully completed season
    LATEST_SEASON = current_year - 1 if datetime.date.today().month < 9 else current_year
    
    print(f"Analyzing play-by-play data for the {LATEST_SEASON} season...")
    output_path = os.path.join('docs', 'data', 'raw', 'oline_rankings.csv')

    try:
        # --- 2. Download Play-by-Play Data ---
        # This is a large dataset but contains the rich detail we need
        pbp_df = nfl.import_pbp_data(years=[LATEST_SEASON])
        print("✅ Successfully downloaded play-by-play data.")

        # --- 3. Calculate Run Blocking Grade (Yards Before Contact) ---
        print("Calculating run blocking grades...")
        run_plays = pbp_df[pbp_df['play_type'] == 'run'].copy()
        # Group by the offensive team (posteam) and calculate the average
        run_blocking = run_plays.groupby('posteam')['yards_before_contact'].mean().reset_index()
        run_blocking.rename(columns={'posteam': 'team', 'yards_before_contact': 'avg_ybco'}, inplace=True)
        # Rank teams: higher avg_ybco is better (rank 1)
        run_blocking['run_rank'] = run_blocking['avg_ybco'].rank(ascending=False, method='first').astype(int)

        # --- 4. Calculate Pass Blocking Grade (Sack Rate) ---
        print("Calculating pass blocking grades...")
        pass_plays = pbp_df[pbp_df['play_type'] == 'pass'].copy()
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
        # Merge the two ranking dataframes
        df_merged = pd.merge(run_blocking[['team', 'run_rank']], pass_blocking[['team', 'pass_rank']], on='team')
        
        # Weight them 50/50 for a final score
        df_merged['composite_score'] = (df_merged['run_rank'] * 0.5) + (df_merged['pass_rank'] * 0.5)
        
        # The final rank is based on the lowest composite score
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
