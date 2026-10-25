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

def run_3_obs_deep_audit():
    print("=" * 90)
    print(" 🎯 3-OB EXPERIMENT: EXTREME vs DECISIONAL vs INDUCEMENT (DEEP FORENSIC AUDIT)")
    print(" Testing: Win Rate, Quick 2.0% - 2.5% TP Hit Rate, Stop Loss Variations")
    print("=" * 90)

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

    # Compare SL variations for Quick 2.0% / 2.5% TP:
    # SL 1: Structural SL (0.3% below OB bottom)
    # SL 2: Fixed Soft SL 1.8% (9% ROE at 5x)
    # SL 3: Fixed Soft SL 2.5% (12.5% ROE at 5x)
    
    sl_configs = [
        {"name": "Structural SL (0.3% Below OB Bottom)", "type": "structural"},
        {"name": "Tight Soft SL (1.8% Move = 9% ROE)", "type": "fixed", "val": 0.018},
        {"name": "Balanced Soft SL (2.5% Move = 12.5% ROE)", "type": "fixed", "val": 0.025}
    ]

    for sl_cfg in sl_configs:
        print(f"\n>>> TESTING STOP LOSS MODEL: [{sl_cfg['name']}] <<<")
        
        for ob_target in ["EXTREME", "DECISIONAL", "SHALLOW_INDUCEMENT"]:
            trades = []
            
            for tf in ["1h", "4h"]:
                tp_pct = 0.022 if tf == "1h" else 0.025 # 2.2% on 1H, 2.5% on 4H
                
                for sym, candles in all_data[tf].items():
                    n = len(candles)
                    for i in range(25, n - 35):
                        swing_low = candles[i]["low"]
                        if swing_low != min(c["low"] for c in candles[i-15:i+1]):
                            continue
                            
                        window = candles[i:min(i+16, n)]
                        highs = [c["high"] for c in window]
                        max_high = max(highs)
                        high_idx = i + highs.index(max_high)
                        if high_idx <= i + 3: continue
                        
                        total_expansion = (max_high - swing_low) / swing_low
                        if total_expansion < 0.045: continue
                        
                        # Identify candidate OB based on ob_target
                        ob_top, ob_bot = None, None
                        
                        if ob_target == "EXTREME":
                            c = candles[i]
                            ob_top = max(c["open"], c["close"])
                            ob_bot = c["low"]
                        elif ob_target == "DECISIONAL":
                            # Find largest candle in 30%-70% of the leg
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - swing_low) / (max_high - swing_low)
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                            if best_mid != -1:
                                c = candles[best_mid - 1]
                                ob_top = max(c["open"], c["close"])
                                ob_bot = c["low"]
                        elif ob_target == "SHALLOW_INDUCEMENT":
                            c = candles[high_idx - 1]
                            ob_top = max(c["open"], c["close"])
                            ob_bot = c["low"]
                            
                        if not ob_top or not ob_bot: continue
                        
                        # Find first tap after high_idx
                        tap_idx = -1
                        for t_idx in range(high_idx + 1, min(high_idx + 45, n)):
                            if candles[t_idx]["low"] <= ob_top:
                                tap_idx = t_idx
                                break
                        if tap_idx == -1 or tap_idx >= n - 10: continue
                        
                        tap_c = candles[tap_idx]
                        c_range = tap_c["high"] - tap_c["low"]
                        lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                        wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
                        mt = (ob_top + ob_bot) / 2.0
                        
                        # Apply smart money confirmation: Wick absorption >= 18% & close >= MT
                        if wick_ratio < 0.18 or tap_c["close"] < mt:
                            continue
                            
                        entry_p = ob_top
                        tp_p = entry_p * (1.0 + tp_pct)
                        
                        if sl_cfg["type"] == "structural":
                            sl_p = ob_bot * 0.997 # 0.3% below OB bottom
                        else:
                            sl_p = entry_p * (1.0 - sl_cfg["val"])
                            
                        trade_res = None
                        exit_p = entry_p
                        exit_time = tap_c["time"]
                        bars = 0
                        
                        for m in range(tap_idx, min(tap_idx + 30, n)):
                            bar = candles[m]
                            bars += 1
                            if bar["high"] >= tp_p:
                                trade_res = "WIN"
                                exit_p = tp_p
                                exit_time = bar["time"]
                                break
                            if bar["close"] <= sl_p:
                                trade_res = "LOSS"
                                exit_p = sl_p
                                exit_time = bar["time"]
                                break
                                
                        if not trade_res:
                            fc = candles[min(tap_idx + 30, n - 1)]["close"]
                            exit_p = fc
                            exit_time = candles[min(tap_idx + 30, n - 1)]["time"]
                            trade_res = "WIN" if fc >= entry_p else "LOSS"
                            
                        gross_pct = (exit_p - entry_p) / entry_p
                        trades.append({
                            "sym": sym, "time": tap_c["time"], "result": trade_res,
                            "gross_pct": gross_pct, "bars": bars
                        })
                        
            trades.sort(key=lambda x: x["time"])
            tot = len(trades)
            wins = sum(1 for t in trades if t["result"] == "WIN")
            losses = tot - wins
            wr = (wins / tot * 100) if tot else 0
            avg_bars = np.mean([t["bars"] for t in trades]) if trades else 0
            
            # Compounding from $50 with 85% trade / 15% vault
            cap = 50.0
            vault = 0.0
            for t in trades:
                pos = cap * 5.0
                net_ret = t["gross_pct"] - 0.0014
                pnl = pos * net_ret
                if pnl > 0:
                    cap += pnl * 0.85
                    vault += pnl * 0.15
                else:
                    cap = max(5.0, cap + pnl)
                    
            print(f"  [{ob_target:18s}]: {tot:3d} Trades | {wins:3d} Wins ({wr:5.1f}%) | Avg Duration: {avg_bars:4.1f} bars | Final: ${cap+vault:,.2f} USDT")

if __name__ == "__main__":
    run_3_obs_deep_audit()
