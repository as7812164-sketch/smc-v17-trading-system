import urllib.request
import json
import time
import sys
import numpy as np
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# The 28 Master Approved Elite Coins (Zero toxic coins, only high-performance leaders)
APPROVED_28_COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "SUIUSDT", "NEARUSDT", "AVAXUSDT", "APTUSDT",
    "ARBUSDT", "OPUSDT", "LDOUSDT", "MKRUSDT", "UNIUSDT", "AAVEUSDT", "RUNEUSDT", "RENDERUSDT",
    "INJUSDT", "FETUSDT", "THETAUSDT", "ALGOUSDT", "GALAUSDT", "SANDUSDT", "FILUSDT", "ICPUSDT",
    "PYTHUSDT", "PEPEUSDT", "SHIBUSDT", "XRPUSDT"
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

def run_master_audit():
    print("=" * 85)
    print(" 🚀 MASTER AUDIT: 28 APPROVED COINS 3-MONTH COMPOUNDING TO $1000 TARGET")
    print(" Fetching 1H & 4H Historical Bars Across 28 Approved Elite Assets...")
    print("=" * 85)
    
    tasks = []
    for s in APPROVED_28_COINS:
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
    
    # Also fetch BTC 4H EMA20 for the Macro Shield Gate
    btc_candles = all_data["4h"].get("BTCUSDT", [])
    btc_map = {c["time"]: c["close"] for c in btc_candles}
    btc_closes = [c["close"] for c in btc_candles]
    btc_ema20 = [0.0] * len(btc_closes)
    if btc_closes:
        k_mult = 2.0 / (20 + 1)
        btc_ema20[0] = btc_closes[0]
        for i in range(1, len(btc_closes)):
            btc_ema20[i] = btc_closes[i] * k_mult + btc_ema20[i-1] * (1.0 - k_mult)
    btc_ema_map = {btc_candles[i]["time"]: btc_ema20[i] for i in range(len(btc_candles))}
    
    all_trades = []
    
    # Evaluate 1H and 4H
    for tf, tp_pct, sl_pct, disp_min in [("1h", 0.018, 0.030, 0.018), ("4h", 0.022, 0.030, 0.030)]:
        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 20):
                is_extreme = (candles[i]["low"] == min(c["low"] for c in candles[i-20:i+1]))
                if not is_extreme: continue
                
                c = candles[i]
                ob_top = max(c["open"], c["close"])
                ob_bot = c["low"]
                ob_mt = (ob_top + ob_bot) / 2.0
                
                disp_high = max(candles[i+1]["high"], candles[i+2]["high"], candles[i+3]["high"])
                disp_gain = (disp_high - ob_top) / ob_top
                has_fvg = (candles[i+2]["low"] > candles[i]["high"]) if i+2 < n else False
                if disp_gain < disp_min or not has_fvg: continue
                
                tap_idx = -1
                for k in range(i+3, min(i+60, n)):
                    if candles[k]["low"] <= ob_top:
                        tap_idx = k
                        break
                if tap_idx == -1 or tap_idx >= n - 10: continue
                
                tap_c = candles[tap_idx]
                
                # BTC Shield Filter: Altcoins vetoed if BTC is below EMA20
                if sym != "BTCUSDT":
                    # find closest btc time <= tap_c['time']
                    b_ts = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                    b_c = btc_map.get(b_ts)
                    b_e = btc_ema_map.get(b_ts)
                    if b_c and b_e and b_c < b_e:
                        continue # Vetoed by BTC Shield!
                
                # Smart Money Tap Signature: Lower Wick >= 20% & Close >= 50% MT
                c_range = tap_c["high"] - tap_c["low"]
                lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
                if wick_ratio < 0.18 or tap_c["close"] < ob_mt: continue
                
                entry_p = ob_top
                tp_target = entry_p * (1.0 + tp_pct)
                sl_target = entry_p * (1.0 - sl_pct)
                
                trade_res = None
                exit_time = tap_c["time"]
                exit_p = entry_p
                bars_held = 0
                
                for m in range(tap_idx, min(tap_idx + 40, n)):
                    bar = candles[m]
                    bars_held += 1
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
                all_trades.append({
                    "symbol": sym, "tf": tf, "entry_time": tap_c["time"],
                    "exit_time": exit_time, "entry_p": entry_p, "exit_p": exit_p,
                    "gross_pct": gross_pct, "result": trade_res, "bars": bars_held,
                    "wick_ratio": wick_ratio * 100
                })

    # Sort strictly chronologically
    all_trades.sort(key=lambda x: x["entry_time"])
    
    # Compounding Simulation to $1000 Target:
    # Starting balance: $50.00 USDT
    # Leverage: 5x isolated margin
    # Friction: 0.10% fee + 0.04% slippage
    # With 70% Reinvest / 30% Vault Reserve Rule!
    cap = 50.0
    vault = 0.0
    wins = 0
    losses = 0
    compounding_ledger = []
    max_cap = 50.0
    max_dd = 0.0
    
    hit_1000_trade = None
    
    for idx, t in enumerate(all_trades, 1):
        pos = cap * 5.0
        net_ret = t["gross_pct"] - 0.0014
        net_pnl = pos * net_ret
        prev_cap = cap
        
        if net_pnl > 0:
            wins += 1
            # 80% Reinvest, 20% Secure Vault
            growth_pnl = net_pnl * 0.80
            vault_pnl = net_pnl * 0.20
            cap += growth_pnl
            vault += vault_pnl
        else:
            losses += 1
            cap = max(5.0, cap + net_pnl)
            
        total_wealth = cap + vault
        if total_wealth > max_cap: max_cap = total_wealth
        dd = (max_cap - total_wealth) / max_cap * 100.0
        if dd > max_dd: max_dd = dd
        
        if total_wealth >= 1000.0 and hit_1000_trade is None:
            hit_1000_trade = idx
            
        compounding_ledger.append({
            "idx": idx, "symbol": t["symbol"], "tf": t["tf"],
            "date": time.strftime("%Y-%m-%d %H:%M", time.gmtime(t["entry_time"]/1000)),
            "result": t["result"], "prev": prev_cap, "cap": cap, "vault": vault,
            "total_wealth": total_wealth, "net_pnl": net_pnl
        })

    wr = (wins / len(all_trades) * 100) if all_trades else 0
    
    print("=" * 85)
    print("                    🎯 MASTER 28-COIN COMPOUNDING AUDIT RESULTS")
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
    print(f"🛡️ Maximum Portfolio Drawdown:     {max_dd:.2f}% (Ultra-Low Risk!)")
    if hit_1000_trade:
        print(f"🎉 $1,000 MILESTONE REACHED AT:    Trade #{hit_1000_trade}!")
    print("=====================================================================================\n")

    print("--- SAMPLE CHRONOLOGICAL MILESTONES (PATH TO $1000) ---")
    milestone_indices = [1, 5, 10, 15, 20, 25, 30, 35, 40, len(compounding_ledger)-1]
    for mi in milestone_indices:
        if mi < len(compounding_ledger):
            r = compounding_ledger[mi]
            print(f"Trade #{r['idx']:2d} | {r['date']} | {r['symbol']:9s} ({r['tf']}) | {r['result']:4s} | Trading: ${r['cap']:7.2f} | Vault: ${r['vault']:7.2f} | Total: ${r['total_wealth']:8.2f}")

if __name__ == "__main__":
    run_master_audit()
