import os
import json
import time
import sys
from datetime import datetime

CACHE_DIR = "market_data_cache"

TIER1_COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT",
    "SUIUSDT", "AVAXUSDT", "UNIUSDT", "NEARUSDT", "ARBUSDT",
    "APTUSDT", "LTCUSDT", "LINKUSDT", "ADAUSDT", "XRPUSDT"
]

def load_cached_tier1(interval):
    data = {}
    for sym in TIER1_COINS:
        fpath = os.path.join(CACHE_DIR, f"{sym}_{interval}.json")
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if raw and len(raw) >= 60:
                    running_cvd = 0.0
                    for c in raw:
                        v = c.get("volume", 0.0)
                        tb = c.get("taker_buy", v * 0.5)
                        ts = max(0.0, v - tb)
                        delta = tb - ts
                        running_cvd += delta
                        c["taker_buy"] = tb
                        c["taker_sell"] = ts
                        c["delta"] = delta
                        c["cvd"] = running_cvd
                    data[sym] = raw
    return data

def run_all_strategies(interval):
    is_1h = (interval == "1h")
    data = load_cached_tier1(interval)

    tp_pct = 0.0150 if is_1h else 0.0240
    be_pct = 0.0075 if is_1h else 0.0105
    sl_pct = 0.0200 if is_1h else 0.0225
    min_rally_pct = 0.020 if is_1h else 0.030

    # 5 Strategies
    strat_trades = {
        "1. Standard Retail SMC": [],
        "2. Classical SMC V17 (3-OB Middle Only)": [],
        "3. Super Sniper Order Flow": [],
        "4. The Elite Trifecta": [],
        "5. 👑 Ultimate Unified Hybrid (Score >= 80)": []
    }

    for sym, candles in data.items():
        n = len(candles)
        if n < 50:
            continue

        for i in range(15, n - 25):
            c = candles[i]
            if c["close"] >= c["open"]:
                continue
            ob_high = c["high"]
            ob_low = c["low"]
            if ob_high <= ob_low:
                continue

            # Standard expansion check
            future_highs = [candles[i+k]["high"] for k in range(1, min(7, n - i))]
            if not future_highs or (max(future_highs) - ob_high) / ob_high < min_rally_pct:
                continue

            entry_p = ob_high
            tp_target = entry_p * (1.0 + tp_pct)
            be_target = entry_p * (1.0 + be_pct)
            sl_target = entry_p * (1.0 - sl_pct)

            # Search 1st tap
            entry_idx = -1
            for k in range(i + 3, min(i + 40, n)):
                if candles[k]["low"] <= entry_p and candles[k]["high"] >= entry_p:
                    entry_idx = k
                    break

            if entry_idx == -1:
                continue

            entry_c = candles[entry_idx]
            entry_time = entry_c["time"]

            # Factors
            vol = entry_c.get("volume", 0.0)
            tb = entry_c.get("taker_buy", vol * 0.5)
            d_ratio = (tb / vol) if vol > 0 else 0.50
            prev_cvd = candles[entry_idx - 2]["cvd"] if entry_idx >= 2 else candles[0]["cvd"]
            cvd_reversal = (entry_c["cvd"] - prev_cvd) > 0

            pullback_window = [candles[x]["low"] for x in range(i + 1, entry_idx)]
            idm_swept = (pullback_window and entry_c["low"] <= min(pullback_window))

            is_2nd_ob = (entry_c["close"] <= ob_high * 1.01)

            lower_wick = min(entry_c["open"], entry_c["close"]) - entry_c["low"]
            c_range = entry_c["high"] - entry_c["low"]
            wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
            bid_wall = (wick_ratio >= 0.20) or (d_ratio >= 0.52)

            # Qualification flags
            pass_retail = True # Any OB, no filters
            pass_smc_v17 = is_2nd_ob # 2nd OB only
            pass_sniper = (d_ratio >= 0.51) and cvd_reversal
            pass_trifecta = idm_swept and is_2nd_ob and bid_wall

            score = 40
            if d_ratio >= 0.51: score += 15
            if cvd_reversal: score += 15
            if idm_swept: score += 15
            if is_2nd_ob: score += 10
            if bid_wall: score += 15
            pass_hybrid = (score >= 80)

            # Simulate outcome WITH Breakeven (for Strats 3, 4, 5) and WITHOUT Breakeven (for Strats 1, 2)
            # Evaluate without BE
            res_no_be = None
            bars_held_no_be = 0
            for m in range(entry_idx, min(entry_idx + 35, n)):
                curr = candles[m]
                bars_held_no_be += 1
                if curr["high"] >= tp_target:
                    res_no_be = "WIN"
                    break
                if curr["close"] <= sl_target:
                    res_no_be = "LOSS"
                    break
            if not res_no_be:
                res_no_be = "LOSS"

            # Evaluate with BE
            res_be = None
            be_active = False
            bars_held_be = 0
            for m in range(entry_idx, min(entry_idx + 35, n)):
                curr = candles[m]
                bars_held_be += 1
                if not be_active and curr["high"] >= be_target:
                    be_active = True
                if curr["high"] >= tp_target:
                    res_be = "WIN"
                    break
                if be_active and curr["low"] <= entry_p:
                    res_be = "BREAKEVEN"
                    break
                if curr["close"] <= sl_target:
                    res_be = "LOSS"
                    break
            if not res_be:
                res_be = "BREAKEVEN" if be_active else "LOSS"

            base_rec = {
                "symbol": sym,
                "time": entry_time,
                "date": datetime.fromtimestamp(entry_time / 1000).strftime("%Y-%m-%d %H:%M"),
                "hours_no_be": bars_held_no_be if is_1h else bars_held_no_be * 4,
                "hours_be": bars_held_be if is_1h else bars_held_be * 4,
                "result_no_be": res_no_be,
                "result_be": res_be
            }

            if pass_retail:
                strat_trades["1. Standard Retail SMC"].append({**base_rec, "result": res_no_be, "hours": base_rec["hours_no_be"]})
            if pass_smc_v17:
                strat_trades["2. Classical SMC V17 (3-OB Middle Only)"].append({**base_rec, "result": res_no_be, "hours": base_rec["hours_no_be"]})
            if pass_sniper:
                strat_trades["3. Super Sniper Order Flow"].append({**base_rec, "result": res_be, "hours": base_rec["hours_be"]})
            if pass_trifecta:
                strat_trades["4. The Elite Trifecta"].append({**base_rec, "result": res_be, "hours": base_rec["hours_be"]})
            if pass_hybrid:
                strat_trades["5. 👑 Ultimate Unified Hybrid (Score >= 80)"].append({**base_rec, "result": res_be, "hours": base_rec["hours_be"]})

    return strat_trades

def process_benchmark(strat_dict, is_1h=True):
    results = []
    roi_win = 0.075 if is_1h else 0.12
    roi_loss = -0.10

    for name, trades in strat_dict.items():
        trades.sort(key=lambda x: x["time"])
        sample = trades[:100]
        total = len(sample)
        if total == 0:
            continue

        wins = sum(1 for t in sample if t["result"] == "WIN")
        bes = sum(1 for t in sample if t["result"] == "BREAKEVEN")
        losses = sum(1 for t in sample if t["result"] == "LOSS")

        wr = (wins / total) * 100.0
        be_rate = (bes / total) * 100.0
        loss_rate = (losses / total) * 100.0
        safety = ((wins + bes) / total) * 100.0
        avg_h = sum(t["hours"] for t in sample) / total

        cap = 50.0
        m1k_trade = None
        m1k_date = None

        for idx, t in enumerate(sample, 1):
            if t["result"] == "WIN":
                cap += cap * roi_win
            elif t["result"] == "LOSS":
                cap += cap * roi_loss
            
            if not m1k_trade and cap >= 1000.0:
                m1k_trade = idx
                m1k_date = t["date"]

        days = (sample[-1]["time"] - sample[0]["time"]) / (86400 * 1000) if total > 1 else 0

        results.append({
            "strategy": name,
            "sample_trades": total,
            "days_to_complete": round(days, 1),
            "win_rate": round(wr, 1),
            "be_rate": round(be_rate, 1),
            "loss_rate": round(loss_rate, 1),
            "safety_rate": round(safety, 1),
            "avg_hours": round(avg_h, 1),
            "final_balance": round(cap, 2),
            "net_gain_pct": round(((cap - 50.0) / 50.0) * 100.0, 1),
            "m1k_trade": m1k_trade,
            "m1k_date": m1k_date
        })
    return results

if __name__ == "__main__":
    b1h = process_benchmark(run_all_strategies("1h"), is_1h=True)
    b4h = process_benchmark(run_all_strategies("4h"), is_1h=False)

    print("=== 1H BENCHMARK ===")
    print(json.dumps(b1h, indent=2))
    print("\n=== 4H BENCHMARK ===")
    print(json.dumps(b4h, indent=2))
