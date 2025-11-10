import os
import requests
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv() 

# Base URL for the DefiLlama API endpoint for APY data
DEFILLAMA_API_URL = "https://yields.llama.fi/pools" 

# Target Aave Assets/Chains to monitor (We will find the IDs dynamically)
# This list is used to FILTER the pools found under the 'aave' project.
TARGET_ASSETS = [
    # Stablecoins to monitor
    "USDC", "DAI", "USDT", "FRAX",
    # BTC assets to monitor (includes your target cbBTC)
    "WBTC", "CBTC", "rBTC",
    # ETH LSTs
    "wstETH", "rETH"
]

# Monitoring thresholds
APY_THRESHOLD = float(os.getenv("APY_THRESHOLD", "4.0")) # Now set to 4.0% via GitHub Secret

# File path configuration
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
        response = requests.get(DEFILLAMA_API_URL, timeout=20) # Increased timeout
        response.raise_for_status() 
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching DefiLlama data: {e}")
        return []


def find_target_pools_data(all_pools):
    """Searches for all pools belonging to 'Aave' and filters by asset."""
    target_data = {}
    print(f"Searching for pools belonging to project: Aave")

    for pool in all_pools:
        # 1. Filter by Project (Aave and Aave V3)
        project = pool.get('project', '').lower()
        if 'aave' not in project:
            continue
            
        # 2. Filter by Asset Symbol (USDC, CBTC, etc.)
        symbol = pool.get('symbol', '').upper()
        
        # Check if the pool's symbol is in our target asset list
        if any(asset in symbol for asset in TARGET_ASSETS):
            pool_id = pool.get('pool')
            target_data[pool_id] = pool
    
    print(f"Found {len(target_data)} relevant Aave pools to monitor.")
    return target_data


def log_and_check_pools(pools_data):
    """Processes each pool: logs data, exports latest, and checks threshold."""
    all_new_entries = []
    current_time = datetime.now().isoformat()
    
    for pool_id, pool_data in pools_data.items():
        apy_value = pool_data.get('apy', 0.0)
        
        # Determine a friendly name for logging
        pool_name = f"{pool_data.get('symbol')} ({pool_data.get('chain')} {pool_data.get('project', 'Aave')})"
        
        # 1. Create Log Entry
        new_entry = {
            'timestamp': current_time,
            'pool_id': pool_id, # This is the DefiLlama UUID
            'chain': pool_data.get('chain'),
            'asset_symbol': pool_data.get('symbol'),
            'apy': apy_value,
            'project': pool_data.get('project'),
            'tvlUsd': pool_data.get('tvlUsd', 0.0)
        }
        all_new_entries.append(new_entry)
        
        # 2. Check Threshold
        if apy_value >= APY_THRESHOLD:
            print(f"\n✨ ALERT: High Yield Detected! Pool: {pool_name} | APY: {apy_value:.2f}% >= Threshold: {APY_THRESHOLD:.2f}% ✨")
            # Future Step: Integrate your Discord/Telegram webhook here!
        else:
            print(f"Pool: {pool_name} | APY: {apy_value:.2f}% (Below threshold)")

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
            json.dump(pools_data, f, indent=4)
        print(f"Exported latest data for {len(pools_data)} pools to {EXPORT_FILE}")


def main():
    """Main execution function for the APY monitor."""
    setup_directories()
    
    all_pools = fetch_all_pool_data()
    if not all_pools:
        print("Failed to get pool data. Exiting.")
        return

    # Find the data for all relevant Aave pools
    target_pools_data = find_target_pools_data(all_pools)

    if target_pools_data:
        log_and_check_pools(target_pools_data)
        export_latest_data(target_pools_data)
    else:
        print("Could not find any relevant Aave pools. Check the TARGET_ASSETS list.")


if __name__ == "__main__":
    main()
