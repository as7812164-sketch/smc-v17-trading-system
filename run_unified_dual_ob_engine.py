import urllib.request
import json
import time
import sys
import numpy as np
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

APPROVED_COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "SUIUSDT", "NEARUSDT", "AVAXUSDT", "APTUSDT",
    "ARBUSDT", "OPUSDT", "LDOUSDT", "MKRUSDT", "UNIUSDT", "AAVEUSDT", "RUNEUSDT", "RENDERUSDT",
    "INJUSDT", "FETUSDT", "THETAUSDT", "ALGOUSDT", "GALAUSDT", "SANDUSDT", "FILUSDT", "ICPUSDT",
    "PYTHUSDT", "PEPEUSDT", "SHIBUSDT", "XRPUSDT", "ADAUSDT", "LINKUSDT", "DOGEUSDT"
]

def fetch_klines(sym, interval, limit=1200):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                candles = []
                for k in data:
                    candles.append({
                        "time": int(k[0]), "open": float(k[1]), "high": float(k[2]),
                        "low": float(k[3]), "close": float(k[4]), "volume": float(k[5])
                    })
                return sym, interval, candles
        except Exception:
            time.sleep(0.2)
    return sym, interval, []

def simulate_unified_dual_ob_strategy():
    tasks = []
    for s in APPROVED_COINS:
        tasks.append((s, "4h", 600))
        tasks.append((s, "1h", 1200))

    all_data = {"4h": {}, "1h": {}}
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(fetch_klines, t[0], t[1], t[2]) for t in tasks]
        for f in concurrent.futures.as_completed(futures):
            sym, tf, klines = f.result()
            if len(klines) >= 100:
                all_data[tf][sym] = klines

    all_trades = []

    for tf in ["1h", "4h"]:
        tp_pct = 0.022 if tf == "1h" else 0.025
        sl_pct = 0.025
        
        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 35):
                swing_low = candles[i]["low"]
                if swing_low != min(c["low"] for c in candles[i-15:i+1]): continue
                
                window = candles[i:min(i+16, n)]
                highs = [c["high"] for c in window]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx <= i + 3: continue
                
                total_expansion = (max_high - swing_low) / swing_low
                if total_expansion < 0.045: continue
                
                # 1. OB1 (Inducement): High_idx - 1
                idm_low = candles[high_idx - 1]["low"]
                
                # 2. OB2 (Decisional): Mid 30-70% zone with FVG
                best_mid = -1
                max_bg = 0.0
                for mid in range(i+1, high_idx):
                    bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                    fib = (candles[mid]["low"] - swing_low) / (max_high - swing_low)
                    if 0.30 <= fib <= 0.70 and bg > max_bg:
                        max_bg = bg
                        best_mid = mid
                
                dec_top, dec_bot = None, None
                if best_mid != -1:
                    dec_c = candles[best_mid - 1]
                    dec_top = max(dec_c["open"], dec_c["close"])
                    dec_bot = dec_c["low"]
                    
                # 3. OB3 (Extreme): Candle at swing_low
                ext_c = candles[i]
                ext_top = max(ext_c["open"], ext_c["close"])
                ext_bot = ext_c["low"]
                
                # Test Decisional First (Only if IDM was swept!)
                dec_trade_taken = False
                if dec_top and dec_bot:
                    # Look for tap
                    for t_idx in range(high_idx + 1, min(high_idx + 35, n)):
                        if candles[t_idx]["low"] <= dec_top:
                            tap_c = candles[t_idx]
                            # Check IDM sweep
                            swept_idm = any(candles[k]["low"] < idm_low for k in range(high_idx, t_idx + 1))
                            c_range = tap_c["high"] - tap_c["low"]
                            lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                            wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
                            mt = (dec_top + dec_bot) / 2.0
                            
                            if swept_idm and wick_ratio >= 0.18 and tap_c["close"] >= mt:
                                # Execute Decisional Scalp
                                entry_p = dec_top
                                tp_p = entry_p * (1.0 + tp_pct)
                                sl_p = entry_p * (1.0 - sl_pct)
                                
                                trade_res = None
                                exit_p = entry_p
                                for m in range(t_idx, min(t_idx + 25, n)):
                                    if candles[m]["high"] >= tp_p:
                                        trade_res = "WIN"; exit_p = tp_p; break
                                    if candles[m]["close"] <= sl_p:
                                        trade_res = "LOSS"; exit_p = sl_p; break
                                        
                                if not trade_res:
                                    fc = candles[min(t_idx + 25, n - 1)]["close"]
                                    trade_res = "WIN" if fc >= entry_p else "LOSS"
                                    exit_p = fc
                                    
                                gross = (exit_p - entry_p) / entry_p
                                all_trades.append({
                                    "sym": sym, "time": tap_c["time"], "ob_type": "DECISIONAL_SCALP",
                                    "tf": tf, "res": trade_res, "gross": gross
                                })
                                dec_trade_taken = True
                            break
                            
                # Test Extreme OB (Anchor Reversal)
                for t_idx in range(high_idx + 1, min(high_idx + 45, n)):
                    if candles[t_idx]["low"] <= ext_top:
                        tap_c = candles[t_idx]
                        c_range = tap_c["high"] - tap_c["low"]
                        lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                        wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
                        mt = (ext_top + ext_bot) / 2.0
                        
                        if wick_ratio >= 0.18 and tap_c["close"] >= mt:
                            entry_p = ext_top
                            tp_p = entry_p * (1.0 + tp_pct)
                            sl_p = entry_p * (1.0 - sl_pct)
                            
                            trade_res = None
                            exit_p = entry_p
                            for m in range(t_idx, min(t_idx + 30, n)):
                                if candles[m]["high"] >= tp_p:
                                    trade_res = "WIN"; exit_p = tp_p; break
                                if candles[m]["close"] <= sl_p:
                                    trade_res = "LOSS"; exit_p = sl_p; break
                                    
                            if not trade_res:
                                fc = candles[min(t_idx + 30, n - 1)]["close"]
                                trade_res = "WIN" if fc >= entry_p else "LOSS"
                                exit_p = fc
                                
                            gross = (exit_p - entry_p) / entry_p
                            all_trades.append({
                                "sym": sym, "time": tap_c["time"], "ob_type": "EXTREME_ANCHOR",
                                "tf": tf, "res": trade_res, "gross": gross
                            })
                        break

    all_trades.sort(key=lambda x: x["time"])
    
    # Compounding from $50
    cap = 50.0
    vault = 0.0
    wins = sum(1 for t in all_trades if t["res"] == "WIN")
    losses = len(all_trades) - wins
    wr = (wins / len(all_trades) * 100) if all_trades else 0
    
    hit_1000 = None
    max_c = 50.0
    max_dd = 0.0
    
    for idx, t in enumerate(all_trades, 1):
        pos = cap * 5.0
        net_ret = t["gross"] - 0.0014
        pnl = pos * net_ret
        if pnl > 0:
            cap += pnl * 0.85
            vault += pnl * 0.15
        else:
            cap = max(5.0, cap + pnl)
            
        tw = cap + vault
        if tw > max_c: max_c = tw
        dd = (max_c - tw) / max_c * 100.0
        if dd > max_dd: max_dd = dd
        
        if tw >= 1000.0 and hit_1000 is None:
            hit_1000 = idx

    print("=" * 85)
    print(" 🚀 UNIFIED DUAL-OB ENGINE (DECISIONAL SCALP + EXTREME ANCHOR)")
    print("=" * 85)
    print(f"Total Qualified Trades Executed:   {len(all_trades)}")
    print(f"🏆 Direct TP Wins:                 {wins} ({wr:.2f}%)")
    print(f"❌ Losses (SL Hit):                {losses} ({100 - wr:.2f}%)")
    print(f"-------------------------------------------------------------------------------------")
    print(f"Initial Starting Capital:          $50.00 USDT")
    print(f"Active Trading Balance:            ${cap:,.2f} USDT")
    print(f"Secured Profit Vault (Cold Stash): ${vault:,.2f} USDT")
    print(f"🌟 Total Net Wealth Generated:     ${cap + vault:,.2f} USDT")
    print(f"🚀 Overall Compounded ROI:         +{(((cap + vault) - 50.0) / 50.0 * 100):,.1f}%")
    print(f"🛡️ Maximum Portfolio Drawdown:     {max_dd:.2f}%")
    if hit_1000:
        print(f"🎉 $1,000 MILESTONE REACHED AT:    Trade #{hit_1000}!")
    print("=====================================================================================\n")

if __name__ == "__main__":
    simulate_unified_dual_ob_strategy()
