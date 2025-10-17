import json
import pandas as pd
import numpy as np
import os
from datetime import datetime

userdata_path = 'user_data/'
ratings_path = 'user_ratings/'

def load_json_files_with_datetime(path, file_type='ratings'):
    """
    Load all JSON files from a directory and add creation datetime.
    
    Parameters:
    - path: directory path containing JSON files
    - file_type: string to identify the type of data (for column naming)
    
    Returns:
    - DataFrame with all records and file_created_at column
    """
    all_data = []
    
    for filename in os.listdir(path):
        if filename.endswith('.json'):
            filepath = os.path.join(path, filename)
            
            # Get file modification time (preserved when copying between machines)
            modification_time = os.path.getmtime(filepath)
            creation_datetime = datetime.fromtimestamp(modification_time)
            
            # Load JSON file
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Handle both single dict and list of dicts
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                data = [{'content': data}]
            
            # Add metadata to each record
            for record in data:
                record['file_created_at'] = creation_datetime
                record['filename'] = filename
            
            all_data.extend(data)
    

    df = pd.DataFrame(all_data)
    return df

# Load ratings
df_ratings = load_json_files_with_datetime(ratings_path, 'ratings')
df_ratings.to_csv('output/ratings.csv')
print(f"Loaded {len(df_ratings)} ratings from {df_ratings['filename'].nunique()} files")
print(f"Number of rated actions: {df_ratings['id'].nunique()}")

# Load user data
df_users = load_json_files_with_datetime(userdata_path, 'users')
df_users.to_csv('output/users.csv')
print(f"\nLoaded {len(df_users)} user records from {df_users['filename'].nunique()} files")
print(f"Number of unique users: {df_users['user_id'].nunique()}")

# Generate log file with statistics
log_path = 'output/rating_log.txt'
with open(log_path, 'w') as log_file:
    log_file.write("=" * 60 + "\n")
    log_file.write("CREATIVITY RATING APP - DATA EXPORT LOG\n")
    log_file.write("=" * 60 + "\n")
    log_file.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    # 1. Number of unique actions rated
    num_unique_actions = df_ratings['id'].nunique()
    log_file.write(f"Number of unique actions rated: {num_unique_actions}\n\n")

    # 2. Number of raters involved
    num_unique_raters = df_users['user_id'].nunique()
    log_file.write(f"Number of raters involved: {num_unique_raters}\n\n")

    # 3. Value counts of value counts for 'id' in df_ratings
    # First, count how many times each action ID has been rated
    id_rating_counts = df_ratings['id'].value_counts()
    # Then, count how many IDs have each rating count (e.g., how many IDs rated once, twice, etc.)
    rating_frequency_distribution = id_rating_counts.value_counts().sort_index()

    log_file.write("Rating frequency distribution:\n")
    log_file.write("-" * 40 + "\n")
    log_file.write(f"{'Times Rated':<15} {'Number of Actions':<20}\n")
    log_file.write("-" * 40 + "\n")
    for times_rated, num_actions in rating_frequency_distribution.items():
        log_file.write(f"{times_rated:<15} {num_actions:<20}\n")

    log_file.write("\n" + "=" * 60 + "\n")

print(f"\n[INFO] Log file created: {log_path}")