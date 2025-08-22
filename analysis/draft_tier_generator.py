import pandas as pd
import os
import json
from pipeline.utils import calculate_fantasy_points # Use the shared function

DATA_FILE = os.path.join('docs', 'data', 'analysis', 'nfl_data.csv')
# ... (rest of configuration and generate_tiers function are unchanged)
def generate_tiers(player_data, position, num_tiers=6):
    # ... (unchanged)
def main():
    # ... (main logic is unchanged, but it now calls the correct scoring function)
    df = pd.read_csv(DATA_FILE, low_memory=False)
    df = calculate_fantasy_points(df)
    # ... (rest of main is unchanged)
