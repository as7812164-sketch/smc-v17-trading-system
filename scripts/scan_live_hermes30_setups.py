import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feed.binance_feed import binance_feed
from config import TOP_22_CHAMPIONS, ALL_MONITORED_COINS
from engine.hermes30_apex_live import hermes30_live_engine
from database.db import get_open_paper_trades

IST = timezone(timedelta(hours=5, minutes=30))

async def main():
    coins = TOP_22_CHAMPIONS
    print(f"=== HERMES 3.0 MODEL 2A LIVE RADAR SCAN ===")
    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # 1. Check open trades
    open_trades = get_open_paper_trades()
    print(f"\n[CURRENT ACTIVE POSITIONS]: {len(open_trades)}")
    for ot in open_trades:
        print(f"  • #{ot.get('id')} {ot.get('symbol')} ({ot.get('side')}) {ot.get('timeframe')} | Entry: {ot.get('entry_price')} | Cur: {ot.get('mark_price')} | PnL: {ot.get('pnl_usdt')} USDT ({ot.get('pnl_pct')}%) | BE Locked: {ot.get('be_locked')}")

    # 2. BTC Macro Sentry
    btc_sentry = await hermes30_live_engine.evaluate_btc_macro_sentry()
    print(f"\n[SENTRY 1: BTC MACRO CAUSAL BRAKE]:")
    print(f"  Bias: {btc_sentry.get('bias')} | 4H Move: {btc_sentry.get('change_pct')}% | Long Veto: {btc_sentry.get('long_veto')} | Short Veto: {btc_sentry.get('short_veto')}")

    # 3. Scan all Top-22 coins on 4H and 1H
    all_setups = []
    approaching_obs = []
    
    for symbol in coins:
        for tf in ['4h', '1h']:
            try:
                candles = await binance_feed.fetch_klines(symbol, interval=tf, limit=80)
                if not candles or len(candles) < 40:
                    continue
                cur_price = float(candles[-1]['close'])
                
                # Check apex setups
                detected = hermes30_live_engine.detect_apex_setups_on_candles(symbol, candles, tf, btc_sentry)
                for s in detected:
                    dist = round((cur_price - s['entry_price']) / cur_price * 100.0, 2)
                    s['current_price'] = cur_price
                    s['dist_to_entry_pct'] = dist
                    all_setups.append(s)
                
                # Also inspect developing Order Blocks (where displacement >= 5.0% + FVG exist, but awaiting tap or within 3% of MT)
                n = len(candles)
                for i in range(20, n - 2):
                    # Check Bullish OB
                    prior_l = [float(x["low"]) for x in candles[max(0, i-15):i+1]]
                    if float(candles[i]["low"]) == min(prior_l):
                        sub_w = candles[i:min(i+16, n)]
                        highs = [float(x["high"]) for x in sub_w]
                        max_h = max(highs)
                        h_idx = i + highs.index(max_h)
                        if h_idx > i + 2:
                            origin_l = float(candles[i]["low"])
                            gain = (max_h - origin_l) / origin_l if origin_l > 0 else 0.0
                            if gain >= 0.050:
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
                                        mt = round((dec_top + dec_bot) / 2.0, 6)
                                        # Distance from current price to MT
                                        diff_pct = round((cur_price - mt) / cur_price * 100.0, 2)
                                        bars_since = (n - 1) - h_idx
                                        if 0.0 < diff_pct <= 5.0 and bars_since <= 28:
                                            approaching_obs.append({
                                                "symbol": symbol,
                                                "side": "LONG",
                                                "timeframe": tf,
                                                "cur_price": cur_price,
                                                "mt_entry": mt,
                                                "dist_to_entry_pct": diff_pct,
                                                "displacement_pct": round(gain * 100, 2),
                                                "ob_range": f"{dec_bot} - {dec_top}",
                                                "bars_since_wave": bars_since
                                            })
                    
                    # Check Bearish OB
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
                                    has_fvg = (float(candles[best_mid + 1]["high"]) < float(candles[best_mid - 1]["low"])) if best_mid + 1 < n else False
                                    if has_fvg:
                                        mt = round((dec_top + dec_bot) / 2.0, 6)
                                        diff_pct = round((mt - cur_price) / cur_price * 100.0, 2)
                                        bars_since = (n - 1) - l_idx
                                        if 0.0 < diff_pct <= 5.0 and bars_since <= 28:
                                            approaching_obs.append({
                                                "symbol": symbol,
                                                "side": "SHORT",
                                                "timeframe": tf,
                                                "cur_price": cur_price,
                                                "mt_entry": mt,
                                                "dist_to_entry_pct": diff_pct,
                                                "displacement_pct": round(drop * 100, 2),
                                                "ob_range": f"{dec_bot} - {dec_top}",
                                                "bars_since_wave": bars_since
                                            })

            except Exception as e:
                # ignore network error on individual coin
                pass

    print(f"\n[CONFIRMED / TRIGGERED SETUPS (TAP COMPLETED)]: {len(all_setups)}")
    for s in all_setups:
        print(f"  [*] {s['symbol']} {s['side']} ({s['interval']}) | Entry (50% MT): {s['entry_price']} | Cur: {s['current_price']} | Dist: {s['dist_to_entry_pct']}% | Wick: {s['wick_ratio_pct']}% | Age: {s['tap_bar_age']} bars | Status: {s['status']}")

    print(f"\n[DEVELOPING SETUPS (APPROACHING 50% MT <= 5.0% DISTANCE)]: {len(approaching_obs)}")
    approaching_obs.sort(key=lambda x: x['dist_to_entry_pct'])
    for a in approaching_obs[:15]:
        print(f"  [>] {a['symbol']} {a['side']} ({a['timeframe']}) | Cur: {a['cur_price']} -> Entry MT: {a['mt_entry']} | Distance: {a['dist_to_entry_pct']}% | Disp: {a['displacement_pct']}% | Age: {a['bars_since_wave']} bars | Zone: {a['ob_range']}")

    with open('live_hermes30_scan_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'time': datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST'),
            'btc_sentry': btc_sentry,
            'confirmed_setups': all_setups,
            'approaching_setups': approaching_obs
        }, f, indent=2)
    print("\nScan results saved to live_hermes30_scan_results.json")

if __name__ == '__main__':
    asyncio.run(main())
