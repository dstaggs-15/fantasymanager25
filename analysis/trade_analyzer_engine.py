import json
import pandas as pd
from datetime import datetime
import os

TRADE_VALUE_WEIGHTS = {
    'ros_projections': 0.30, 'proven_production': 0.15, 'player_tier': 0.15,
    'weekly_upside': 0.10, 'roster_consistency': 0.10, 'player_efficiency': 0.05,
    'player_age': 0.05, 'team_offense': 0.05
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, 'docs', 'data', 'reports')

def load_json_report(filename):
    path = os.path.join(REPORTS_DIR, filename)
    try:
        return pd.read_json(path)
    except Exception as e:
        print(f"Error loading {path}: {e}. Returning empty DataFrame.")
        return pd.DataFrame()

def normalize_score(series, ascending=True):
    if series.max() == series.min(): return pd.Series([50] * len(series), index=series.index)
    return 100 * ((series - series.min()) / (series.max() - series.min())) if ascending else 100 * ((series.max() - series) / (series.max() - series.min()))

def get_player_tier_score(ros_rank):
    if pd.isna(ros_rank) or ros_rank == 0: return 0
    if ros_rank <= 12: return 100
    elif ros_rank <= 24: return 85
    elif ros_rank <= 48: return 70
    elif ros_rank <= 72: return 50
    else: return 30

def generate_trade_value_report():
    print("🚀 Starting the 8-Factor Trade Value engine...")
    ros_projections = load_json_report('ros_projections.json')
    vorp_data = load_json_report('vorp_analyzer_report.json')
    start_scores = load_json_report('start_score_report.json')
    
    if vorp_data.empty:
        print("❌ Critical error: vorp_analyzer_report.json is missing or empty. Aborting.")
        return

    master_df = vorp_data.copy()
    if not ros_projections.empty: master_df = pd.merge(master_df, ros_projections[['player_id', 'ros_projection', 'ros_rank']], on='player_id', how='left')
    else: master_df[['ros_projection', 'ros_rank']] = [0, 999]
    if not start_scores.empty: master_df = pd.merge(master_df, start_scores[['player_id', 'start_score']], on='player_id', how='left')
    else: master_df['start_score'] = 0
    
    master_df.select_dtypes(include='number').fillna(0, inplace=True)
    
    master_df['ros_score'] = normalize_score(master_df['ros_projection'])
    master_df['production_score'] = normalize_score(master_df['ppg'])
    master_df['tier_score'] = master_df['ros_rank'].apply(get_player_tier_score)
    master_df['upside_score'] = master_df['start_score'] * 10
    master_df['consistency_score'] = normalize_score(master_df['std_dev'], ascending=False)
    master_df['efficiency_score'] = normalize_score(master_df['vorp'])
    master_df['age_score'] = 0 # Placeholder as age data is not used
    master_df['offense_score'] = normalize_score(master_df.groupby('team')['ppg'].transform('mean')).fillna(50)

    master_df['trade_value'] = sum(master_df[f_name.replace('_projections', '_score')] * weight for f_name, weight in TRADE_VALUE_WEIGHTS.items()).round(1)
    
    output_cols = ['player_id', 'player_name', 'position', 'team', 'trade_value']
    final_report = master_df[output_cols].sort_values(by='trade_value', ascending=False)
    
    output_path = os.path.join(REPORTS_DIR, 'trade_value_report.json')
    final_report.to_json(output_path, orient='records', indent=4)
    print(f"✅ Successfully generated and saved Trade Value Report to {output_path}")

if __name__ == '__main__':
    generate_trade_value_report()
