import urllib.request
import json
import time
import sys
import numpy as np
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

COINS_40 = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "SUIUSDT", "AVAXUSDT", "NEARUSDT", "BNBUSDT", "DOGEUSDT",
    "XRPUSDT", "ADAUSDT", "LINKUSDT", "DOTUSDT", "LTCUSDT", "BCHUSDT", "APTUSDT", "ARBUSDT",
    "OPUSDT", "INJUSDT", "TIAUSDT", "SEIUSDT", "FETUSDT", "RUNEUSDT", "FILUSDT", "ICPUSDT",
    "PEPEUSDT", "SHIBUSDT", "WIFUSDT", "RENDERUSDT", "STXUSDT", "GALAUSDT", "FTMUSDT",
    "AAVEUSDT", "UNIUSDT", "CRVUSDT", "MKRUSDT", "LDOUSDT", "ATOMUSDT", "THETAUSDT",
    "ALGOUSDT", "KASUSDT"
]

def fetch_klines(sym, interval, limit=550):
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

def run_experiment():
    print("=" * 85)
    print(" 🔬 EXPERIMENT RUNNER: 3-MONTH 1H & 4H COMPOUNDING & FORENSIC DISCOVERY")
    print(" Locked Targets: 1H (TP +1.8%, SL -3.0%) | 4H (TP +2.2%, SL -3.0%) @ 5x Leverage")
    print("=" * 85)
    
    tasks = []
    # 4H data (~550 bars) and 1H data (~1200 bars)
    for s in COINS_40:
        tasks.append((s, "4h", 550))
        tasks.append((s, "1h", 1200))
        
    all_data = {"4h": {}, "1h": {}}
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(fetch_klines, t[0], t[1], t[2]) for t in tasks]
        for f in concurrent.futures.as_completed(futures):
            sym, tf, klines = f.result()
            if len(klines) >= 100:
                all_data[tf][sym] = klines

    print(f"Loaded {len(all_data['4h'])} pairs for 4H and {len(all_data['1h'])} pairs for 1H.\n")
    
    trades_1h = []
    trades_4h = []
    
    # Process both timeframes with locked parameters
    for tf, tp_pct, sl_pct, disp_min in [("1h", 0.018, 0.030, 0.018), ("4h", 0.022, 0.030, 0.030)]:
        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 20):
                # Extreme swing low of 20-bar window
                is_extreme = (candles[i]["low"] == min(c["low"] for c in candles[i-20:i+1]))
                if not is_extreme: continue
                
                c = candles[i]
                ob_top = max(c["open"], c["close"])
                ob_bot = c["low"]
                ob_mt = (ob_top + ob_bot) / 2.0
                
                # Displacement check with FVG
                disp_high = max(candles[i+1]["high"], candles[i+2]["high"], candles[i+3]["high"])
                disp_gain = (disp_high - ob_top) / ob_top
                has_fvg = (candles[i+2]["low"] > candles[i]["high"]) if i+2 < n else False
                if disp_gain < disp_min or not has_fvg: continue
                
                # Retest search
                tap_idx = -1
                for k in range(i+3, min(i+60, n)):
                    if candles[k]["low"] <= ob_top:
                        tap_idx = k
                        break
                if tap_idx == -1 or tap_idx >= n - 10: continue
                
                tap_c = candles[tap_idx]
                c_range = tap_c["high"] - tap_c["low"]
                lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
                
                # Smart Money Tap Filter
                if wick_ratio < 0.18 or tap_c["close"] < ob_mt:
                    continue
                    
                entry_p = ob_top
                tp_target = entry_p * (1.0 + tp_pct)
                sl_target = entry_p * (1.0 - sl_pct) # Strict 3.0% SL (15% ROE @ 5x)
                
                trade_res = None
                exit_time = tap_c["time"]
                exit_p = entry_p
                bars_held = 0
                max_favorable = 0.0
                
                for m in range(tap_idx, min(tap_idx + 40, n)):
                    bar = candles[m]
                    bars_held += 1
                    fav = (bar["high"] - entry_p) / entry_p
                    if fav > max_favorable: max_favorable = fav
                    
                    if bar["high"] >= tp_target:
                        trade_res = "WIN"
                        exit_p = tp_target
                        exit_time = bar["time"]
                        break
                    if bar["close"] <= sl_target:
                        trade_res = "LOSS"
                        exit_p = sl_target
                        exit_time = bar["time"]
                        break
                        
                if not trade_res:
                    final_close = candles[min(tap_idx + 40, n - 1)]["close"]
                    exit_p = final_close
                    exit_time = candles[min(tap_idx + 40, n - 1)]["time"]
                    trade_res = "WIN" if final_close >= entry_p else "LOSS"
                    
                gross_pct = (exit_p - entry_p) / entry_p
                rec = {
                    "symbol": sym, "tf": tf, "entry_time": tap_c["time"],
                    "exit_time": exit_time, "entry_p": entry_p, "exit_p": exit_p,
                    "gross_pct": gross_pct, "result": trade_res, "bars": bars_held,
                    "max_favorable": max_favorable * 100, "wick_ratio": wick_ratio * 100
                }
                
                if tf == "1h": trades_1h.append(rec)
                else: trades_4h.append(rec)
                
    # Sort chronologically
    trades_1h.sort(key=lambda x: x["entry_time"])
    trades_4h.sort(key=lambda x: x["entry_time"])
    all_combined = sorted(trades_1h + trades_4h, key=lambda x: x["entry_time"])
    
    # Run Compounding Simulation for:
    # 1. 1H standalone ($50 starting)
    # 2. 4H standalone ($50 starting)
    # 3. Combined Portfolio ($50 starting)
    def simulate_compounding(trades, label):
        cap = 50.0
        max_cap = 50.0
        max_dd = 0.0
        wins = 0
        losses = 0
        ledger = []
        friction = 0.0014 # 0.10% fee + 0.04% slippage
        
        for idx, t in enumerate(trades, 1):
            pos = cap * 5.0
            net_ret = t["gross_pct"] - friction
            pnl = pos * net_ret
            prev = cap
            cap = max(1.0, cap + pnl)
            if cap > max_cap: max_cap = cap
            dd = (max_cap - cap) / max_cap * 100.0
            if dd > max_dd: max_dd = dd
            if t["result"] == "WIN": wins += 1
            else: losses += 1
            ledger.append({
                "num": idx, "symbol": t["symbol"], "tf": t["tf"],
                "date": time.strftime("%Y-%m-%d %H:%M", time.gmtime(t["entry_time"]/1000)),
                "result": t["result"], "prev": prev, "cap": cap, "net_pnl": pnl
            })
            
        wr = (wins / len(trades) * 100) if trades else 0
        print(f"\n=====================================================================================")
        print(f" 📊 {label.upper()} AUDIT RESULTS (3 MONTHS / 40 COINS)")
        print(f"=====================================================================================")
        print(f"  • Total Executed Trades:       {len(trades)}")
        print(f"  • 🏆 Direct TP Wins:           {wins} ({wr:.2f}%)")
        print(f"  • ❌ Losses:                   {losses} ({100 - wr:.2f}%)")
        print(f"  • 📈 Initial Capital:          $50.00 USDT")
        print(f"  • 🚀 Final Compounded Balance: ${cap:,.2f} USDT")
        print(f"  • 💎 Net Account ROI:          +{((cap - 50.0)/50.0*100):,.1f}%")
        print(f"  • 🛡️ Maximum Drawdown:         {max_dd:.2f}%")
        
        return cap, wr, len(trades), ledger
        
    cap_1h, wr_1h, count_1h, _ = simulate_compounding(trades_1h, "1-Hour (1H) Standalone System")
    cap_4h, wr_4h, count_4h, _ = simulate_compounding(trades_4h, "4-Hour (4H) Standalone System")
    cap_comb, wr_comb, count_comb, ledger_comb = simulate_compounding(all_combined, "Combined Master System (1H + 4H Synchronized)")
    
    # Deep Hidden Pattern Autopsy:
    print("\n" + "=" * 85)
    print(" 🕵️ DEEP FORENSIC AUTOPSY: WHAT HIDDEN PATTERN MAKES THE BEST BOUNCE?")
    print("=" * 85)
    
    # 1. Wick size correlation with win rate
    high_wick_trades = [t for t in all_combined if t["wick_ratio"] >= 35.0]
    normal_wick_trades = [t for t in all_combined if t["wick_ratio"] < 35.0]
    hw_wr = (sum(1 for t in high_wick_trades if t["result"] == "WIN") / len(high_wick_trades) * 100) if high_wick_trades else 0
    nw_wr = (sum(1 for t in normal_wick_trades if t["result"] == "WIN") / len(normal_wick_trades) * 100) if normal_wick_trades else 0
    
    print(f"• Hidden Factor 1 (Wick Quality):")
    print(f"  - When Lower Wick >= 35%: Win Rate is {hw_wr:.1f}% ({len(high_wick_trades)} trades)")
    print(f"  - When Lower Wick < 35%:  Win Rate is {nw_wr:.1f}% ({len(normal_wick_trades)} trades)")
    
    # 2. Coin category performance
    tier1_syms = {"BTCUSDT", "ETHUSDT", "SOLUSDT", "NEARUSDT", "SUIUSDT", "AVAXUSDT", "BNBUSDT", "LDOUSDT", "MKRUSDT", "ARB"}
    tier1_trades = [t for t in all_combined if t["symbol"] in tier1_syms]
    t1_wr = (sum(1 for t in tier1_trades if t["result"] == "WIN") / len(tier1_trades) * 100) if tier1_trades else 0
    print(f"\n• Hidden Factor 2 (Asset Liquidity Tier):")
    print(f"  - Tier-1 High-Liquidity Coins: Win Rate is {t1_wr:.1f}% ({len(tier1_trades)} trades)")
    
    print("\n" + "=" * 85)
    print(" Chronological Compounding Snapshot (Last 10 Trades):")
    for l in ledger_comb[-10:]:
        print(f"  Trade #{l['num']:2d} | {l['date']} | {l['symbol']:9s} ({l['tf']}) | {l['result']:4s} | ${l['prev']:8.2f} ➔ ${l['cap']:8.2f}")
    print("=====================================================================================\n")

if __name__ == "__main__":
    run_experiment()
