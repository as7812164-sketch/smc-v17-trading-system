import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime
import asyncio
import json
from feed.binance_feed import binance_feed
from config import TOP_22_CHAMPIONS, ALL_MONITORED_COINS
from engine.hermes40_live import hermes40_live_engine, calculate_atr_series

async def run_scan():
    coins = ALL_MONITORED_COINS if ALL_MONITORED_COINS else TOP_22_CHAMPIONS
    print(f"Scanning {len(coins)} coins across 4H & 1H with Hermes 4.0 Institutional Model...")
    btc_sentry = await hermes40_live_engine.evaluate_btc_macro()
    print("King BTC Sentry status:", btc_sentry)
    
    triggered_setups = []
    approaching_setups = []
    all_recent_obs = []
    
    for symbol in coins:
        for tf in ['4h', '1h']:
            try:
                candles = await binance_feed.fetch_klines(symbol, interval=tf, limit=60)
                if len(candles) < 35:
                    continue
                cur_price = float(candles[-1]['close'])
                
                # 1. Triggered & Confirmed Setups
                setups = hermes40_live_engine.detect_hermes40_setups_sync(symbol, tf, candles, btc_sentry)
                for s in setups:
                    s['current_price'] = cur_price
                    # calculate distance from entry
                    dist = round((cur_price - s['entry_price']) / cur_price * 100, 2)
                    s['current_dist_from_entry_pct'] = dist
                    triggered_setups.append(s)
                
                # 2. Developing Bedrock OBs (Valid OB with Body BOS & FVG, approaching 50% MT)
                n = len(candles)
                start_scan = max(15, n - 35)
                atrs = calculate_atr_series(candles, 14)
                
                for i in range(start_scan, n - 2):
                    c1, c2 = candles[i-1], candles[i]
                    c1_l, c1_h = float(c1['low']), float(c1['high'])
                    c2_o, c2_c = float(c2['open']), float(c2['close'])
                    c2_l, c2_h = float(c2['low']), float(c2['high'])
                    
                    # Bullish OB Check
                    if not btc_sentry.get('long_veto', False) and c2_c <= c2_o and c2_l < c1_l:
                        prior_lows = [float(c['low']) for c in candles[max(0, i-15):i+1]]
                        if c2_l == min(prior_lows):
                            sub_w = candles[i:min(i+20, n)]
                            highs = [float(c['high']) for c in sub_w]
                            m_high = max(highs)
                            h_idx = i + highs.index(m_high)
                            if h_idx > i + 2:
                                disp_gain = (m_high - c2_l) / c2_l if c2_l > 0 else 0.0
                                if disp_gain >= 0.035:
                                    has_fvg = any(float(candles[d+1]['low']) > float(candles[d-1]['high']) for d in range(i+1, min(h_idx, n-1)) if d+1 < n)
                                    prev_swing_high = max(float(x['high']) for x in candles[max(0, i-15):i])
                                    body_bos = any(float(c['close']) > prev_swing_high for c in candles[i+1:h_idx+1])
                                    if has_fvg and body_bos:
                                        entry_p = round((c2_h + c2_l) / 2.0, 6)
                                        diff_pct = round((cur_price - entry_p) / cur_price * 100, 2)
                                        atr_val = atrs[min(h_idx, len(atrs)-1)]
                                        sl_p = round(c2_l - (0.35 * atr_val), 6)
                                        tp_p = round(entry_p * 1.03, 6)
                                        
                                        all_recent_obs.append({
                                            'symbol': symbol,
                                            'side': 'LONG',
                                            'timeframe': tf,
                                            'entry_price_50mt': entry_p,
                                            'current_price': cur_price,
                                            'dist_to_entry_pct': diff_pct,
                                            'ob_range': f"{c2_l} - {c2_h}",
                                            'displacement_pct': round(disp_gain * 100, 2),
                                            'tp_price': tp_p,
                                            'sl_price': sl_p,
                                            'status': 'WAITING_FOR_RETEST' if diff_pct > 0 else 'TESTED'
                                        })
                    
                    # Bearish OB Check
                    if not btc_sentry.get('short_veto', False) and c2_c >= c2_o and c2_h > c1_h:
                        prior_highs = [float(c['high']) for c in candles[max(0, i-15):i+1]]
                        if c2_h == max(prior_highs):
                            sub_w = candles[i:min(i+20, n)]
                            lows = [float(c['low']) for c in sub_w]
                            m_low = min(lows)
                            low_idx = i + lows.index(m_low)
                            if low_idx > i + 2:
                                disp_drop = (c2_h - m_low) / c2_h if c2_h > 0 else 0.0
                                if disp_drop >= 0.035:
                                    has_fvg = any(float(candles[d+1]['high']) < float(candles[d-1]['low']) for d in range(i+1, min(low_idx, n-1)) if d+1 < n)
                                    prev_swing_low = min(float(x['low']) for x in candles[max(0, i-15):i])
                                    body_bos = any(float(c['close']) < prev_swing_low for c in candles[i+1:low_idx+1])
                                    if has_fvg and body_bos:
                                        entry_p = round((c2_h + c2_l) / 2.0, 6)
                                        diff_pct = round((entry_p - cur_price) / cur_price * 100, 2)
                                        atr_val = atrs[min(low_idx, len(atrs)-1)]
                                        sl_p = round(c2_h + (0.35 * atr_val), 6)
                                        tp_p = round(entry_p * 0.97, 6)
                                        
                                        all_recent_obs.append({
                                            'symbol': symbol,
                                            'side': 'SHORT',
                                            'timeframe': tf,
                                            'entry_price_50mt': entry_p,
                                            'current_price': cur_price,
                                            'dist_to_entry_pct': diff_pct,
                                            'ob_range': f"{c2_l} - {c2_h}",
                                            'displacement_pct': round(disp_drop * 100, 2),
                                            'tp_price': tp_p,
                                            'sl_price': sl_p,
                                            'status': 'WAITING_FOR_RETEST' if diff_pct > 0 else 'TESTED'
                                        })
            except Exception as e:
                pass
                
    # Sort closest OBs to current price
    waiting_obs = [x for x in all_recent_obs if 0.0 <= x['dist_to_entry_pct'] <= 5.0]
    waiting_obs.sort(key=lambda x: x['dist_to_entry_pct'])
    
    # Save full results to JSON
    output_data = {
        "scan_time": datetime.now().isoformat(),
        "btc_sentry": btc_sentry,
        "triggered_count": len(triggered_setups),
        "triggered_setups": triggered_setups,
        "closest_waiting_count": len(waiting_obs),
        "closest_waiting_setups": waiting_obs[:15]
    }
    with open("live_hermes4_setups.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"DONE! Found {len(triggered_setups)} triggered setups and {len(waiting_obs)} waiting setups.")
    print("Saved to live_hermes4_setups.json")

if __name__ == '__main__':
    asyncio.run(run_scan())
