import os
import json
from run_real_market_acid_test import load_local_data, TOP_22_CHAMPIONS

print("=" * 70)
print("🎯 TESTING HERMES 3.5 INSTITUTIONAL FILTERS BOOST")
print("Rule 1: Inducement (IDM) Liquidity Sweep")
print("Rule 2: Minimum 18% Rejection Absorption Wick")
print("Rule 3: 50% Mean Threshold Defense (No Falling Knives)")
print("=" * 70)

all_data = {"1h": {}, "4h": {}}
for sym in TOP_22_CHAMPIONS:
    for tf in ["1h", "4h"]:
        k = load_local_data(sym, tf)
        if len(k) >= 500:
            all_data[tf][sym] = k

trades = []
for tf in ["1h", "4h"]:
    tp_pct = 0.022 if tf == "1h" else 0.028
    sl_pct = 0.025 if tf == "1h" else 0.028

    for sym, candles in all_data[tf].items():
        n = len(candles)
        for i in range(25, n - 35):
            # Bullish Setups
            if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                sub_w = candles[i:min(i+16, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx > i + 3:
                    gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                    if gain >= 0.045:
                        idm_low = candles[high_idx - 1]["low"]
                        best_mid = -1
                        max_bg = 0.0
                        for mid in range(i+1, high_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                            fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg
                                best_mid = mid
                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = max(dec_c["open"], dec_c["close"])
                            dec_bot = dec_c["low"]
                            mt = (dec_top + dec_bot) / 2.0
                            has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                            if has_fvg:
                                for t in range(high_idx + 1, min(high_idx + 35, n)):
                                    if candles[t]["low"] <= dec_top * 1.0005:
                                        tap_c = candles[t]
                                        c_range = tap_c["high"] - tap_c["low"]
                                        swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                        l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                        w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                        
                                        # Strict Institutional Gate: IDM Sweep + 18% Wick + Close >= MT
                                        if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                            entry_p = dec_top
                                            tp_p = entry_p * (1.0 + tp_pct)
                                            sl_p = entry_p * (1.0 - sl_pct)
                                            
                                            # Check outcome
                                            win = False
                                            loss = False
                                            for f in range(t + 1, min(t + 40, n)):
                                                if candles[f]["high"] >= tp_p:
                                                    win = True
                                                    break
                                                elif candles[f]["low"] <= sl_p:
                                                    loss = True
                                                    break
                                            if win:
                                                trades.append({'sym': sym, 'side': 'LONG', 'tf': tf, 'outcome': 'WIN', 'roe': 14.0})
                                                break
                                            elif loss:
                                                trades.append({'sym': sym, 'side': 'LONG', 'tf': tf, 'outcome': 'LOSS', 'roe': -14.0})
                                                break

w = len([t for t in trades if t['outcome'] == 'WIN'])
l = len([t for t in trades if t['outcome'] == 'LOSS'])
wr = (w / len(trades) * 100) if trades else 0.0
print(f"Total Trades Identified : {len(trades)}")
print(f"Wins                    : {w}")
print(f"Losses                  : {l}")
print(f"WIN RATE                : {wr:.2f}%")
print("=" * 70)
