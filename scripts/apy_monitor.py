import os
import requests
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables (like API keys or thresholds) from a .env file
load_dotenv() 

# Base URL for the DefiLlama API endpoint for APY data
DEFILLAMA_API_URL = "https://yields.llama.fi/pools" 

# Target yield pool configuration
# This is for a generic Aave V2 stablecoin pool (e.g., DAI or USDC on Polygon)
# You will replace these with the actual chain and pool ID you want to monitor
TARGET_CHAIN = "Polygon" 
TARGET_POOL_ID = os.getenv("TARGET_POOL_ID", "aave-v2-polygon-dai") 

# Monitoring thresholds
APY_THRESHOLD = float(os.getenv("APY_THRESHOLD", "5.0")) # Default 5.0%

# File path configuration
LOGS_DIR = "data/logs"
EXPORTS_DIR = "data/exports"
LOG_FILE = os.path.join(LOGS_DIR, f"apy_log_{TARGET_POOL_ID}.csv")
EXPORT_FILE = os.path.join(EXPORTS_DIR, f"apy_snapshot_{TARGET_POOL_ID}.json")


def setup_directories():
    """Ensure the log and export directories exist."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(EXPORTS_DIR, exist_ok=True)


def fetch_pool_data():
    """Fetches all yield pool data from DefiLlama."""
    print(f"Fetching data from DefiLlama: {DEFILLAMA_API_URL}")
    try:
        response = requests.get(DEFILLAMA_API_URL, timeout=15)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching DefiLlama data: {e}")
        return []


def find_target_pool(all_pools):
    """Searches for the specific target pool by chain and ID."""
    print(f"Searching for pool ID: {TARGET_POOL_ID} on Chain: {TARGET_CHAIN}")
    for pool in all_pools:
        # Check if the pool is on the target chain and matches the pool ID
        if pool.get('chain') == TARGET_CHAIN and pool.get('pool') == TARGET_POOL_ID:
            print("Target pool found.")
            return pool
    
    print(f"Warning: Target pool {TARGET_POOL_ID} not found in the list.")
    return None


def log_apy(pool_data):
    """Appends the current APY data to a CSV log file."""
    if not pool_data:
        print("No pool data to log.")
        return

    # Extract relevant data points
    current_time = datetime.now().isoformat()
    apy_value = pool_data.get('apy', 0.0)
    
    # Create a DataFrame for easy handling
    new_entry = pd.DataFrame([{
        'timestamp': current_time,
        'apy': apy_value,
        'chain': pool_data.get('chain'),
        'pool_id': pool_data.get('pool'),
        'project': pool_data.get('project'),
        'tvlUsd': pool_data.get('tvlUsd', 0.0)
    }])

    # Check if file exists to decide whether to write headers
    file_exists = os.path.exists(LOG_FILE)
    
    # Append to the CSV file
    new_entry.to_csv(LOG_FILE, mode='a', header=not file_exists, index=False)
    print(f"Logged APY: {apy_value:.2f}% to {LOG_FILE}")


def export_latest_data(pool_data):
    """Exports the full latest pool data to a JSON file."""
    if pool_data:
        with open(EXPORT_FILE, 'w') as f:
            json.dump(pool_data, f, indent=4)
        print(f"Exported latest data to {EXPORT_FILE}")


def check_threshold(apy_value):
    """Checks the APY against the defined threshold and sends an alert."""
    if apy_value >= APY_THRESHOLD:
        print(f"\n✨ ALERT: High Yield Detected! APY ({apy_value:.2f}%) >= Threshold ({APY_THRESHOLD:.2f}%) ✨")
        # --- Notification Placeholder ---
        # Future step: Integrate a function here to send a notification (Discord, Telegram, Email)
        # For example: send_notification(f"APY Alert! {TARGET_POOL_ID} is now at {apy_value:.2f}%!")
    else:
        print(f"APY ({apy_value:.2f}%) is below the threshold of {APY_THRESHOLD:.2f}%. Monitoring continues.")


def main():
    """Main execution function for the APY monitor."""
    setup_directories()
    
    all_pools = fetch_pool_data()
    if not all_pools:
        print("Failed to get pool data. Exiting.")
        return

    target_pool = find_target_pool(all_pools)

    if target_pool:
        current_apy = target_pool.get('apy', 0.0)
        
        # Log and export the data
        log_apy(target_pool)
        export_latest_data(target_pool)
        
        # Check the yield threshold
        check_threshold(current_apy)
    else:
        print(f"Could not process APY check for {TARGET_POOL_ID}. Check configuration.")


if __name__ == "__main__":
    main()
