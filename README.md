# Yieldfarm_passiveinc_py
Yield monitoring script 
# 💰 YieldFarm Passive Income Monitor (GitHub Actions)

This repository hosts a Python script that **automatically monitors the Annual Percentage Yield (APY)** for a dynamic basket of key Aave V2 and V3 pools across various chains, checking them against a custom profitability threshold.

The script runs on an **hourly schedule** using GitHub Actions, logs the historical data, and is designed for real-time alerting.

---

## 🛠️ Project Status

| Component | Status | Description |
| :--- | :--- | :--- |
| **APY Data Source** | DefiLlama Yields API | Reliable, aggregated DeFi data. |
| **Scheduler** | Hourly via GitHub Actions | Runs every hour (`cron: '0 * * * *'`). |
| **Monitoring List** | All Aave Pools (filtered) | Dynamically finds pools with symbols like **USDC, DAI, WBTC, CBTC,** etc. |
| **Alert Threshold** | **4.0% APY** | Set securely via GitHub Secrets. |
| **Data Storage** | `data/logs/apy_log_aave-all.csv` | Logs a historical record of APY data. |

---

## 📂 Repository Structure

* `scripts/apy_monitor.py`: The core Python logic for fetching data, processing pools, and checking the threshold.
* `.github/workflows/monitor.yml`: The GitHub Actions configuration that sets the hourly schedule and commits logs.
* `requirements.txt`: Lists all necessary Python dependencies (`requests`, `pandas`, `python-dotenv`).
* `data/`: Contains generated logs and the latest JSON export, committed automatically after each successful run.

## ⚙️ Configuration (Secrets)

The alert threshold is set securely as a **Repository Secret** named `APY_THRESHOLD`.

* **`APY_THRESHOLD`**: Currently set to **`4.0`** (for 4.0%). To change this, update the secret value in `Settings > Secrets and variables > Actions`.

---

## 🔔 Next Enhancement: Instant Alerts

The script currently logs an alert in the console. The next step is to integrate an external notification service.

We will focus on integrating a **Discord** or **Telegram** webhook into the `apy_monitor.py` script to get instant pings on your phone.
