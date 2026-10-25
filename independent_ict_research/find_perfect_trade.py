import os
import sys
import json
from datetime import datetime

base_dir = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
for sym in ['SOLUSDT', 'NEARUSDT', 'FETUSDT', 'BTCUSDT', 'AVAXUSDT']:
    fpath = os.path.join(base_dir, 'historical_data', f'{sym}_4h.json')
    if not os.path.exists(fpath):
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        candles = json.load(f)

    for i in range(150, len(candles) - 40):
        c = candles[i]
        prev = candles[i - 1]
        # Valid OB: swept prior low, red candle, swing low
        if c['low'] == min(x['low'] for x in candles[i - 8:i + 1]) and c['low'] < prev['low'] and c['close'] <= c['open']:
            highs = [x['high'] for x in candles[i:i + 14]]
            m_high = max(highs)
            h_idx = i + highs.index(m_high)
            gain = (m_high - c['low']) / c['low']
            if gain >= 0.05 and h_idx > i + 2:
                has_fvg = candles[i + 2]['low'] > prev['high'] if i + 2 < len(candles) else False
                body_bos = any(candles[k]['close'] > prev['high'] for k in range(i + 1, h_idx + 1))
                if has_fvg and body_bos:
                    d_range = m_high - c['low']
                    fib_50 = m_high - 0.50 * d_range
                    fib_618 = m_high - 0.618 * d_range
                    fib_786 = m_high - 0.786 * d_range
                    ob_high = c['high']
                    ob_low = c['low']
                    ob_mt = (ob_high + ob_low) / 2.0
                    idm = candles[h_idx - 1]['low']
                    for t in range(h_idx + 1, min(h_idx + 30, len(candles))):
                        tap = candles[t]
                        if tap['low'] < idm and tap['low'] <= ob_high and tap['low'] >= ob_low * 0.998:
                            c_range = tap['high'] - tap['low']
                            l_wick = min(tap['open'], tap['close']) - tap['low']
                            w_ratio = l_wick / c_range if c_range > 0 else 0
                            if w_ratio >= 0.20 and tap['close'] >= ob_mt:
                                entry = round(ob_mt, 4)
                                sl = round(ob_low * 0.988, 4)
                                tp = round(m_high, 4)
                                hit_tp = any(x['high'] >= tp for x in candles[t + 1:t + 25])
                                hit_sl = any(x['low'] <= sl for x in candles[t + 1:t + 25])
                                if hit_tp and not hit_sl:
                                    dt_ob = datetime.fromtimestamp(c['time'] / 1000).strftime('%d %b %Y %H:%M')
                                    dt_sh = datetime.fromtimestamp(candles[h_idx]['time'] / 1000).strftime('%d %b %Y %H:%M')
                                    dt_tap = datetime.fromtimestamp(tap['time'] / 1000).strftime('%d %b %Y %H:%M')
                                    print("FOUND TEXTBOOK REAL TRADE!")
                                    print(f"Pair: {sym} 4H")
                                    print(f"OB Date: {dt_ob} | O: {c['open']} | H: {c['high']} | L: {c['low']} | C: {c['close']}")
                                    print(f"Prior Low Swept: {prev['low']} (OB L: {c['low']} < {prev['low']})")
                                    print(f"Displacement: +{gain * 100:.2f}% to Swing High: {m_high:.4f} on {dt_sh}")
                                    print(f"FVG Gap: [{prev['high']:.4f} to {candles[i + 2]['low']:.4f}]")
                                    print(f"Fib 0.50: {fib_50:.4f} | Fib 0.618: {fib_618:.4f} | Fib 0.786: {fib_786:.4f}")
                                    print(f"IDM Level: {idm:.4f} (Swept by pullback)")
                                    print(f"Entry Price (at OB MT 50%): {entry}")
                                    print(f"Tap Candle: Date: {dt_tap} | Low: {tap['low']} | Rejection Wick: {w_ratio * 100:.1f}%")
                                    print(f"Stop Loss: {sl} | Take Profit: {tp} | Risk:Reward: {(tp - entry) / (entry - sl):.2f}")
                                    sys.exit(0)
