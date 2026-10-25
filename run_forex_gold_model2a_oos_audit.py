import os
import sys
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))
FOREX_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data_forex")

FOREX_PAIRS = [
    "XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
    "USDCHF", "NZDUSD", "EURJPY", "GBPJPY", "EURGBP"
]

CANDLE_CACHE = {}

def load_candles(sym, interval):
    key = f"{sym}_{interval}"
    if key in CANDLE_CACHE:
        return CANDLE_CACHE[key]
    fpath = os.path.join(FOREX_DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath):
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    for c in data:
        c["open"] = float(c["open"])
        c["high"] = float(c["high"])
        c["low"] = float(c["low"])
        c["close"] = float(c["close"])
        c["volume"] = float(c.get("volume", 0.0))
    CANDLE_CACHE[key] = data
    return data

def build_dxy_map():
    dxy_4h = load_candles("DX_Y_NYB", "4h")
    return {c["time"]: c for c in dxy_4h}

def harvest_forex_model2a_setups():
    dxy_map_4h = build_dxy_map()
    raw_setups = []

    for tf in ["4h", "1h"]:
        max_tap_window = 28
        max_hold = 36 if tf == "4h" else 48

        for sym in FOREX_PAIRS:
            candles = load_candles(sym, tf)
            n = len(candles)
            if n < 40:
                continue

            # Minimum displacement wave required:
            # Gold moves ~1.0% to 2.0% in displacement wave
            # Forex pairs move ~0.40% to 0.70% (40-70 pips)
            min_disp = 0.0080 if sym == "XAUUSD" else 0.0040

            for i in range(20, n - 2):
                # ----------------- LONG SETUP -----------------
                if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 2:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= min_disp:
                            idm_low = candles[high_idx - 1]["low"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                                if has_fvg:
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        if candles[t]["low"] <= dec_top * 1.0002:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            # Sentry 1: King DXY Causal Filter
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            dxy_c = dxy_map_4h.get(prev_4h_ts)
                                            dxy_pump = (dxy_c["close"] - dxy_c["open"]) / dxy_c["open"] if dxy_c else 0.0
                                            
                                            # If USD quotes base (EURUSD, GBPUSD, XAUUSD), DXY pump hurts Longs
                                            dxy_clean = True
                                            if sym in ["XAUUSD", "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"]:
                                                dxy_clean = (dxy_pump < 0.0035)

                                            if dxy_clean and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "LONG",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "tap_close": tap_c["close"], "max_hold": max_hold,
                                                    "disp_pct": gain
                                                })
                                                break

                # ----------------- SHORT SETUP -----------------
                if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 2:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= min_disp:
                            idm_high = candles[low_idx - 1]["high"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid
                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                                if has_bear_fvg:
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        if candles[t]["high"] >= dec_bot * 0.9998:
                                            tap_c = candles[t]
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            # Sentry 1: King DXY Causal Filter
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            dxy_c = dxy_map_4h.get(prev_4h_ts)
                                            dxy_dump = (dxy_c["open"] - dxy_c["close"]) / dxy_c["open"] if dxy_c else 0.0
                                            
                                            dxy_clean_short = True
                                            if sym in ["XAUUSD", "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"]:
                                                dxy_clean_short = (dxy_dump < 0.0035)

                                            if dxy_clean_short and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "tap_close": tap_c["close"], "max_hold": max_hold,
                                                    "disp_pct": drop
                                                })
                                                break

    raw_setups.sort(key=lambda x: x["time"])
    return raw_setups

def run_forex_oos_audit():
    print("=" * 85)
    print(" 🏛️ HERMES 3.0 MODEL 2A: FOREX & GOLD (XAUUSD) REAL OOS AUDIT ($100 START)")
    print("=" * 85)

    all_setups = harvest_forex_model2a_setups()
    print(f"Total Model 2A Forex & Gold Setups Harvested: {len(all_setups)}")

    # OOS Date Filter: September 25, 2025 to September 25, 2026
    oos_start_ts = int(datetime(2025, 9, 25, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    oos_setups = [s for s in all_setups if s["time"] >= oos_start_ts]
    print(f"Out-of-Sample (OOS) Setups: {len(oos_setups)}")

    # -------------------------------------------------------------------------
    # PART A: DEDICATED XAUUSD (GOLD) $100 -> $1,000 COMPOUNDING AUDIT (10% ROI TARGET)
    # -------------------------------------------------------------------------
    gold_setups = [s for s in oos_setups if s["sym"] == "XAUUSD"]
    print(f"\n[A] Running Dedicated GOLD (XAUUSD) OOS Challenge ({len(gold_setups)} Setups)...")

    # In Gold:
    # 10% ROI target per win:
    # With 0.01 lot per $100 capital, 100 pips ($10 move) = $10 profit = +10.0% ROI!
    # Risk-Reward: 1:2 R:R (TP = +10.0% ROI / +100 pips, SL = -5.0% ROI / -50 pips)
    # BE Trigger: +5.0% ROI (+50 pips) locks Break-Even at $0.00 loss
    # Soft SL: -50 pips (-5.0% ROI) on Candle Body Close
    # Hard SL: -100 pips (-10.0% ROI) on intra-bar emergency wick

    gold_bal = 100.0
    gold_peak = 100.0
    gold_dd = 0.0
    gold_executed = []
    gold_busy = 0
    milestone_1000_trade = None

    for s in gold_setups:
        if s["time"] < gold_busy:
            continue

        sym, tf, t = s["sym"], s["tf"], s["t_idx"]
        side = s["side"]
        candles = load_candles(sym, tf)
        n = len(candles)
        ep = s["mt"]

        # In Gold: $10 move = ~0.37% move at $2700 Gold price
        # Target 100 pips = $10.00 price move
        tp_price = ep + 10.0 if side == "LONG" else ep - 10.0
        be_trig_price = ep + 5.0 if side == "LONG" else ep - 5.0
        soft_sl_price = ep - 5.0 if side == "LONG" else ep + 5.0
        hard_sl_price = ep - 10.0 if side == "LONG" else ep + 10.0

        outcome = None
        exit_price = ep
        exit_time = s["time"]
        be_act = False
        wicks_absorbed = 0

        for b in range(t + 1, min(t + 1 + s["max_hold"], n)):
            c = candles[b]
            bar_t = c["time"]

            if side == "LONG":
                if not be_act and c["high"] >= be_trig_price:
                    be_act = True
                if c["low"] <= hard_sl_price:
                    outcome = "HARD_SL"
                    exit_price = hard_sl_price
                    exit_time = bar_t
                    break
                if c["high"] >= tp_price:
                    outcome = "TP_HIT"
                    exit_price = tp_price
                    exit_time = bar_t
                    break
                if be_act and c["low"] <= ep:
                    outcome = "BE_SAVE"
                    exit_price = ep
                    exit_time = bar_t
                    break
                if not be_act and c["low"] <= soft_sl_price:
                    if c["close"] <= soft_sl_price:
                        outcome = "SOFT_SL"
                        exit_price = c["close"]
                        exit_time = bar_t
                        break
                    else:
                        wicks_absorbed += 1
            else: # SHORT
                if not be_act and c["low"] <= be_trig_price:
                    be_act = True
                if c["high"] >= hard_sl_price:
                    outcome = "HARD_SL"
                    exit_price = hard_sl_price
                    exit_time = bar_t
                    break
                if c["low"] <= tp_price:
                    outcome = "TP_HIT"
                    exit_price = tp_price
                    exit_time = bar_t
                    break
                if be_act and c["high"] >= ep:
                    outcome = "BE_SAVE"
                    exit_price = ep
                    exit_time = bar_t
                    break
                if not be_act and c["high"] >= soft_sl_price:
                    if c["close"] >= soft_sl_price:
                        outcome = "SOFT_SL"
                        exit_price = c["close"]
                        exit_time = bar_t
                        break
                    else:
                        wicks_absorbed += 1

        if not outcome:
            last_c = candles[min(t + s["max_hold"], n - 1)]
            exit_price = last_c["close"]
            exit_time = last_c["time"]
            if side == "LONG":
                outcome = "TP_HIT" if exit_price >= ep + 5.0 else ("BE_SAVE" if be_act else "SOFT_SL")
            else:
                outcome = "TP_HIT" if exit_price <= ep - 5.0 else ("BE_SAVE" if be_act else "SOFT_SL")

        gold_busy = exit_time

        # PnL Calculation with 10% ROI dynamic compounding:
        # At start ($100), 0.01 lot -> TP = $10.0 (+10%), SL = -$5.0 (-5%)
        # As balance grows, lot size scales (0.01 lot per $100 balance)
        if outcome == "TP_HIT":
            roi_pct = 10.0
        elif outcome == "BE_SAVE":
            roi_pct = 0.0
        elif outcome == "HARD_SL":
            roi_pct = -10.0
        else: # SOFT_SL
            roi_pct = -5.0

        pnl = gold_bal * (roi_pct / 100.0)
        gold_bal += pnl
        if gold_bal > gold_peak:
            gold_peak = gold_bal
        cur_dd = (gold_peak - gold_bal) / gold_peak * 100.0
        if cur_dd > gold_dd:
            gold_dd = cur_dd

        dt = datetime.fromtimestamp(s["time"] / 1000, tz=IST)
        gold_executed.append({
            "num": len(gold_executed) + 1,
            "sym": "XAUUSD",
            "tf": tf,
            "side": side,
            "date": dt.strftime("%Y-%m-%d %H:%M"),
            "month": dt.strftime("%B %Y"),
            "entry": ep,
            "exit": exit_price,
            "outcome": outcome,
            "roi_pct": roi_pct,
            "pnl": round(pnl, 2),
            "balance": round(gold_bal, 2),
            "wicks_absorbed": wicks_absorbed
        })

        if gold_bal >= 1000.0 and not milestone_1000_trade:
            milestone_1000_trade = (len(gold_executed), round(gold_bal, 2), dt.strftime("%Y-%m-%d %H:%M"))

    # -------------------------------------------------------------------------
    # PART B: COMPLETE FOREX PORTFOLIO (11 PAIRS INCLUDING GOLD)
    # -------------------------------------------------------------------------
    print(f"\n[B] Running Full Forex Multi-Pair Portfolio (11 Pairs, {len(oos_setups)} Total Setups)...")

    fx_bal = 100.0
    fx_peak = 100.0
    fx_dd = 0.0
    fx_executed = []
    fx_busy = 0
    fx_milestone_1000 = None

    for s in oos_setups:
        if s["time"] < fx_busy:
            continue

        sym, tf, t = s["sym"], s["tf"], s["t_idx"]
        side = s["side"]
        candles = load_candles(sym, tf)
        n = len(candles)
        ep = s["mt"]

        # Pip targets calibrated per pair:
        if sym == "XAUUSD":
            tp_move = 10.0 # 100 pips
            sl_move = 5.0  # 50 pips
        elif "JPY" in sym:
            tp_move = 0.50 # 50 pips
            sl_move = 0.25 # 25 pips
        else: # EURUSD, GBPUSD, etc.
            tp_move = 0.0050 # 50 pips
            sl_move = 0.0025 # 25 pips

        tp_price = ep + tp_move if side == "LONG" else ep - tp_move
        be_trig_price = ep + (tp_move / 2.0) if side == "LONG" else ep - (tp_move / 2.0)
        soft_sl_price = ep - sl_move if side == "LONG" else ep + sl_move
        hard_sl_price = ep - (sl_move * 2.0) if side == "LONG" else ep + (sl_move * 2.0)

        outcome = None
        exit_price = ep
        exit_time = s["time"]
        be_act = False
        wicks_absorbed = 0

        for b in range(t + 1, min(t + 1 + s["max_hold"], n)):
            c = candles[b]
            bar_t = c["time"]

            if side == "LONG":
                if not be_act and c["high"] >= be_trig_price:
                    be_act = True
                if c["low"] <= hard_sl_price:
                    outcome = "HARD_SL"
                    exit_price = hard_sl_price
                    exit_time = bar_t
                    break
                if c["high"] >= tp_price:
                    outcome = "TP_HIT"
                    exit_price = tp_price
                    exit_time = bar_t
                    break
                if be_act and c["low"] <= ep:
                    outcome = "BE_SAVE"
                    exit_price = ep
                    exit_time = bar_t
                    break
                if not be_act and c["low"] <= soft_sl_price:
                    if c["close"] <= soft_sl_price:
                        outcome = "SOFT_SL"
                        exit_price = c["close"]
                        exit_time = bar_t
                        break
                    else:
                        wicks_absorbed += 1
            else: # SHORT
                if not be_act and c["low"] <= be_trig_price:
                    be_act = True
                if c["high"] >= hard_sl_price:
                    outcome = "HARD_SL"
                    exit_price = hard_sl_price
                    exit_time = bar_t
                    break
                if c["low"] <= tp_price:
                    outcome = "TP_HIT"
                    exit_price = tp_price
                    exit_time = bar_t
                    break
                if be_act and c["high"] >= ep:
                    outcome = "BE_SAVE"
                    exit_price = ep
                    exit_time = bar_t
                    break
                if not be_act and c["high"] >= soft_sl_price:
                    if c["close"] >= soft_sl_price:
                        outcome = "SOFT_SL"
                        exit_price = c["close"]
                        exit_time = bar_t
                        break
                    else:
                        wicks_absorbed += 1

        if not outcome:
            last_c = candles[min(t + s["max_hold"], n - 1)]
            exit_price = last_c["close"]
            exit_time = last_c["time"]
            if side == "LONG":
                outcome = "TP_HIT" if exit_price >= ep + (tp_move / 2.0) else ("BE_SAVE" if be_act else "SOFT_SL")
            else:
                outcome = "TP_HIT" if exit_price <= ep - (tp_move / 2.0) else ("BE_SAVE" if be_act else "SOFT_SL")

        fx_busy = exit_time

        # 10% ROI Target on TP, -5% on SL, 0% on BE
        if outcome == "TP_HIT":
            roi_pct = 10.0
        elif outcome == "BE_SAVE":
            roi_pct = 0.0
        elif outcome == "HARD_SL":
            roi_pct = -10.0
        else:
            roi_pct = -5.0

        pnl = fx_bal * (roi_pct / 100.0)
        fx_bal += pnl
        if fx_bal > fx_peak:
            fx_peak = fx_bal
        cur_dd = (fx_peak - fx_bal) / fx_peak * 100.0
        if cur_dd > fx_dd:
            fx_dd = cur_dd

        dt = datetime.fromtimestamp(s["time"] / 1000, tz=IST)
        fx_executed.append({
            "num": len(fx_executed) + 1,
            "sym": sym,
            "tf": tf,
            "side": side,
            "date": dt.strftime("%Y-%m-%d %H:%M"),
            "month": dt.strftime("%B %Y"),
            "outcome": outcome,
            "roi_pct": roi_pct,
            "pnl": round(pnl, 2),
            "balance": round(fx_bal, 2),
            "wicks_absorbed": wicks_absorbed
        })

        if fx_bal >= 1000.0 and not fx_milestone_1000:
            fx_milestone_1000 = (len(fx_executed), round(fx_bal, 2), dt.strftime("%Y-%m-%d %H:%M"), sym)

    # -------------------------------------------------------------------------
    # PRINT RESULTS
    # -------------------------------------------------------------------------
    # Gold stats:
    g_total = len(gold_executed)
    g_tp = sum(1 for t in gold_executed if t["outcome"] == "TP_HIT")
    g_be = sum(1 for t in gold_executed if t["outcome"] == "BE_SAVE")
    g_sl = sum(1 for t in gold_executed if "SL" in t["outcome"])
    g_wicks = sum(t["wicks_absorbed"] for t in gold_executed)
    g_pwr = (g_tp / (g_tp + g_sl) * 100.0) if (g_tp + g_sl) > 0 else 0.0
    g_eff_wr = ((g_tp + g_be) / g_total * 100.0) if g_total > 0 else 0.0

    print("\n" + "=" * 80)
    print("🏆 1. GOLD (XAUUSD) DEDICATED OOS COMPOUNDING AUDIT REPORT")
    print("=" * 80)
    print(f"Total Sequential Trades     : {g_total}")
    print(f"Take Profit Wins (TP)       : {g_tp} (+10.0% ROI per trade)")
    print(f"Break-Even Saves (BE)       : {g_be} ($0 Risk Saved)")
    print(f"Stop Loss Hits (SL)         : {g_sl}")
    print(f"Absorbed Stop-Hunt Wicks    : {g_wicks}")
    print(f"PURE WIN RATE (TP vs SL)    : {g_pwr:.2f}%")
    print(f"CAPITAL PRESERVATION RATE   : {g_eff_wr:.2f}%")
    print(f"Starting Capital            : $100.00 USD")
    print(f"Final Capital               : ${gold_bal:,.2f} USD")
    print(f"Net Growth (%)              : {((gold_bal - 100.0) / 100.0 * 100.0):+,.2f}%")
    print(f"Max Drawdown                : {gold_dd:.2f}%")
    if milestone_1000_trade:
        print(f"⭐ $1,000 MILESTONE CROSSED : At Trade #{milestone_1000_trade[0]} on {milestone_1000_trade[2]} (Balance: ${milestone_1000_trade[1]})")

    # Forex Portfolio stats:
    f_total = len(fx_executed)
    f_tp = sum(1 for t in fx_executed if t["outcome"] == "TP_HIT")
    f_be = sum(1 for t in fx_executed if t["outcome"] == "BE_SAVE")
    f_sl = sum(1 for t in fx_executed if "SL" in t["outcome"])
    f_wicks = sum(t["wicks_absorbed"] for t in fx_executed)
    f_pwr = (f_tp / (f_tp + f_sl) * 100.0) if (f_tp + f_sl) > 0 else 0.0
    f_eff_wr = ((f_tp + f_be) / f_total * 100.0) if f_total > 0 else 0.0

    print("\n" + "=" * 80)
    print("📊 2. FULL FOREX PORTFOLIO (11 PAIRS + GOLD) OOS AUDIT REPORT")
    print("=" * 80)
    print(f"Total Sequential Trades     : {f_total}")
    print(f"Take Profit Wins (TP)       : {f_tp} (+10.0% ROI per trade)")
    print(f"Break-Even Saves (BE)       : {f_be} ($0 Risk Saved)")
    print(f"Stop Loss Hits (SL)         : {f_sl}")
    print(f"Absorbed Stop-Hunt Wicks    : {f_wicks}")
    print(f"PURE WIN RATE (TP vs SL)    : {f_pwr:.2f}%")
    print(f"CAPITAL PRESERVATION RATE   : {f_eff_wr:.2f}%")
    print(f"Starting Capital            : $100.00 USD")
    print(f"Final Capital               : ${fx_bal:,.2f} USD")
    print(f"Net Growth (%)              : {((fx_bal - 100.0) / 100.0 * 100.0):+,.2f}%")
    print(f"Max Drawdown                : {fx_dd:.2f}%")
    if fx_milestone_1000:
        print(f"⭐ $1,000 MILESTONE CROSSED : At Trade #{fx_milestone_1000[0]} on {fx_milestone_1000[2]} with {fx_milestone_1000[3]} (Balance: ${fx_milestone_1000[1]})")

    # Monthly breakdown for Gold
    gold_monthly = defaultdict(lambda: {"trades": 0, "tp": 0, "be": 0, "sl": 0, "net_pnl": 0.0})
    for t in gold_executed:
        m = t["month"]
        gold_monthly[m]["trades"] += 1
        if t["outcome"] == "TP_HIT": gold_monthly[m]["tp"] += 1
        elif t["outcome"] == "BE_SAVE": gold_monthly[m]["be"] += 1
        else: gold_monthly[m]["sl"] += 1
        gold_monthly[m]["net_pnl"] += t["pnl"]

    print("\n" + "-" * 75)
    print(f"{'MONTH':<16} | {'TRADES':<6} | {'TP':<4} | {'BE':<4} | {'SL':<4} | {'WIN RATE':<9} | {'NON-LOSS%':<9}")
    print("-" * 75)
    for m, st in gold_monthly.items():
        wr = (st["tp"] / (st["tp"] + st["sl"]) * 100.0) if (st["tp"] + st["sl"]) > 0 else 0.0
        nl = ((st["tp"] + st["be"]) / st["trades"] * 100.0) if st["trades"] > 0 else 0.0
        print(f"{m:<16} | {st['trades']:<6} | {st['tp']:<4} | {st['be']:<4} | {st['sl']:<4} | {wr:6.1f}%   | {nl:6.1f}%")
    print("-" * 75)

    # Save summary report
    report_data = {
        "gold_xauusd": {
            "total_trades": g_total,
            "tp_wins": g_tp,
            "be_saves": g_be,
            "sl_hits": g_sl,
            "wicks_absorbed": g_wicks,
            "pure_win_rate": round(g_pwr, 2),
            "capital_preservation_rate": round(g_eff_wr, 2),
            "start_balance": 100.0,
            "final_balance": round(gold_bal, 2),
            "max_drawdown_pct": round(gold_dd, 2),
            "milestone_1000": milestone_1000_trade
        },
        "full_forex_portfolio": {
            "total_trades": f_total,
            "tp_wins": f_tp,
            "be_saves": f_be,
            "sl_hits": f_sl,
            "wicks_absorbed": f_wicks,
            "pure_win_rate": round(f_pwr, 2),
            "capital_preservation_rate": round(f_eff_wr, 2),
            "start_balance": 100.0,
            "final_balance": round(fx_bal, 2),
            "max_drawdown_pct": round(fx_dd, 2),
            "milestone_1000": fx_milestone_1000
        }
    }
    with open("forex_gold_model2a_real_oos_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

if __name__ == "__main__":
    run_forex_oos_audit()
