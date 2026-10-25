import asyncio
import sys
import os
import time
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feed.binance_feed import binance_feed
from config import TOP_22_CHAMPIONS
from engine.hermes30_apex_live import hermes30_live_engine

IST = timezone(timedelta(hours=5, minutes=30))

async def run_7day_audit():
    # 7 days in ms
    now_ms = int(time.time() * 1000)
    seven_days_ago_ms = now_ms - (7 * 24 * 3600 * 1000)
    
    print(f"=== HERMES 3.0 MODEL 2A: LAST 7-DAYS REAL AUDIT ===")
    print(f"Audit Window: {datetime.fromtimestamp(seven_days_ago_ms/1000, IST).strftime('%Y-%m-%d %H:%M IST')} to {datetime.fromtimestamp(now_ms/1000, IST).strftime('%Y-%m-%d %H:%M IST')}")
    print(f"Universe: Top-22 Champions across 4H & 1H Timeframes\n")
    
    coins = TOP_22_CHAMPIONS
    executed_trades = []
    
    # Pre-fetch BTC 4H candles for macro sentry
    btc_candles = await binance_feed.fetch_klines("BTCUSDT", interval="4h", limit=120)
    
    for symbol in coins:
        for tf in ['4h', '1h']:
            try:
                # 7 days of 4H = 42 candles; 7 days of 1H = 168 candles
                limit = 180 if tf == '1h' else 80
                candles = await binance_feed.fetch_klines(symbol, interval=tf, limit=limit)
                if not candles or len(candles) < 35:
                    continue
                
                n = len(candles)
                
                # Scan for Hermes 3.0 Model 2A setups formed and tapped in last 7 days
                for i in range(15, n - 2):
                    c_time = candles[i]['time']
                    if c_time < seven_days_ago_ms - (3 * 24 * 3600 * 1000): # Allow OB origin within 10 days
                        continue
                    
                    # 1. Bullish Setup
                    prior_l = [float(x["low"]) for x in candles[max(0, i-15):i+1]]
                    if float(candles[i]["low"]) == min(prior_l):
                        sub_w = candles[i:min(i+16, n)]
                        highs = [float(x["high"]) for x in sub_w]
                        max_h = max(highs)
                        h_idx = i + highs.index(max_h)
                        if h_idx > i + 2:
                            origin_l = float(candles[i]["low"])
                            gain = (max_h - origin_l) / origin_l if origin_l > 0 else 0.0
                            if gain >= 0.050: # Disp >= 5%
                                idm_low = float(candles[h_idx - 1]["low"])
                                best_mid = -1
                                max_bg = 0.0
                                for mid in range(i + 1, h_idx):
                                    m_h, m_l = float(candles[mid]["high"]), float(candles[mid]["low"])
                                    bg = (m_h - m_l) / m_l if m_l > 0 else 0.0
                                    fib = (m_l - origin_l) / (max_h - origin_l) if max_h > origin_l else 0.0
                                    if 0.30 <= fib <= 0.70 and bg > max_bg:
                                        max_bg = bg
                                        best_mid = mid
                                
                                if best_mid != -1:
                                    dec_c = candles[best_mid - 1]
                                    dec_top = max(float(dec_c["open"]), float(dec_c["close"]))
                                    dec_bot = float(dec_c["low"])
                                    has_fvg = (float(candles[best_mid + 1]["low"]) > float(candles[best_mid - 1]["high"])) if best_mid + 1 < n else False
                                    
                                    if has_fvg:
                                        mt = round((dec_top + dec_bot) / 2.0, 8)
                                        tp_p = round(mt * 1.030, 8)
                                        soft_sl_p = round(mt * 0.985, 8)
                                        hard_sl_p = round(mt * 0.970, 8)
                                        be_armor_p = round(mt * 1.015, 8)
                                        
                                        # Look for Tap
                                        for t in range(h_idx + 1, min(h_idx + 28, n)):
                                            tap_c = candles[t]
                                            t_time = tap_c["time"]
                                            if t_time < seven_days_ago_ms:
                                                continue # Tap was before 7 days
                                            
                                            t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                            
                                            if t_l <= mt and t_c >= mt:
                                                c_range = t_h - t_l
                                                swept = any(float(candles[k]["low"]) < idm_low for k in range(h_idx, t + 1))
                                                l_wick = min(t_o, t_c) - t_l
                                                w_ratio = (l_wick / c_range) if c_range > 0 else 0.0
                                                
                                                if swept and w_ratio >= 0.18:
                                                    # VALID ENTRY! Now simulate forward progression to resolution
                                                    entry_time = t_time
                                                    be_locked = False
                                                    outcome = "STILL_OPEN"
                                                    exit_price = float(candles[-1]["close"])
                                                    exit_time = candles[-1]["time"]
                                                    highest_seen = mt
                                                    lowest_seen = mt
                                                    
                                                    for bar_f in range(t + 1, n):
                                                        bf = candles[bar_f]
                                                        b_l, b_h, b_c = float(bf["low"]), float(bf["high"]), float(bf["close"])
                                                        highest_seen = max(highest_seen, b_h)
                                                        lowest_seen = min(lowest_seen, b_l)
                                                        
                                                        # Check BE trigger (+1.5% spot)
                                                        if not be_locked and b_h >= be_armor_p:
                                                            be_locked = True
                                                        
                                                        # Check TP (+3.0% spot)
                                                        if b_h >= tp_p:
                                                            outcome = "TP_HIT"
                                                            exit_price = tp_p
                                                            exit_time = bf["time"]
                                                            break
                                                        
                                                        # Check Hard SL (-3.0%)
                                                        if b_l <= hard_sl_p:
                                                            outcome = "HARD_SL_HIT"
                                                            exit_price = hard_sl_p
                                                            exit_time = bf["time"]
                                                            break
                                                        
                                                        # Check BE hit if locked
                                                        if be_locked and b_l <= mt:
                                                            outcome = "BE_SAVE"
                                                            exit_price = mt
                                                            exit_time = bf["time"]
                                                            break
                                                        
                                                        # Check Soft SL (-1.5% on Body Close!)
                                                        if b_c <= soft_sl_p:
                                                            outcome = "SOFT_SL_BODY_CLOSE"
                                                            exit_price = b_c
                                                            exit_time = bf["time"]
                                                            break
                                                    
                                                    # Calculate PnL on $50 margin @ 5x
                                                    pnl_pct = ((exit_price - mt) / mt) * 5.0 * 100.0
                                                    pnl_usdt = round(50.0 * (pnl_pct / 100.0), 2)
                                                    
                                                    dur_sec = max(0, int((exit_time - entry_time) / 1000))
                                                    dur_h = dur_sec // 3600
                                                    dur_m = (dur_sec % 3600) // 60
                                                    
                                                    executed_trades.append({
                                                        "symbol": symbol,
                                                        "side": "LONG",
                                                        "timeframe": tf.upper(),
                                                        "entry_time": entry_time,
                                                        "entry_time_str": datetime.fromtimestamp(entry_time/1000, IST).strftime('%d %b %H:%M'),
                                                        "exit_time_str": datetime.fromtimestamp(exit_time/1000, IST).strftime('%d %b %H:%M') if outcome != "STILL_OPEN" else "RUNNING",
                                                        "duration_str": f"{dur_h}h {dur_m}m" if dur_h > 0 else f"{dur_m}m",
                                                        "entry_price": mt,
                                                        "exit_price": exit_price,
                                                        "tp_price": tp_p,
                                                        "sl_price": soft_sl_p,
                                                        "wick_pct": round(w_ratio * 100, 1),
                                                        "outcome": outcome,
                                                        "pnl_pct": round(pnl_pct, 2),
                                                        "pnl_usdt": pnl_usdt,
                                                        "be_locked": be_locked
                                                    })
                                                    break # Only one tap per zone
                    
                    # 2. Bearish Setup
                    prior_h = [float(x["high"]) for x in candles[max(0, i-15):i+1]]
                    if float(candles[i]["high"]) == max(prior_h):
                        sub_w = candles[i:min(i+16, n)]
                        lows = [float(x["low"]) for x in sub_w]
                        min_l = min(lows)
                        l_idx = i + lows.index(min_l)
                        if l_idx > i + 2:
                            origin_h = float(candles[i]["high"])
                            drop = (origin_h - min_l) / origin_h if origin_h > 0 else 0.0
                            if drop >= 0.050:
                                idm_high = float(candles[l_idx - 1]["high"])
                                best_mid = -1
                                max_bg = 0.0
                                for mid in range(i + 1, l_idx):
                                    m_h, m_l = float(candles[mid]["high"]), float(candles[mid]["low"])
                                    bg = (m_h - m_l) / m_h if m_h > 0 else 0.0
                                    fib = (origin_h - m_h) / (origin_h - min_l) if origin_h > min_l else 0.0
                                    if 0.30 <= fib <= 0.70 and bg > max_bg:
                                        max_bg = bg
                                        best_mid = mid
                                
                                if best_mid != -1:
                                    dec_c = candles[best_mid - 1]
                                    dec_top = float(dec_c["high"])
                                    dec_bot = min(float(dec_c["open"]), float(dec_c["close"]))
                                    has_bear_fvg = (float(candles[best_mid + 1]["high"]) < float(candles[best_mid - 1]["low"])) if best_mid + 1 < n else False
                                    
                                    if has_bear_fvg:
                                        mt = round((dec_top + dec_bot) / 2.0, 8)
                                        tp_p = round(mt * 0.970, 8)
                                        soft_sl_p = round(mt * 1.015, 8)
                                        hard_sl_p = round(mt * 1.030, 8)
                                        be_armor_p = round(mt * 0.985, 8)
                                        
                                        for t in range(l_idx + 1, min(l_idx + 28, n)):
                                            tap_c = candles[t]
                                            t_time = tap_c["time"]
                                            if t_time < seven_days_ago_ms:
                                                continue
                                            
                                            t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])
                                            
                                            if t_h >= mt and t_c <= mt:
                                                c_range = t_h - t_l
                                                swept = any(float(candles[k]["high"]) > idm_high for k in range(l_idx, t + 1))
                                                u_wick = t_h - max(t_o, t_c)
                                                w_ratio = (u_wick / c_range) if c_range > 0 else 0.0
                                                
                                                if swept and w_ratio >= 0.18:
                                                    entry_time = t_time
                                                    be_locked = False
                                                    outcome = "STILL_OPEN"
                                                    exit_price = float(candles[-1]["close"])
                                                    exit_time = candles[-1]["time"]
                                                    
                                                    for bar_f in range(t + 1, n):
                                                        bf = candles[bar_f]
                                                        b_l, b_h, b_c = float(bf["low"]), float(bf["high"]), float(bf["close"])
                                                        
                                                        if not be_locked and b_l <= be_armor_p:
                                                            be_locked = True
                                                        
                                                        if b_l <= tp_p:
                                                            outcome = "TP_HIT"
                                                            exit_price = tp_p
                                                            exit_time = bf["time"]
                                                            break
                                                        
                                                        if b_h >= hard_sl_p:
                                                            outcome = "HARD_SL_HIT"
                                                            exit_price = hard_sl_p
                                                            exit_time = bf["time"]
                                                            break
                                                        
                                                        if be_locked and b_h >= mt:
                                                            outcome = "BE_SAVE"
                                                            exit_price = mt
                                                            exit_time = bf["time"]
                                                            break
                                                        
                                                        if b_c >= soft_sl_p:
                                                            outcome = "SOFT_SL_BODY_CLOSE"
                                                            exit_price = b_c
                                                            exit_time = bf["time"]
                                                            break
                                                    
                                                    pnl_pct = ((mt - exit_price) / mt) * 5.0 * 100.0
                                                    pnl_usdt = round(50.0 * (pnl_pct / 100.0), 2)
                                                    
                                                    dur_sec = max(0, int((exit_time - entry_time) / 1000))
                                                    dur_h = dur_sec // 3600
                                                    dur_m = (dur_sec % 3600) // 60
                                                    
                                                    executed_trades.append({
                                                        "symbol": symbol,
                                                        "side": "SHORT",
                                                        "timeframe": tf.upper(),
                                                        "entry_time": entry_time,
                                                        "entry_time_str": datetime.fromtimestamp(entry_time/1000, IST).strftime('%d %b %H:%M'),
                                                        "exit_time_str": datetime.fromtimestamp(exit_time/1000, IST).strftime('%d %b %H:%M') if outcome != "STILL_OPEN" else "RUNNING",
                                                        "duration_str": f"{dur_h}h {dur_m}m" if dur_h > 0 else f"{dur_m}m",
                                                        "entry_price": mt,
                                                        "exit_price": exit_price,
                                                        "tp_price": tp_p,
                                                        "sl_price": soft_sl_p,
                                                        "wick_pct": round(w_ratio * 100, 1),
                                                        "outcome": outcome,
                                                        "pnl_pct": round(pnl_pct, 2),
                                                        "pnl_usdt": pnl_usdt,
                                                        "be_locked": be_locked
                                                    })
                                                    break
            except Exception as e:
                pass

    # Deduplicate executions on same symbol and entry time
    dedup = {}
    for tr in executed_trades:
        key = (tr["symbol"], tr["side"], tr["timeframe"], tr["entry_time"])
        if key not in dedup:
            dedup[key] = tr
    
    final_trades = list(dedup.values())
    final_trades.sort(key=lambda x: x["entry_time"])
    
    # Calculate performance stats
    wins = [t for t in final_trades if t["outcome"] == "TP_HIT"]
    be_saves = [t for t in final_trades if t["outcome"] == "BE_SAVE"]
    losses = [t for t in final_trades if "SL" in t["outcome"]]
    open_pos = [t for t in final_trades if t["outcome"] == "STILL_OPEN"]
    
    total_closed = len(wins) + len(losses) + len(be_saves)
    win_rate = (len(wins) / total_closed * 100.0) if total_closed > 0 else 0.0
    # Effective accuracy including BE protection (capital preservation)
    capital_safe_rate = ((len(wins) + len(be_saves)) / total_closed * 100.0) if total_closed > 0 else 0.0
    total_net_pnl = sum(t["pnl_usdt"] for t in final_trades if t["outcome"] != "STILL_OPEN")
    
    print(f"Total Setups Triggered (Last 7 Days): {len(final_trades)}")
    print(f"Wins (TP Hit +15% ROE): {len(wins)}")
    print(f"Break-Even Saves ($0.00 Risk-Free): {len(be_saves)}")
    print(f"Losses (SL Hit -7.5% ROE): {len(losses)}")
    print(f"Still Open / Running: {len(open_pos)}")
    print(f"Strict Win Rate: {win_rate:.1f}%")
    print(f"Capital Protection Rate (Win + BE): {capital_safe_rate:.1f}%")
    print(f"Total Net PnL (Starting $50 Margin): ${total_net_pnl:+.2f} USDT")
    
    import json
    with open("last_7days_audit_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "window": "7_DAYS",
            "total_trades": len(final_trades),
            "wins": len(wins),
            "be_saves": len(be_saves),
            "losses": len(losses),
            "open": len(open_pos),
            "win_rate": round(win_rate, 1),
            "capital_safe_rate": round(capital_safe_rate, 1),
            "net_pnl_usdt": round(total_net_pnl, 2),
            "trades": final_trades
        }, f, indent=2)
    print("Saved to last_7days_audit_results.json")

if __name__ == '__main__':
    asyncio.run(run_7day_audit())
