import os, json
from datetime import datetime, timezone

data_dir = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\historical_data"
files = [f for f in os.listdir(data_dir) if f.endswith(".json")]
print(f"Total historical data files: {len(files)}")

# Inspect BTCUSDT_1h.json
btc_path = os.path.join(data_dir, "BTCUSDT_1h.json")
with open(btc_path, "r", encoding="utf-8") as f:
    btc_candles = json.load(f)

first_c = btc_candles[0]
last_c = btc_candles[-1]

t_start = datetime.fromtimestamp(first_c["time"] / 1000.0 if first_c["time"] > 1e11 else first_c["time"], tz=timezone.utc)
t_end = datetime.fromtimestamp(last_c["time"] / 1000.0 if last_c["time"] > 1e11 else last_c["time"], tz=timezone.utc)

print(f"BTCUSDT 1H Candles count: {len(btc_candles):,}")
print(f"Start Date: {t_start.strftime('%Y-%m-%d %H:%M UTC')}")
print(f"End Date:   {t_end.strftime('%Y-%m-%d %H:%M UTC')}")
print(f"First Candle: Time={first_c['time']} | Open={first_c['open']} | High={first_c['high']} | Low={first_c['low']} | Close={first_c['close']} | Volume={first_c['volume']}")
print(f"Last Candle:  Time={last_c['time']} | Open={last_c['open']} | High={last_c['high']} | Low={last_c['low']} | Close={last_c['close']} | Volume={last_c['volume']}")

# Inspect SOLUSDT_1h.json
sol_path = os.path.join(data_dir, "SOLUSDT_1h.json")
if os.path.exists(sol_path):
    with open(sol_path, "r", encoding="utf-8") as f:
        sol_c = json.load(f)
    print(f"\nSOLUSDT 1H Candles count: {len(sol_c):,}")
    print(f"SOL First Price: ${sol_c[0]['close']} | SOL Last Price: ${sol_c[-1]['close']}")

# Total candles across all files
total_c = 0
for f in files:
    fp = os.path.join(data_dir, f)
    with open(fp, "r", encoding="utf-8") as fl:
        total_c += len(json.load(fl))
print(f"\nTotal Candlesticks across ALL files: {total_c:,}")
