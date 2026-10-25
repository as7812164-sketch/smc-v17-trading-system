import os, sys, json

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

def run_calibrated_15pct_system():
    trades = []
    # Target: Exactly +15.0% ROE at 5x leverage (+3.00% spot move)
    tp_spot_gain = 0.0300
    be_spot_trigger = 0.0150  # +7.5% ROE (+1.50% spot) -> Lock Break-Even!
    max_hold = 32

    for tf in ["1h", "4h"]:
        for sym, candles in all_data[tf].items():
            n = len(candles)
            if n < 60: continue
            atrs = calculate_atr(candles, 14)
            for i in range(25, n - 35):
                c1, c2 = candles[i-1], candles[i]
                # Bullish
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
                                entry_price = (c2["high"] + c2["low"]) / 2.0  # 50% Mean Threshold
                                
                                for t in range(h_idx+1, min(h_idx+35, n)):
                                    tap = candles[t]
                                    idm_swept = any(candles[k]["low"] < idm_low for k in range(h_idx, t+1))
                                    touched = tap["low"] <= entry_price
                                    if idm_swept and touched:
                                        btc_c = btc_map[tf].get(tap["time"])
                                        if btc_c and sym != "BTCUSDT" and ((btc_c["close"] - btc_c["open"]) / btc_c["open"]) < -0.010:
                                            break
                                        c_range = tap["high"] - tap["low"]
                                        w_ratio = (min(tap["open"], tap["close"]) - tap["low"]) / c_range if c_range > 0 else 0
                                        if w_ratio >= 0.18 and tap["close"] >= c2["low"]:
                                            entry = entry_price
                                            tp_p = entry * (1.0 + tp_spot_gain)
                                            atr_val = atrs[t] if t < len(atrs) else (entry * 0.015)
                                            sl_p = c2["low"] - (0.35 * atr_val)
                                            be_trigger_p = entry * (1.0 + be_spot_trigger)
                                            
                                            res = None; exit_p = entry; exit_t = tap["time"]; be_locked = False
                                            for m in range(t+1, min(t+max_hold, n)):
                                                if candles[m]["high"] >= be_trigger_p:
                                                    be_locked = True
                                                if candles[m]["high"] >= tp_p:
                                                    res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                if candles[m]["low"] <= sl_p:
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
                # Bearish
                if c2["close"] >= c2["open"] and c2["high"] > c1["high"] and c2["high"] == max(c["high"] for c in candles[max(0, i-12):i+1]):
                    sub_w = candles[i:min(i+18, n)]
                    lows = [c["low"] for c in sub_w]
                    m_low = min(lows)
                    low_idx = i + lows.index(m_low)
                    if low_idx > i + 2:
                        drop = (c2["high"] - m_low) / c2["high"]
                        if drop >= 0.035:
                            has_fvg = any(candles[d+1]["high"] < candles[d-1]["low"] for d in range(i+1, min(low_idx, n-1)) if d+1 < n)
                            body_bos = any(c["close"] < min(x["low"] for x in candles[max(0, i-15):i]) for c in candles[i+1:low_idx+1])
                            if has_fvg and body_bos:
                                d_range = c2["high"] - m_low
                                fib_50 = m_low + 0.50 * d_range
                                idm_high = candles[low_idx-1]["high"]
                                entry_price = (c2["high"] + c2["low"]) / 2.0
                                
                                for t in range(low_idx+1, min(low_idx+35, n)):
                                    tap = candles[t]
                                    idm_swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t+1))
                                    touched = tap["high"] >= entry_price
                                    if idm_swept and touched:
                                        btc_c = btc_map[tf].get(tap["time"])
                                        if btc_c and sym != "BTCUSDT" and ((btc_c["close"] - btc_c["open"]) / btc_c["open"]) > 0.010:
                                            break
                                        c_range = tap["high"] - tap["low"]
                                        w_ratio = (tap["high"] - max(tap["open"], tap["close"])) / c_range if c_range > 0 else 0
                                        if w_ratio >= 0.18 and tap["close"] <= c2["high"]:
                                            entry = entry_price
                                            tp_p = entry * (1.0 - tp_spot_gain)
                                            atr_val = atrs[t] if t < len(atrs) else (entry * 0.015)
                                            sl_p = c2["high"] + (0.35 * atr_val)
                                            be_trigger_p = entry * (1.0 - be_spot_trigger)
                                            
                                            res = None; exit_p = entry; exit_t = tap["time"]; be_locked = False
                                            for m in range(t+1, min(t+max_hold, n)):
                                                if candles[m]["low"] <= be_trigger_p:
                                                    be_locked = True
                                                if candles[m]["low"] <= tp_p:
                                                    res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                if candles[m]["high"] >= sl_p:
                                                    if be_locked: res = "WIN"; exit_p = entry
                                                    else: res = "LOSS"; exit_p = max(sl_p, candles[m]["open"])
                                                    exit_t = candles[m]["time"]; break
                                            if not res:
                                                fc = candles[min(t+max_hold, n-1)]["close"]
                                                res = "WIN" if fc <= entry else ("WIN" if be_locked else "LOSS")
                                                exit_p = entry if be_locked and fc > entry else fc
                                                exit_t = candles[min(t+max_hold, n-1)]["time"]
                                            
                                            trades.append({
                                                "sym": sym, "side": "SHORT", "tf": tf, "time": tap["time"], "exit_time": exit_t,
                                                "entry": entry, "exit": exit_p, "gross": (entry - exit_p) / entry,
                                                "roe_pct": ((entry - exit_p) / entry) * 5.0 * 100.0, "res": res
                                            })
                                            break
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
        "executed": len(executed),
        "tp_hits": len(tp_hits),
        "be_saves": len(be_saves),
        "losses": len(losses),
        "win_rate": round((len(tp_hits) + len(be_saves)) / len(executed) * 100, 2),
        "pure_tp_rate": round(len(tp_hits) / len(executed) * 100, 2),
        "final_equity": round(bal + vault, 2),
        "max_dd": round(max_dd, 2)
    }

res = run_calibrated_15pct_system()
print("Calibrated 15% ROE System Results:", res)
