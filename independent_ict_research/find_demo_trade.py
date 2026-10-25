import os
import sys
import json
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, 'historical_data', 'NEARUSDT_4h.json')
with open(data_path, 'r') as f:
    candles = json.load(f)

for i in range(200, len(candles) - 30):
    c = candles[i]
    prev = candles[i - 1]
    if c['low'] == min(x['low'] for x in candles[i - 10:i + 1]) and c['low'] < prev['low'] and c['close'] <= c['open']:
        highs = [x['high'] for x in candles[i:i + 15]]
        m_high = max(highs)
        h_idx = i + highs.index(m_high)
        gain = (m_high - c['low']) / c['low']
        if gain >= 0.04 and h_idx > i + 2:
            has_fvg = candles[i + 2]['low'] > prev['high'] if i + 2 < len(candles) else False
            idm = candles[h_idx - 1]['low']
            dealing_range = m_high - c['low']
            fib_50 = m_high - 0.50 * dealing_range
            fib_618 = m_high - 0.618 * dealing_range
            fib_786 = m_high - 0.786 * dealing_range

            for t in range(h_idx + 1, min(h_idx + 25, len(candles))):
                tap = candles[t]
                # IDM swept
                if tap['low'] < idm and tap['low'] <= fib_50:
                    c_range = tap['high'] - tap['low']
                    l_wick = min(tap['open'], tap['close']) - tap['low']
                    w_ratio = l_wick / c_range if c_range > 0 else 0
                    if w_ratio >= 0.18:
                        entry = tap['low']
                        tp = entry * 1.035
                        sl = c['low'] * 0.992
                        hit_tp = any(x['high'] >= tp for x in candles[t + 1:t + 20])
                        hit_sl = any(x['low'] <= sl for x in candles[t + 1:t + 20])
                        if hit_tp and not hit_sl:
                            dt_ob = datetime.fromtimestamp(c['time'] / 1000).strftime('%Y-%m-%d %H:%M')
                            dt_high = datetime.fromtimestamp(candles[h_idx]['time'] / 1000).strftime('%Y-%m-%d %H:%M')
                            dt_tap = datetime.fromtimestamp(tap['time'] / 1000).strftime('%Y-%m-%d %H:%M')
                            print("REAL SETUP FOUND:")
                            print(f"Asset: NEARUSDT 4H")
                            print(f"Candle 1 (Prior): Low={prev['low']}, High={prev['high']}")
                            print(f"Candle 2 (Valid OB): Date={dt_ob}, O={c['open']}, H={c['high']}, L={c['low']}, C={c['close']} (Swept Candle 1 low)")
                            print(f"Candle 3-5 (Displacement): FVG present, Body BOS confirmed")
                            print(f"Swing High: Date={dt_high}, High={m_high}, Gain={gain * 100:.2f}%")
                            print(f"Fib 0.50: {fib_50:.4f}, Fib 0.618: {fib_618:.4f}, Fib 0.786: {fib_786:.4f}")
                            print(f"IDM Level: {idm:.4f} (Swept by pullback)")
                            print(f"Mitigation Tap Candle: Date={dt_tap}, O={tap['open']}, H={tap['high']}, L={tap['low']}, C={tap['close']}, Rejection Wick={w_ratio * 100:.1f}%")
                            print(f"Entry: {entry:.4f}, SL: {sl:.4f}, TP: {tp:.4f}")
                            sys.exit(0)
