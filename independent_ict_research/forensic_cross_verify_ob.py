import json
import os
from datetime import datetime

base_dir = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
with open(os.path.join(base_dir, "historical_data", "NEARUSDT_4h.json"), "r") as f:
    candles = json.load(f)

# Find the exact candle with low 1.433
target_idx = -1
for idx, c in enumerate(candles):
    if abs(c["low"] - 1.433) < 0.001:
        target_idx = idx
        break

print(f"Target Index: {target_idx}")
if target_idx != -1:
    print("--- RAW CANDLE SEQUENCE ---")
    for k in range(target_idx - 3, target_idx + 10):
        c = candles[k]
        dt = datetime.fromtimestamp(c["time"] / 1000).strftime("%Y-%m-%d %H:%M")
        color = "GREEN" if c["close"] > c["open"] else ("RED" if c["close"] < c["open"] else "DOJI")
        role = ""
        if k == target_idx - 1:
            role = "<-- CANDLE 1 (Prior Reference Candle)"
        elif k == target_idx:
            role = "<-- CANDLE 2 (CANDIDATE ORDER BLOCK)"
        elif k == target_idx + 1:
            role = "<-- CANDLE 3 (Displacement 1)"
        elif k == target_idx + 2:
            role = "<-- CANDLE 4 (Displacement 2)"
        elif k == target_idx + 3:
            role = "<-- CANDLE 5 (Displacement 3)"
            
        print(f"[{k}] {dt} | {color:<5} | O: {c['open']:.4f} | H: {c['high']:.4f} | L: {c['low']:.4f} | C: {c['close']:.4f} {role}")

    print("\n--- FULL TIMELINE TO MITIGATION ---")
    for k in range(548, 590):
        c = candles[k]
        dt = datetime.fromtimestamp(c["time"] / 1000).strftime("%Y-%m-%d %H:%M")
        color = "GREEN" if c["close"] > c["open"] else ("RED" if c["close"] < c["open"] else "DOJI")
        print(f"[{k}] {dt} | {color:<5} | O: {c['open']:.4f} | H: {c['high']:.4f} | L: {c['low']:.4f} | C: {c['close']:.4f}")

