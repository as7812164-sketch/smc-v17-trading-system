import os
import sys
import glob
import json
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "market_data_cache_15m"

def load_data():
    files = glob.glob(str(DATA_DIR / "*_15m.json"))
    coins_data = {}
    for f in sorted(files):
        sym = Path(f).name.replace("_15m.json", "")
        with open(f, "r", encoding="utf-8") as fp:
            raw = json.load(fp)
            for c in raw:
                c["open"] = float(c["open"])
                c["high"] = float(c["high"])
                c["low"] = float(c["low"])
                c["close"] = float(c["close"])
            if len(raw) >= 1000:
                coins_data[sym] = raw
    return coins_data

def group_by_day(candles):
    days = {}
    for idx, c in enumerate(candles):
        dt = datetime.datetime.fromtimestamp(c["time"] / 1000.0, tz=datetime.timezone.utc)
        k = dt.strftime("%Y-%m-%d")
        if k not in days:
            days[k] = []
        days[k].append((idx, c))
    return days

def compute_ema(prices, period):
    if len(prices) < period:
        return [prices[-1]] * len(prices)
    ema = []
    multiplier = 2 / (period + 1)
    sma = sum(prices[:period]) / period
    for _ in range(period - 1):
        ema.append(sma)
    ema.append(sma)
    for p in prices[period:]:
        cur_ema = (p - ema[-1]) * multiplier + ema[-1]
        ema.append(cur_ema)
    return ema

def classify_market_regime(price, e50, e200):
    diff_pct = abs(e50 - e200) / e200 * 100.0
    if diff_pct < 0.60:
        return "SIDEWAYS"
    elif e50 > e200 and price >= e50 * 0.998:
        return "UPTREND"
    elif e50 < e200 and price <= e50 * 1.002:
        return "DOWNTREND"
    else:
        return "SIDEWAYS"

def run_wick_filtered_test():
    coins_data = load_data()
    trades = []

    for sym, candles in coins_data.items():
        n = len(candles)
        closes = [c["close"] for c in candles]
        ema50 = compute_ema(closes, 50)
        ema200 = compute_ema(closes, 200)

        daily = group_by_day(candles)
        sorted_days = sorted(daily.keys())
        busy_until = 0

        for d_i in range(1, len(sorted_days)):
            p_day = sorted_days[d_i - 1]
            c_day = sorted_days[d_i]

            p_list = daily[p_day]
            c_list = daily[c_day]
            if len(p_list) < 80 or len(c_list) < 80:
                continue

            pdh = max(c[1]["high"] for c in p_list)
            pdl = min(c[1]["low"] for c in p_list)

            for idx_in_day, (g_idx, c) in enumerate(c_list):
                if c["time"] < busy_until:
                    continue

                c_o = c["open"]
                c_h = c["high"]
                c_l = c["low"]
                c_c = c["close"]
                c_rng = c_h - c_l
                if c_rng <= 0:
                    continue

                regime = classify_market_regime(c_c, ema50[g_idx], ema200[g_idx])

                # LONG: PDL Sweep + V-shape lower wick >= 25% + close above PDL
                if c_l < pdl and c_c > pdl:
                    lower_wick = min(c_o, c_c) - c_l
                    if (lower_wick / c_rng) >= 0.25:
                        entry_price = c_c
                        sl_price = c_l
                        risk = entry_price - sl_price
                        if risk > 0:
                            tp_price = entry_price + (risk * 2.0)
                            be_price = entry_price + risk

                            outcome = None
                            be_active = False
                            exit_time = c["time"]

                            for f_i in range(g_idx + 1, min(g_idx + 97, n)):
                                b = candles[f_i]
                                if not be_active and b["high"] >= be_price:
                                    be_active = True
                                if b["low"] <= sl_price:
                                    outcome = "SL_HIT"
                                    exit_time = b["time"]
                                    break
                                if b["high"] >= tp_price:
                                    outcome = "TP_HIT"
                                    exit_time = b["time"]
                                    break
                                if be_active and b["low"] <= entry_price:
                                    outcome = "BE_SAVE"
                                    exit_time = b["time"]
                                    break

                            if not outcome:
                                outcome = "TIMEOUT"

                            busy_until = exit_time
                            pnl_r = 2.0 if outcome == "TP_HIT" else (-1.0 if outcome == "SL_HIT" else 0.0)
                            trades.append({"symbol": sym, "side": "LONG", "regime": regime, "outcome": outcome, "pnl_r": pnl_r})

                # SHORT: PDH Sweep + V-shape upper wick >= 25% + close below PDH
                if c_h > pdh and c_c < pdh:
                    upper_wick = c_h - max(c_o, c_c)
                    if (upper_wick / c_rng) >= 0.25:
                        entry_price = c_c
                        sl_price = c_h
                        risk = sl_price - entry_price
                        if risk > 0:
                            tp_price = entry_price - (risk * 2.0)
                            be_price = entry_price - risk

                            outcome = None
                            be_active = False
                            exit_time = c["time"]

                            for f_i in range(g_idx + 1, min(g_idx + 97, n)):
                                b = candles[f_i]
                                if not be_active and b["low"] <= be_price:
                                    be_active = True
                                if b["high"] >= sl_price:
                                    outcome = "SL_HIT"
                                    exit_time = b["time"]
                                    break
                                if b["low"] <= tp_price:
                                    outcome = "TP_HIT"
                                    exit_time = b["time"]
                                    break
                                if be_active and b["high"] >= entry_price:
                                    outcome = "BE_SAVE"
                                    exit_time = b["time"]
                                    break

                            if not outcome:
                                outcome = "TIMEOUT"

                            busy_until = exit_time
                            pnl_r = 2.0 if outcome == "TP_HIT" else (-1.0 if outcome == "SL_HIT" else 0.0)
                            trades.append({"symbol": sym, "side": "SHORT", "regime": regime, "outcome": outcome, "pnl_r": pnl_r})

    def print_res(t_list, label):
        tot = len(t_list)
        if tot == 0:
            return
        tp = sum(1 for x in t_list if x["outcome"] == "TP_HIT")
        be = sum(1 for x in t_list if x["outcome"] == "BE_SAVE")
        sl = sum(1 for x in t_list if x["outcome"] == "SL_HIT")
        wr = tp / (tp + sl) * 100.0 if (tp + sl) > 0 else 0.0
        non_loss = (tp + be) / tot * 100.0
        net_r = sum(x["pnl_r"] for x in t_list)
        print(f"{label:<30} | Total: {tot:<5} | TP: {tp:<4} | BE: {be:<4} | SL: {sl:<4} | Pure WR: {wr:5.1f}% | Non-Loss: {non_loss:5.1f}% | Net: {net_r:+7.1f} R")

    print("\n" + "=" * 95)
    print("🌟 WITH V-SHAPE REJECTION WICK >= 25% + BREAK-EVEN ARMOR AT 1:1")
    print("=" * 95)
    print_res([t for t in trades if t["regime"] == "SIDEWAYS"], "SIDEWAYS (Ranging)")
    print_res([t for t in trades if t["regime"] == "DOWNTREND"], "DOWNTREND (Bearish)")
    print_res([t for t in trades if t["regime"] == "UPTREND"], "UPTREND (Bullish)")
    print("-" * 95)
    print_res(trades, "TOTAL ALL REGIMES")
    print("=" * 95 + "\n")

if __name__ == "__main__":
    run_wick_filtered_test()
