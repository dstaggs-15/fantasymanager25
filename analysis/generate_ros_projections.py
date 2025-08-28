# analysis/generate_ros_projections.py
import pandas as pd
import os
import sys
import json

def generate_ros_projections():
    """
    Generates our own Rest-of-Season (ROS) projections by calculating a weighted
    average of a player's recent performance.
    """
    print("\n--- Starting 'Homegrown' ROS Projection Generation ---")

    processed_data_path = os.path.join('docs', 'data', 'processed', 'weekly_data_processed.csv')
    output_path = os.path.join('docs', 'data', 'reports', 'ros_projections.json')

    try:
        df = pd.read_csv(processed_data_path)
        print("✅ Successfully loaded processed data.")
    except FileNotFoundError:
        print(f"❌ CRITICAL ERROR: Processed data file not found.")
        sys.exit(1)

    player_projections = []
    df.sort_values(by=['season', 'week'], ascending=True, inplace=True)

    for player_id in df['player_id'].unique():
        player_df = df[df['player_id'] == player_id]
        if len(player_df) < 4: continue
            
        last_4 = player_df.tail(4)['fantasy_points'].mean()
        last_8 = player_df.tail(8)['fantasy_points'].mean()
        last_16 = player_df.tail(16)['fantasy_points'].mean()
        
        weights = {'last_4': 0.5, 'last_8': 0.3, 'last_16': 0.2}
        weighted_ppg = (last_4 * weights['last_4']) + (last_8 * weights['last_8']) + (last_16 * weights['last_16'])
        
        player_info = player_df.iloc[-1]
        player_projections.append({
            'player_display_name': player_info['player_display_name'], # CORRECTED COLUMN NAME
            'position': player_info['position'],
            'team': player_info['recent_team'],
            'ros_projected_ppg': round(weighted_ppg, 2)
        })

    df_projections = pd.DataFrame(player_projections)
    df_projections['rank'] = df_projections['ros_projected_ppg'].rank(ascending=False, method='first').astype(int)
    df_projections.sort_values(by='rank', inplace=True)

    with open(output_path, 'w') as f:
        json.dump(df_projections.to_dict(orient='records'), f, indent=4)
        
    print(f"✅ Successfully created and saved ROS projections report.")

if __name__ == '__main__':
    generate_ros_projections()
