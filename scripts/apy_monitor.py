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

# Target Aave Pool IDs to monitor (Stablecoins, BTC, and key assets across V2/V3)
TARGET_POOL_IDS = [
    # Aave V3 Pools (Stablecoins)
    "aave-v3-arbitrum-usdc",
    "aave-v3-polygon-usdc",
    "aave-v3-ethereum-usdc",
    "aave-v3-optimism-usdc",
    "aave-v3-avalanche-usdc",
    "aave-v3-base-usdc",
    # Aave V3 Pools (BTC Assets)
    "aave-v3-ethereum-wbtc",     # Wrapped BTC (WBTC)
    "aave-v3-ethereum-cbbtc",    # Coinbase Wrapped BTC (Your Target)
    "aave-v3-arbitrum-wbtc",
    # Aave V2 Pools (Legacy)
    "aave-v2-polygon-dai",
    "aave-v2-ethereum-dai",
]

# Monitoring thresholds
# Gets the APY_THRESHOLD from GitHub Secrets/ENV, defaults to 5.0%
APY_THRESHOLD = float(os.getenv("APY_THRESHOLD", "5.0")) 

# File path configuration for batch logging/exporting all Aave pools
PROJECT_SLUG = "aave-all" 
LOGS_DIR = "data/logs"
EXPORTS_DIR = "data/exports"
LOG_FILE = os.path.join(LOGS_DIR, f"apy_log_{PROJECT_SLUG}.csv")
EXPORT_FILE = os.path.join(EXPORTS_DIR, f"apy_snapshot_{PROJECT_SLUG}.json")


def setup_directories():
    """Ensure the log and export directories exist."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(EXPORTS_DIR, exist_ok=True)


def fetch_all_pool_data():
    """Fetches all yield pool data from DefiLlama."""
    print(f"Fetching data from DefiLlama: {DEFILLAMA_API_URL}")
    try:
        response = requests.get(DEFILLAMA_API_URL, timeout=15)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching DefiLlama data: {e}")
        return []


def find_target_pools_data(all_pools):
    """Searches for the specific target pools from the full list."""
    target_data = {}
    
    # Create a dictionary for quick lookup: {pool_id: pool_data}
    pool_lookup = {pool.get('pool'): pool for pool in all_pools}
    
    print(f"Searching for {len(TARGET_POOL_IDS)} target Aave pools...")

    for pool_id in TARGET_POOL_IDS:
        if pool_id in pool_lookup:
            target_data[pool_id] = pool_lookup[pool_id]
        else:
            print(f"Warning: Pool ID {pool_id} not found.")

    return target_data


def log_and_check_pools(pools_data):
    """Processes each pool: logs data, exports latest, and checks threshold."""
    all_new_entries = []
    current_time = datetime.now().isoformat()
    
    for pool_id, pool_data in pools_data.items():
        apy_value = pool_data.get('apy', 0.0)
        
        # 1. Create Log Entry
        new_entry = {
            'timestamp': current_time,
            'pool_id': pool_data.get('pool'),
            'chain': pool_data.get('chain'),
            'apy': apy_value,
            'project': pool_data.get('project'),
            'tvlUsd': pool_data.get('tvlUsd', 0.0)
        }
        all_new_entries.append(new_entry)
        
        # 2. Check Threshold
        if apy_value >= APY_THRESHOLD:
            print(f"\n✨ ALERT: High Yield Detected! Pool: {pool_id} | APY: {apy_value:.2f}% >= Threshold: {APY_THRESHOLD:.2f}% ✨")
            # Notification Placeholder: Integrate your Discord/Telegram webhook here!
        else:
            print(f"Pool: {pool_id} | APY: {apy_value:.2f}% (Below threshold)")

    # 3. Batch Log to CSV
    if all_new_entries:
        new_df = pd.DataFrame(all_new_entries)
        file_exists = os.path.exists(LOG_FILE)
        new_df.to_csv(LOG_FILE, mode='a', header=not file_exists, index=False)
        print(f"\nSuccessfully logged {len(all_new_entries)} pool entries to {LOG_FILE}")


def export_latest_data(pools_data):
    """Exports the full latest pool data to a single JSON file."""
    if pools_data:
        with open(EXPORT_FILE, 'w') as f:
            # We export the full dictionary {pool_id: pool_data}
            json.dump(pools_data, f, indent=4)
        print(f"Exported latest data for {len(pools_data)} pools to {EXPORT_FILE}")


def main():
    """Main execution function for the APY monitor."""
    setup_directories()
    
    all_pools = fetch_all_pool_data()
    if not all_pools:
        print("Failed to get pool data. Exiting.")
        return

    # Find the data for all pools in our TARGET_POOL_IDS list
    target_pools_data = find_target_pools_data(all_pools)

    if target_pools_data:
        # Log and check all target pools
        log_and_check_pools(target_pools_data)
        
        # Export the latest data for all target pools
        export_latest_data(target_pools_data)
    else:
        print("Could not find any of the target Aave pools. Check the pool ID list.")


if __name__ == "__main__":
    main()
