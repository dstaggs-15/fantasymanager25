import pandas as pd
import nfl_data_py as nfl
import os
import datetime
import sys

def get_raw_data():
    print("--- Starting Raw Data Collection ---")
    current_year = datetime.date.today().year
    YEARS = list(range(current_year - 4, current_year + 1))
    output_dir = os.path.join('docs', 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True)

    weekly_output_path = os.path.join(output_dir, 'weekly_stats_raw.csv')
    roster_output_path = os.path.join(output_dir, 'players_master.csv')
    schedule_output_path = os.path.join(output_dir, 'schedule_raw.csv')

    # --- Download Weekly Stats ---
    all_weekly_data = []
    print(f"📊 Downloading weekly player stats for {YEARS}...")
    for year in YEARS:
        try:
            yearly_df = nfl.import_weekly_data(years=[year])
            all_weekly_data.append(yearly_df)
        except Exception:
            print(f"  -> INFO: Weekly data for {year} not available. Skipping.")
    if all_weekly_data:
        weekly_df = pd.concat(all_weekly_data, ignore_index=True)
        weekly_df.to_csv(weekly_output_path, index=False)
        print("✅ Saved weekly stats.")
    else:
        print("❌ No weekly data found. Exiting.")
        sys.exit(1)

    # --- Download Player Roster Info ---
    all_rosters = []
    print("📋 Downloading player rosters...")
    for year in YEARS:
        try:
            df = nfl.import_rosters(years=[year])
            print(f"  {year} roster columns:", df.columns.tolist())
            if all(col in df.columns for col in ['player_id', 'player_name', 'birth_date']):
                all_rosters.append(df)
            else:
                print(f"  ⚠️ Skipping {year}: Missing required roster columns.")
        except Exception as e:
            print(f"  -> Failed to download roster for {year}: {e}")

    if not all_rosters:
        print("❌ No valid roster data found. Cannot continue.")
        sys.exit(1)

    roster_df = pd.concat(all_rosters, ignore_index=True)
    roster_df.rename(columns={
        'player_name': 'player_display_name',
        'team': 'recent_team'
    }, inplace=True)

    keep_cols = ['player_id', 'player_display_name', 'position', 'recent_team', 'birth_date']
    master_list = roster_df[keep_cols].drop_duplicates(subset='player_id', keep='first').copy()
    master_list.to_csv(roster_output_path, index=False)
    print("✅ Saved player master list.")

    # --- Download Schedule ---
    try:
        print("🗓️ Downloading schedule...")
        schedule_df = nfl.import_schedules(years=YEARS)
        schedule_df.to_csv(schedule_output_path, index=False)
        print("✅ Saved schedule data.")
    except Exception as e:
        print(f"❌ Failed to download schedule data: {e}")

    print("--- Raw Data Collection Complete ---")

if __name__ == '__main__':
    get_raw_data()
