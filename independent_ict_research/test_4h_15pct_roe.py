import os, sys, json
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

BASE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
DATA_DIR = os.path.join(BASE_DIR, "historical_data")

def load_candles(sym, tf):
    fpath = os.path.join(DATA_DIR, f"{sym}_{tf}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f: return json.load(f)

def calculate_atr(candles, period=14):
    if not candles: return []
    atrs = [max(candles[0]["high"] - candles[0]["low"], 1e-6)]
    for i in range(1, len(candles)):
        curr, prev = candles[i], candles[i-1]
        tr = max(curr["high"] - curr.get("low", curr["high"]), abs(curr["high"] - prev["close"]), abs(curr["low"] - prev["close"]))
        atrs.append((atrs[-1] * (period - 1) + tr) / period)
    return atrs

all_data = {"1h": {}, "4h": {}}
for sym in TOP_22_CHAMPIONS:
    for tf in ["1h", "4h"]:
        c = load_candles(sym, tf)
        if len(c) >= 500: all_data[tf][sym] = c

btc_map = {
    "1h": {c["time"]: c for c in all_data["1h"].get("BTCUSDT", [])},
    "4h": {c["time"]: c for c in all_data["4h"].get("BTCUSDT", [])}
}

def run_test(timeframes=["4h"], allow_of_entry=True):
    trades = []
    target_spot_tp = 0.0300  # +3.00% spot = +15.0% ROE at 5x
    target_spot_sl = 0.0150  # -1.50% spot = -7.50% ROE at 5x (1:2 R:R)
    
    for tf in timeframes:
        max_hold = 36
        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 60: continue
            atrs = calculate_atr(candles, 14)
            for i in range(25, n - 35):
                # Bullish
                c1, c2 = candles[i-1], candles[i]
                if c2["close"] <= c2["open"] and c2["low"] < c1["low"] and c2["low"] == min(c["low"] for c in candles[max(0, i-12):i+1]):
                    sub_w = candles[i:min(i+18, n)]
                    highs = [c["high"] for c in sub_w]
                    m_high = max(highs)
                    h_idx = i + highs.index(m_high)
                    if h_idx > i + 2:
                        gain = (m_high - c2["low"]) / c2["low"]
                        if gain >= 0.035:
                            has_fvg = any(candles[d+1]["low"] > candles[d-1]["high"] for d in range(i+1, min(h_idx, n-1)) if d+1 < n)
                            body_bos = any(c["close"] > max(x["high"] for x in candles[max(0, i-15):i]) for c in candles[i+1:h_idx+1])
                            if has_fvg and body_bos:
                                d_range = m_high - c2["low"]
                                fib_50 = m_high - 0.50 * d_range
                                fib_618 = m_high - 0.618 * d_range
                                idm_low = candles[h_idx-1]["low"]
                                entry_ceiling = fib_618 if allow_of_entry else c2["high"]
                                
                                for t in range(h_idx+1, min(h_idx+35, n)):
                                    tap = candles[t]
                                    idm_swept = any(candles[k]["low"] < idm_low for k in range(h_idx, t+1))
                                    touched = tap["low"] <= entry_ceiling
                                    if idm_swept and touched:
                                        btc_c = btc_map[tf].get(tap["time"])
                                        if btc_c and sym != "BTCUSDT" and ((btc_c["close"] - btc_c["open"]) / btc_c["open"]) < -0.010:
                                            break
                                        c_range = tap["high"] - tap["low"]
                                        w_ratio = (min(tap["open"], tap["close"]) - tap["low"]) / c_range if c_range > 0 else 0
                                        if w_ratio >= 0.18 and tap["close"] >= c2["low"]:
                                            entry = entry_ceiling
                                            tp_p = entry * (1.0 + target_spot_tp)
                                            sl_p = entry * (1.0 - target_spot_sl)
                                            be_trigger = entry * (1.0 + 0.0120) # +6% ROE -> BE Lock
                                            
                                            res = None; exit_p = entry; exit_t = tap["time"]; be_locked = False
                                            for m in range(t+1, min(t+max_hold, n)):
                                                if candles[m]["high"] >= be_trigger:
                                                    be_locked = True
                                                if candles[m]["high"] >= tp_p:
                                                    res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                if candles[m]["low"] <= (entry if be_locked else sl_p):
                                                    if be_locked: res = "WIN"; exit_p = entry
                                                    else: res = "LOSS"; exit_p = min(sl_p, candles[m]["open"])
                                                    exit_t = candles[m]["time"]; break
                                            if not res:
                                                fc = candles[min(t+max_hold, n-1)]["close"]
                                                res = "WIN" if fc >= entry else ("WIN" if be_locked else "LOSS")
                                                exit_p = entry if be_locked and fc < entry else fc
                                                exit_t = candles[min(t+max_hold, n-1)]["time"]
                                            
                                            trades.append({
                                                "sym": sym, "side": "LONG", "tf": tf, "time": tap["time"], "exit_time": exit_t,
                                                "entry": entry, "exit": exit_p, "gross": (exit_p - entry) / entry,
                                                "roe_pct": ((exit_p - entry) / entry) * 5.0 * 100.0, "res": res
                                            })
                                            break
    # Simulate sequential portfolio
    trades.sort(key=lambda x: x["time"])
    executed = []; active_exit = 0
    for t in trades:
        if t["time"] >= active_exit:
            executed.append(t); active_exit = t["exit_time"]
            
    if not executed: return {}
    tp_hits = [t for t in executed if t["roe_pct"] >= 14.5]
    be_saves = [t for t in executed if 0 <= t["roe_pct"] < 14.5 and t["res"] == "WIN"]
    losses = [t for t in executed if t["res"] == "LOSS"]
    
    bal = 50.0; vault = 0.0; peak = 50.0; max_dd = 0.0
    for t in executed:
        pos = bal * 5.0
        pnl = pos * (t["gross"] - 0.0016)
        if pnl >= 0:
            vault += pnl * 0.15; bal += pnl * 0.85
        else:
            bal += pnl
            if bal < 10.0: bal = 10.0
        eq = bal + vault
        if eq > peak: peak = eq
        dd = (peak - eq) / peak * 100.0
        if dd > max_dd: max_dd = dd

    return {
        "tf": "+".join(timeframes),
        "total_executed": len(executed),
        "tp_hits": len(tp_hits),
        "be_saves": len(be_saves),
        "losses": len(losses),
        "win_rate": round((len(tp_hits) + len(be_saves)) / len(executed) * 100, 2),
        "pure_tp_rate": round(len(tp_hits) / len(executed) * 100, 2),
        "final_equity": round(bal + vault, 2),
        "max_dd": round(max_dd, 2)
    }

print("Running 4H Macro Swings (15% ROE @ 5x)...")
res_4h = run_test(["4h"], allow_of_entry=True)
print("4H Results:", res_4h)

print("\nRunning 1H + 4H Combined (15% ROE @ 5x)...")
res_all = run_test(["1h", "4h"], allow_of_entry=True)
print("1H+4H Results:", res_all)
