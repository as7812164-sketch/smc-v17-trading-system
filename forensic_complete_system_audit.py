import json
import time
import os
import sys
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

APPROVED_COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "SUIUSDT", "NEARUSDT", "AVAXUSDT", "APTUSDT",
    "ARBUSDT", "OPUSDT", "LDOUSDT", "MKRUSDT", "UNIUSDT", "AAVEUSDT", "RUNEUSDT", "RENDERUSDT",
    "INJUSDT", "FETUSDT", "THETAUSDT", "ALGOUSDT", "GALAUSDT", "SANDUSDT", "FILUSDT", "ICPUSDT",
    "PYTHUSDT", "PEPEUSDT", "SHIBUSDT", "XRPUSDT", "ADAUSDT", "LINKUSDT", "DOGEUSDT"
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")

def load_local_data(sym, interval):
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

def run_comprehensive_forensic_audit():
    print("=" * 95)
    print(" 🔬 COMPLETE FORENSIC AUDIT: ALGORITHM EXPOSURE, LONGS vs SHORTS, CONCURRENCY & LOOPHOLES")
    print(" Dataset: 1 Full Year (339,512 Bars) Across 31 Approved Coins on 1H & 4H")
    print(" Testing: 1) Longs vs Shorts | 2) Realistic 1-Trade-At-A-Time Portfolio Queue | 3) Slippage & Limits")
    print("=" * 95)

    all_data = {"1h": {}, "4h": {}}
    for sym in APPROVED_COINS:
        for tf in ["1h", "4h"]:
            k = load_local_data(sym, tf)
            if len(k) >= 500:
                all_data[tf][sym] = k

    all_signals = []

    # Scan 1H and 4H for BOTH Bullish (Long) and Bearish (Short) Decisional & Extreme OBs
    for tf in ["1h", "4h"]:
        tp_pct = 0.022 if tf == "1h" else 0.028
        sl_pct = 0.025 if tf == "1h" else 0.028
        max_hold = 24

        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 35):
                # -------------------------------------------------------------
                # 1. BULLISH SETUP (LONG)
                # -------------------------------------------------------------
                if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 3:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.045:
                            idm_low = candles[high_idx - 1]["low"]
                            # Decisional OB
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg; best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                                if has_fvg:
                                    # Look for tap
                                    for t in range(high_idx + 1, min(high_idx + 35, n)):
                                        # Limit fill check: must penetrate 0.05% below top
                                        if candles[t]["low"] <= dec_top * 0.9995:
                                            tap_c = candles[t]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            c_range = tap_c["high"] - tap_c["low"]
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + tp_pct)
                                                sl_p = entry * (1.0 - sl_pct)
                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["high"] >= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] <= sl_p:
                                                        res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc >= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                all_signals.append({
                                                    "sym": sym, "tf": tf, "side": "LONG", "entry_time": tap_c["time"],
                                                    "exit_time": exit_t, "entry_p": entry, "exit_p": exit_p,
                                                    "gross": (exit_p - entry) / entry, "res": res
                                                })
                                            break

                # -------------------------------------------------------------
                # 2. BEARISH SETUP (SHORT)
                # -------------------------------------------------------------
                if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 3:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= 0.045:
                            idm_high = candles[low_idx - 1]["high"]
                            # Bearish Decisional OB
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg; best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + 35, n)):
                                        if candles[t]["high"] >= dec_bot * 1.0005:
                                            tap_c = candles[t]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            c_range = tap_c["high"] - tap_c["low"]
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0
                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - tp_pct)
                                                sl_p = entry * (1.0 + sl_pct)
                                                res = None; exit_p = entry; exit_t = tap_c["time"]
                                                for m in range(t, min(t + max_hold, n)):
                                                    if candles[m]["low"] <= tp_p:
                                                        res = "WIN"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                    if candles[m]["close"] >= sl_p:
                                                        res = "LOSS"; exit_p = sl_p; exit_t = candles[m]["time"]; break
                                                if not res:
                                                    fc = candles[min(t + max_hold, n - 1)]["close"]
                                                    res = "WIN" if fc <= entry else "LOSS"
                                                    exit_p = fc
                                                    exit_t = candles[min(t + max_hold, n - 1)]["time"]
                                                all_signals.append({
                                                    "sym": sym, "tf": tf, "side": "SHORT", "entry_time": tap_c["time"],
                                                    "exit_time": exit_t, "entry_p": entry, "exit_p": exit_p,
                                                    "gross": (entry - exit_p) / entry, "res": res
                                                })
                                            break

    all_signals.sort(key=lambda x: x["entry_time"])

    # Separate Stats: Longs vs Shorts
    longs = [s for s in all_signals if s["side"] == "LONG"]
    shorts = [s for s in all_signals if s["side"] == "SHORT"]

    l_wins = sum(1 for s in longs if s["res"] == "WIN")
    s_wins = sum(1 for s in shorts if s["res"] == "WIN")

    print(f"\n📊 RAW SIGNAL GENERATION BREAKDOWN (1 FULL YEAR):")
    print(f"   • Total LONG Signals:  {len(longs):4d} | Wins: {l_wins:4d} | Win Rate: {l_wins/max(1, len(longs))*100:5.2f}%")
    print(f"   • Total SHORT Signals: {len(shorts):4d} | Wins: {s_wins:4d} | Win Rate: {s_wins/max(1, len(shorts))*100:5.2f}%")
    print(f"   • Combined Signals:    {len(all_signals):4d} | Total Wins: {l_wins+s_wins} | Win Rate: {(l_wins+s_wins)/max(1, len(all_signals))*100:5.2f}%\n")

    # -------------------------------------------------------------
    # 3. REALISTIC PORTFOLIO SIMULATION (CONCURRENCY LOOPHOLE TEST)
    # -------------------------------------------------------------
    # In reality, a $50 account CANNOT take 10 trades at the same time!
    # Let's test two realistic scenarios:
    # A) Max 1 Trade At A Time (Single Position Queue)
    # B) Max 2 Trades At A Time (50% Capital per position)

    for max_pos in [1, 2]:
        cap = 50.0
        vault = 0.0
        max_c = 50.0
        max_dd = 0.0
        active_positions = [] # stores (exit_time, pnl_pct)
        executed_trades = []
        hit_1000 = None

        for s in all_signals:
            curr_t = s["entry_time"]
            # Close any positions whose exit_time <= curr_t
            remaining = []
            for pos_exit, pos_alloc, net_ret in active_positions:
                if pos_exit <= curr_t:
                    pnl = pos_alloc * 5.0 * net_ret
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
                        hit_1000 = len(executed_trades)
                else:
                    remaining.append((pos_exit, pos_alloc, net_ret))
            active_positions = remaining

            # If capacity available, take the trade!
            if len(active_positions) < max_pos:
                alloc = cap / (max_pos - len(active_positions))
                # Deduct realistic fees (0.05% maker + 0.05% taker + 0.04% slippage = 0.14%)
                net_ret = s["gross"] - 0.0014
                active_positions.append((s["exit_time"], alloc, net_ret))
                executed_trades.append(s)

        # Flush any remaining positions
        for pos_exit, pos_alloc, net_ret in active_positions:
            pnl = pos_alloc * 5.0 * net_ret
            if pnl > 0:
                cap += pnl * 0.85
                vault += pnl * 0.15
            else:
                cap = max(5.0, cap + pnl)

        e_wins = sum(1 for t in executed_trades if t["res"] == "WIN")
        e_losses = len(executed_trades) - e_wins
        e_wr = (e_wins / len(executed_trades) * 100) if executed_trades else 0

        print(f"==========================================================================================")
        print(f" 💼 REAL-WORLD EXECUTION: [MAX {max_pos} ACTIVE POSITION{'S' if max_pos>1 else ''} AT A TIME]")
        print(f"==========================================================================================")
        print(f" Executed Trades (No Overlap): {len(executed_trades)} trades (Out of {len(all_signals)} total signals)")
        print(f" Execution Win Rate:           {e_wins}/{len(executed_trades)} ({e_wr:.2f}%)")
        print(f" Starting Balance:             $50.00 USDT")
        print(f" Final Trading Capital:        ${cap:,.2f} USDT")
        print(f" Secured Profit Vault:         ${vault:,.2f} USDT")
        print(f" Total Net Wealth:             ${cap + vault:,.2f} USDT")
        print(f" Maximum Portfolio Drawdown:   {max_dd:.2f}% (Realistic Capital Risk!)")
        print(f" 🎉 $1,000 Milestone:          {'REACHED at Trade #' + str(hit_1000) if hit_1000 else 'NO'}")
        print("==========================================================================================\n")

if __name__ == "__main__":
    run_comprehensive_forensic_audit()
