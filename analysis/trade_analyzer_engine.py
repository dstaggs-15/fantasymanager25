import json
import pandas as pd
from datetime import datetime
import os

# --- Constants & Configuration ---

# Define the weights for the 8-Factor Trade Value Model
# Source: Project Brief, Section 5
TRADE_VALUE_WEIGHTS = {
    'ros_projections': 0.30,
    'proven_production': 0.15,
    'player_tier': 0.15,
    'weekly_upside': 0.10,
    'roster_consistency': 0.10,
    'player_efficiency': 0.05,
    'player_age': 0.05,
    'team_offense': 0.05
}

# Define file paths based on the project structure
# Source: Project Brief, Section 3
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, 'data', 'reports')

# --- Helper Functions ---

def load_json_report(filename):
    """Loads a JSON report into a pandas DataFrame, handling potential file errors."""
    path = os.path.join(REPORTS_DIR, filename)
    try:
        df = pd.read_json(path)
        print(f"Successfully loaded {filename}")
        return df
    except Exception as e:
        print(f"Error loading {path}: {e}. Returning empty DataFrame.")
        return pd.DataFrame()

def normalize_score(series, ascending=True):
    """Normalizes a pandas Series to a 0-100 scale, handling cases with no variance."""
    if series.max() == series.min():
        return pd.Series([50] * len(series), index=series.index) # Return neutral score if all values are the same
    if ascending:
        return 100 * (series - series.min()) / (series.max() - series.min())
    else:
        return 100 * (series.max() - series) / (series.max() - series.min())

def get_player_tier_score(ros_rank):
    """Assigns a score based on a player's ROS rank tier."""
    if pd.isna(ros_rank) or ros_rank == 0: return 0
    if ros_rank <= 12: return 100
    elif ros_rank <= 24: return 85
    elif ros_rank <= 48: return 70
    elif ros_rank <= 72: return 50
    else: return 30

def calculate_age(birthdate_str):
    """Calculates player age from a birthdate string."""
    if pd.isna(birthdate_str): return 30 # Default age for missing data
    try:
        birthdate = datetime.strptime(str(birthdate_str), '%Y-%m-%d')
        today = datetime.now()
        return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    except (ValueError, TypeError):
        return 30 # Default age for malformed data

# --- Main Engine Logic ---

def generate_trade_value_report():
    """Calculates the 8-Factor Trade Value for every player and saves a JSON report."""
    print("🚀 Starting the 8-Factor Trade Value engine...")

    # 1. Load all required data sources
    ros_projections = load_json_report('ros_projections.json')
    vorp_data = load_json_report('vorp_analyzer_report.json')
    start_scores = load_json_report('start_score_report.json')
    
    if vorp_data.empty:
        print("❌ Critical error: vorp_analyzer_report.json is missing or empty. This is the base file. Aborting.")
        return

    # 2. **CRITICAL FIX**: Merge data robustly, ensuring key columns are preserved.
    # We use 'vorp_data' as the primary source of player info (name, position, team, etc.)
    # and merge other data into it. This prevents the 'position' column from disappearing.
    master_df = vorp_data.copy()
    
    # Merge ROS projections if available
    if not ros_projections.empty:
        master_df = pd.merge(master_df, ros_projections[['player_id', 'ros_projection', 'ros_rank']], on='player_id', how='left')
    else:
        master_df['ros_projection'] = 0
        master_df['ros_rank'] = 999

    # Merge Start Scores if available
    if not start_scores.empty:
        master_df = pd.merge(master_df, start_scores[['player_id', 'start_score']], on='player_id', how='left')
    else:
        master_df['start_score'] = 0

    # Fill any remaining NaN values in numeric columns with 0
    numeric_cols = master_df.select_dtypes(include='number').columns
    master_df[numeric_cols] = master_df[numeric_cols].fillna(0)
    
    print(f"📊 Successfully merged data for {len(master_df)} players.")
    
    # 3. Calculate the 8 Factor Scores using vectorized operations (no loops needed)
    master_df['ros_score'] = normalize_score(master_df['ros_projection'])
    master_df['production_score'] = normalize_score(master_df['ppg'])
    master_df['tier_score'] = master_df['ros_rank'].apply(get_player_tier_score)
    master_df['upside_score'] = master_df['start_score'] * 10
    master_df['consistency_score'] = normalize_score(master_df['std_dev'], ascending=False)
    master_df['efficiency_score'] = normalize_score(master_df['vorp'])
    master_df['age'] = master_df['birth_date'].apply(calculate_age)
    master_df['age_score'] = normalize_score(master_df['age'], ascending=False)
    
    team_offense_score = normalize_score(master_df.groupby('team')['ppg'].transform('mean'))
    master_df['offense_score'] = team_offense_score.fillna(50)

    print("✅ Calculated all 8 factor scores.")

    # 4. Calculate the Final Weighted "Trade Value"
    master_df['trade_value'] = (
        master_df['ros_score'] * TRADE_VALUE_WEIGHTS['ros_projections'] +
        master_df['production_score'] * TRADE_VALUE_WEIGHTS['proven_production'] +
        master_df['tier_score'] * TRADE_VALUE_WEIGHTS['player_tier'] +
        master_df['upside_score'] * TRADE_VALUE_WEIGHTS['weekly_upside'] +
        master_df['consistency_score'] * TRADE_VALUE_WEIGHTS['roster_consistency'] +
        master_df['efficiency_score'] * TRADE_VALUE_WEIGHTS['player_efficiency'] +
        master_df['age_score'] * TRADE_VALUE_WEIGHTS['player_age'] +
        master_df['offense_score'] * TRADE_VALUE_WEIGHTS['team_offense']
    ).round(1)

    # 5. Prepare and Save the Final Report
    output_columns = [
        'player_id', 'player_name', 'position', 'team', 'trade_value',
        'ros_score', 'production_score', 'tier_score', 'upside_score', 
        'consistency_score', 'efficiency_score', 'age_score', 'offense_score'
    ]
    final_report = master_df[output_columns].sort_values(by='trade_value', ascending=False)
    
    output_path = os.path.join(REPORTS_DIR, 'trade_value_report.json')
    final_report.to_json(output_path, orient='records', indent=4)
        
    print(f"💾 Successfully generated and saved Trade Value Report!")
    print(f"Location: {output_path}")

# --- Script Execution ---
if __name__ == '__main__':
    generate_trade_value_report()
