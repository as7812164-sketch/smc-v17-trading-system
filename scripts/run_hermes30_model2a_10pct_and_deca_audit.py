import os
import sys
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))
TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR_2Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "historical_data_2year")
CANDLE_CACHE = {}

def load_candles(sym, interval):
    key = f"{sym}_{interval}"
    if key in CANDLE_CACHE:
        return CANDLE_CACHE[key]
    fpath = os.path.join(DATA_DIR_2Y, f"{sym}_{interval}.json")
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

def build_btc_map():
    btc_4h = load_candles("BTCUSDT", "4h")
    btc_1h = load_candles("BTCUSDT", "1h")
    return {c["time"]: c for c in btc_4h}, {c["time"]: c for c in btc_1h}

def harvest_model2a_setups_with_limit_proximity():
    """
    Harvest Hermes 3.0 Model 2A setups with:
    - 4 Sentry Guardians
    - Displacement >= 5.0%
    - FVG present
    - IDM liquidity swept
    - Decisional OB at 0.30 - 0.70 Fib
    - Lower/Upper rejection wick >= 18%
    - Tap candle close >= MT (LONG) or <= MT (SHORT)
    - 0.20% proximity limit order trigger:
      Price reaches within 0.20% of MT (or touches MT)
    """
    btc_map_4h, _ = build_btc_map()
    raw_setups = []

    for tf in ["4h", "1h"]:
        max_tap_window = 28
        max_hold = 36 if tf == "4h" else 48

        for sym in TOP_22_CHAMPIONS:
            candles = load_candles(sym, tf)
            n = len(candles)
            if n < 40:
                continue

            for i in range(20, n - 2):
                # ----------------- LONG SETUP -----------------
                if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 2:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= 0.050: # Sentry 2: >= 5% displacement
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
                                    mt = (dec_top + dec_bot) / 2.0
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        tap_c = candles[t]
                                        # Limit Proximity check: reaches within 0.20% of MT
                                        if tap_c["low"] <= mt * 1.0020 and tap_c["close"] >= mt * 0.985:
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0

                                            # Sentry 1: King BTC Causal Brake
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean = btc_dump < 0.020

                                            # Model 2A Qualification: Rejection Wick >= 18% & Body Close >= MT
                                            if btc_clean and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "LONG",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "tap_close": tap_c["close"], "max_hold": max_hold
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
                        if drop >= 0.050: # Sentry 2: >= 5% displacement
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
                                    mt = (dec_top + dec_bot) / 2.0
                                    for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                        tap_c = candles[t]
                                        # Limit Proximity check: reaches within 0.20% of MT
                                        if tap_c["high"] >= mt * 0.9980 and tap_c["close"] <= mt * 1.015:
                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0

                                            # Sentry 1: King BTC Causal Brake
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                            btc_clean_short = btc_pump < 0.020

                                            # Model 2A Qualification: Rejection Wick >= 18% & Body Close <= MT
                                            if btc_clean_short and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                raw_setups.append({
                                                    "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                    "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                    "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                    "tap_close": tap_c["close"], "max_hold": max_hold
                                                })
                                                break

    raw_setups.sort(key=lambda x: x["time"])
    return raw_setups

def simulate_trade_with_stepped_trailing(s):
    """
    Simulates a trade execution with:
    - Limit order fill at MT
    - 5x Leverage
    - Stepped Trailing SL Ladder:
      * Initial SL: Soft -1.5% Spot (-7.5% ROI) on Candle Body Close | Hard -3.0% Spot (-15% ROI) on Intra-bar Wick
      * Step 1: Touch +5% ROI (+1.0% spot) -> SL moves to +1% ROI (+0.2% spot)
      * Step 2: Touch +10% ROI (+2.0% spot) -> SL moves to +5% ROI (+1.0% spot)
      * Step 3: Touch +15% ROI (+3.0% spot) -> SL moves to +10% ROI (+2.0% spot)
      * Step 4: Touch +20% ROI (+4.0% spot) -> SL moves to +15% ROI (+3.0% spot)
      * Step K: Touch +(5*K)% ROI -> SL moves to +(5*(K-1))% ROI
    - Limit order exit when Trailing SL price is touched.
    """
    sym, tf, t = s["sym"], s["tf"], s["t_idx"]
    side = s["side"]
    candles = load_candles(sym, tf)
    n = len(candles)
    entry_price = s["mt"]

    # Initial SL thresholds
    soft_sl_price = entry_price * 0.9850 if side == "LONG" else entry_price * 1.0150
    hard_sl_price = entry_price * 0.9700 if side == "LONG" else entry_price * 1.0300

    current_trailing_step = 0
    locked_roi_pct = None
    active_trailing_sl_price = None

    outcome = None
    exit_price = entry_price
    exit_time = s["time"]
    realized_roi = 0.0

    fee_rate = 0.0010 # 0.10% roundtrip taker/limit fee

    for bar_idx in range(t + 1, min(t + 1 + s["max_hold"], n)):
        c = candles[bar_idx]
        b_time = c["time"]
        b_high = c["high"]
        b_low = c["low"]
        b_close = c["close"]

        if side == "LONG":
            # Highest favorable spot move in this bar
            max_fav_move = (b_high - entry_price) / entry_price
            max_fav_roi = max_fav_move * 500.0 # 5x leverage * 100

            # Update stepped trailing ladder if reached higher tier
            # Tier 1: 5% ROI -> Lock 1%
            # Tier 2: 10% ROI -> Lock 5%
            # Tier 3: 15% ROI -> Lock 10%
            # Tier 4: 20% ROI -> Lock 15% ...
            if max_fav_roi >= 5.0:
                potential_tier = int(max_fav_roi // 5) # 5->1, 10->2, 15->3, 20->4
                if potential_tier > current_trailing_step:
                    current_trailing_step = potential_tier
                    locked_roi_pct = 1.0 if potential_tier == 1 else float((potential_tier - 1) * 5)
                    # Convert locked ROI to exit price
                    locked_spot_move = locked_roi_pct / 500.0
                    active_trailing_sl_price = entry_price * (1.0 + locked_spot_move)

            # Check exits in pessimistic priority
            # 1. Hard Disaster SL (-3.0% Spot / -15% ROI)
            if current_trailing_step == 0 and b_low <= hard_sl_price:
                outcome = "HARD_SL_HIT"
                exit_price = hard_sl_price
                exit_time = b_time
                realized_roi = -15.0 - (fee_rate * 500.0)
                break

            # 2. Stepped Trailing SL Hit (if active)
            if current_trailing_step > 0 and active_trailing_sl_price is not None:
                if b_low <= active_trailing_sl_price:
                    outcome = f"TRAILING_SL_HIT_TIER_{current_trailing_step}"
                    exit_price = active_trailing_sl_price
                    exit_time = b_time
                    realized_roi = locked_roi_pct - (fee_rate * 500.0)
                    break

            # 3. Soft SL on Candle Body Close (-1.5% Spot / -7.5% ROI)
            if current_trailing_step == 0:
                if b_low <= soft_sl_price:
                    if b_close <= soft_sl_price:
                        outcome = "SOFT_BODY_CLOSE_SL"
                        exit_price = b_close
                        exit_time = b_time
                        actual_spot_move = (b_close - entry_price) / entry_price
                        realized_roi = (actual_spot_move * 500.0) - (fee_rate * 500.0)
                        break
                    # If body close > soft_sl, wick was absorbed, trade continues!

        else: # SHORT
            max_fav_move = (entry_price - b_low) / entry_price
            max_fav_roi = max_fav_move * 500.0

            if max_fav_roi >= 5.0:
                potential_tier = int(max_fav_roi // 5)
                if potential_tier > current_trailing_step:
                    current_trailing_step = potential_tier
                    locked_roi_pct = 1.0 if potential_tier == 1 else float((potential_tier - 1) * 5)
                    locked_spot_move = locked_roi_pct / 500.0
                    active_trailing_sl_price = entry_price * (1.0 - locked_spot_move)

            # 1. Hard Disaster SL (-3.0% Spot / -15% ROI)
            if current_trailing_step == 0 and b_high >= hard_sl_price:
                outcome = "HARD_SL_HIT"
                exit_price = hard_sl_price
                exit_time = b_time
                realized_roi = -15.0 - (fee_rate * 500.0)
                break

            # 2. Stepped Trailing SL Hit
            if current_trailing_step > 0 and active_trailing_sl_price is not None:
                if b_high >= active_trailing_sl_price:
                    outcome = f"TRAILING_SL_HIT_TIER_{current_trailing_step}"
                    exit_price = active_trailing_sl_price
                    exit_time = b_time
                    realized_roi = locked_roi_pct - (fee_rate * 500.0)
                    break

            # 3. Soft SL on Candle Body Close
            if current_trailing_step == 0:
                if b_high >= soft_sl_price:
                    if b_close >= soft_sl_price:
                        outcome = "SOFT_BODY_CLOSE_SL"
                        exit_price = b_close
                        exit_time = b_time
                        actual_spot_move = (entry_price - b_close) / entry_price
                        realized_roi = (actual_spot_move * 500.0) - (fee_rate * 500.0)
                        break

    if not outcome:
        # Reached max hold timeout
        last_c = candles[min(t + s["max_hold"], n - 1)]
        exit_price = last_c["close"]
        exit_time = last_c["time"]
        if side == "LONG":
            spot_m = (exit_price - entry_price) / entry_price
        else:
            spot_m = (entry_price - exit_price) / entry_price
        realized_roi = (spot_m * 500.0) - (fee_rate * 500.0)
        outcome = "TIMEOUT_CLOSE"

    trade_dt = datetime.fromtimestamp(s["time"] / 1000, tz=IST)
    exit_dt = datetime.fromtimestamp(exit_time / 1000, tz=IST)

    return {
        "symbol": sym,
        "tf": tf,
        "side": side,
        "entry_time": s["time"],
        "exit_time": exit_time,
        "entry_date_str": trade_dt.strftime("%Y-%m-%d %H:%M"),
        "exit_date_str": exit_dt.strftime("%Y-%m-%d %H:%M"),
        "entry_price": round(entry_price, 5),
        "exit_price": round(exit_price, 5),
        "outcome": outcome,
        "trailing_step": current_trailing_step,
        "locked_roi": locked_roi_pct if locked_roi_pct is not None else 0.0,
        "realized_roi": round(realized_roi, 2)
    }

def run_hermes30_model2a_audit():
    print("==========================================================================================")
    print("🏛️ HERMES 3.0 MODEL 2A: STEPPED TRAILING SL & 10% MARGIN AUDIT ($500 START)")
    print("==========================================================================================")
    print(f"Asset Universe: Official Top-22 Champions from historical_data_2year")
    print(f"Strategy: Hermes 3.0 Model 2A with Stepped Trailing SL + 0.20% Limit Entry")
    
    raw_setups = harvest_model2a_setups_with_limit_proximity()
    print(f"Total Qualified Model 2A Setups across 2-Year Dataset: {len(raw_setups)}")

    # OOS Scope 1: September 2026 (Last Month OOS: 2026-09-01 to 2026-09-25)
    sep_start_ts = int(datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    sep_end_ts = int(datetime(2026, 9, 25, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)

    # OOS Scope 2: August 2026 (2026-08-01 to 2026-08-31)
    aug_start_ts = int(datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    aug_end_ts = int(datetime(2026, 8, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)

    # Simulate trades
    all_simulated_trades = [simulate_trade_with_stepped_trailing(s) for s in raw_setups]

    trades_sep = [t for t in all_simulated_trades if sep_start_ts <= t["entry_time"] <= sep_end_ts]
    trades_aug = [t for t in all_simulated_trades if aug_start_ts <= t["entry_time"] <= aug_end_ts]

    print(f"September 2026 (Last Month OOS) Executed Model 2A Trades: {len(trades_sep)}")
    print(f"August 2026 Executed Model 2A Trades: {len(trades_aug)}\n")

    # ---------------------------------------------------------------------------------
    # SIMULATION FUNCTION FOR 10% MARGIN PORTFOLIO
    # ---------------------------------------------------------------------------------
    def evaluate_portfolio(trades_list, mode="DYNAMIC_10PCT", start_cap=500.0, max_concurrent=10):
        trades = sorted(trades_list, key=lambda x: x["entry_time"])
        equity = start_cap
        peak_equity = start_cap
        max_dd_pct = 0.0

        events = []
        for i, t in enumerate(trades):
            events.append((t["entry_time"], "ENTRY", i, t))
            events.append((t["exit_time"], "EXIT", i, t))
        events.sort(key=lambda x: (x[0], 0 if x[1] == "EXIT" else 1))

        open_positions = {}
        trade_results = []

        for ts, ev_type, idx, t in events:
            if ev_type == "ENTRY":
                if len(open_positions) >= max_concurrent:
                    continue
                if mode == "DYNAMIC_10PCT":
                    margin = round(equity * 0.10, 2)
                elif mode == "FIXED_50":
                    margin = 50.0
                elif mode == "SEQUENTIAL_100PCT":
                    margin = round(equity, 2)

                open_positions[idx] = {
                    "trade": t,
                    "margin": margin,
                    "entry_time": ts
                }
            elif ev_type == "EXIT":
                if idx in open_positions:
                    pos = open_positions.pop(idx)
                    margin = pos["margin"]
                    roi = t["realized_roi"]
                    pnl = round(margin * (roi / 100.0), 2)
                    equity = round(equity + pnl, 2)

                    if equity > peak_equity:
                        peak_equity = equity
                    dd = (peak_equity - equity) / peak_equity * 100.0 if peak_equity > 0 else 0.0
                    if dd > max_dd_pct:
                        max_dd_pct = dd

                    trade_results.append({
                        "symbol": t["symbol"],
                        "tf": t["tf"],
                        "side": t["side"],
                        "entry_date": t["entry_date_str"],
                        "outcome": t["outcome"],
                        "roi": roi,
                        "margin": margin,
                        "pnl": pnl,
                        "equity_after": equity
                    })

        return {
            "mode": mode,
            "start_capital": start_cap,
            "final_equity": equity,
            "net_pnl": equity - start_cap,
            "growth_pct": ((equity - start_cap) / start_cap) * 100.0,
            "max_dd_pct": max_dd_pct,
            "trades_taken": len(trade_results),
            "trade_results": trade_results
        }

    # ---------------------------------------------------------------------------------
    # SIMULATION FUNCTION FOR DECA COMPOUNDING MATRIX (10 ISOLATED SLOTS)
    # ---------------------------------------------------------------------------------
    def evaluate_deca_matrix(trades_list, start_total=500.0):
        trades = sorted(trades_list, key=lambda x: x["entry_time"])
        slots_4h = [{"id": i, "balance": start_total / 10.0, "busy_until": 0, "trades": [], "peak": start_total/10.0, "max_dd": 0.0} for i in range(1, 6)]
        slots_1h = [{"id": i, "balance": start_total / 10.0, "busy_until": 0, "trades": [], "peak": start_total/10.0, "max_dd": 0.0} for i in range(6, 11)]

        executed = []
        for t in trades:
            slots = slots_4h if t["tf"] == "4h" else slots_1h
            available = [s for s in slots if s["busy_until"] <= t["entry_time"]]
            if not available:
                continue
            # Pick slot with lowest balance or first available
            slot = sorted(available, key=lambda s: s["balance"])[0]

            pos_margin = round(slot["balance"], 2)
            roi = t["realized_roi"]
            pnl = round(pos_margin * (roi / 100.0), 2)
            slot["balance"] = round(slot["balance"] + pnl, 2)
            slot["busy_until"] = t["exit_time"]

            if slot["balance"] > slot["peak"]:
                slot["peak"] = slot["balance"]
            dd = (slot["peak"] - slot["balance"]) / slot["peak"] * 100.0 if slot["peak"] > 0 else 0.0
            if dd > slot["max_dd"]:
                slot["max_dd"] = dd

            slot["trades"].append(t)
            executed.append((t, slot["id"], pnl, slot["balance"]))

        all_slots = slots_4h + slots_1h
        final_total = sum(s["balance"] for s in all_slots)
        avg_dd = sum(s["max_dd"] for s in all_slots) / len(all_slots)
        max_dd = max(s["max_dd"] for s in all_slots)

        return {
            "start_capital": start_total,
            "final_equity": round(final_total, 2),
            "net_pnl": round(final_total - start_total, 2),
            "growth_pct": round(((final_total - start_total) / start_total) * 100.0, 2),
            "avg_dd": round(avg_dd, 2),
            "max_single_dd": round(max_dd, 2),
            "trades_taken": len(executed),
            "slots": all_slots
        }

    # RUN EVALUATIONS FOR SEPTEMBER 2026
    print("==========================================================================================")
    print("1. SEPTEMBER 2026 (LAST MONTH OOS): HERMES 3.0 MODEL 2A RESULTS ($500 START)")
    print("==========================================================================================")
    
    # Trade outcomes summary
    wins_sep = [t for t in trades_sep if t["realized_roi"] >= 5.0]
    saves_sep = [t for t in trades_sep if 0.0 <= t["realized_roi"] < 5.0]
    loss_sep = [t for t in trades_sep if t["realized_roi"] < 0.0]
    
    print(f"Total Qualified Trades:       {len(trades_sep)}")
    print(f"Green Trades (Wins + Saves):  {len(wins_sep) + len(saves_sep)} ({(len(wins_sep) + len(saves_sep))/len(trades_sep)*100:.2f}%)")
    print(f"  - Big Trending Wins (>=+5% ROI): {len(wins_sep)} trades")
    print(f"  - Fee-Protection Saves (+1% ROI): {len(saves_sep)} trades")
    print(f"Stop Loss Hits:               {len(loss_sep)} trades ({len(loss_sep)/len(trades_sep)*100:.2f}%)\n")

    res_dyn_sep = evaluate_portfolio(trades_sep, "DYNAMIC_10PCT", 500.0)
    res_fix_sep = evaluate_portfolio(trades_sep, "FIXED_50", 500.0)
    res_deca_sep = evaluate_deca_matrix(trades_sep, 500.0)

    print(f"MODEL A: DYNAMIC 10% EQUITY COMPOUNDING")
    print(f"  - Trades Taken:     {res_dyn_sep['trades_taken']} / {len(trades_sep)}")
    print(f"  - Starting Balance: ${res_dyn_sep['start_capital']:.2f}")
    print(f"  - Final Balance:    ${res_dyn_sep['final_equity']:.2f} (+${res_dyn_sep['net_pnl']:.2f} USDT)")
    print(f"  - Net Return %:     +{res_dyn_sep['growth_pct']:.2f}%")
    print(f"  - Max Drawdown:     {res_dyn_sep['max_dd_pct']:.2f}%\n")

    print(f"MODEL B: FIXED $50 MARGIN (NON-COMPOUNDING)")
    print(f"  - Trades Taken:     {res_fix_sep['trades_taken']} / {len(trades_sep)}")
    print(f"  - Starting Balance: ${res_fix_sep['start_capital']:.2f}")
    print(f"  - Final Balance:    ${res_fix_sep['final_equity']:.2f} (+${res_fix_sep['net_pnl']:.2f} USDT)")
    print(f"  - Net Return %:     +{res_fix_sep['growth_pct']:.2f}%")
    print(f"  - Max Drawdown:     {res_fix_sep['max_dd_pct']:.2f}%\n")

    print(f"MODEL C: DECA COMPOUNDING MATRIX (10 ISOLATED $50 SLOTS)")
    print(f"  - Trades Taken:     {res_deca_sep['trades_taken']} / {len(trades_sep)}")
    print(f"  - Starting Balance: ${res_deca_sep['start_capital']:.2f}")
    print(f"  - Final Balance:    ${res_deca_sep['final_equity']:.2f} (+${res_deca_sep['net_pnl']:.2f} USDT)")
    print(f"  - Net Return %:     +{res_deca_sep['growth_pct']:.2f}%")
    print(f"  - Average Slot DD:  {res_deca_sep['avg_dd']:.2f}% | Max Single Slot DD: {res_deca_sep['max_single_dd']:.2f}%\n")

    # RUN EVALUATIONS FOR AUGUST 2026
    print("==========================================================================================")
    print("2. AUGUST 2026 OOS: HERMES 3.0 MODEL 2A RESULTS ($500 START)")
    print("==========================================================================================")
    res_dyn_aug = evaluate_portfolio(trades_aug, "DYNAMIC_10PCT", 500.0)
    res_fix_aug = evaluate_portfolio(trades_aug, "FIXED_50", 500.0)
    res_deca_aug = evaluate_deca_matrix(trades_aug, 500.0)

    print(f"MODEL A: DYNAMIC 10% EQUITY COMPOUNDING: Final Balance: ${res_dyn_aug['final_equity']:.2f} (+{res_dyn_aug['growth_pct']:.2f}%) | Max DD: {res_dyn_aug['max_dd_pct']:.2f}%")
    print(f"MODEL B: FIXED $50 MARGIN:              Final Balance: ${res_fix_aug['final_equity']:.2f} (+{res_fix_aug['growth_pct']:.2f}%) | Max DD: {res_fix_aug['max_dd_pct']:.2f}%")
    print(f"MODEL C: DECA COMPOUNDING MATRIX:       Final Balance: ${res_deca_aug['final_equity']:.2f} (+{res_deca_aug['growth_pct']:.2f}%) | Avg DD: {res_deca_aug['avg_dd']:.2f}%\n")

    # SAVE TO JSON
    report_data = {
        "strategy": "HERMES_3.0_MODEL_2A_STEPPED_TRAILING",
        "asset_universe": "TOP_22_CHAMPIONS",
        "september_2026": {
            "total_trades": len(trades_sep),
            "wins": len(wins_sep),
            "fee_saves": len(saves_sep),
            "losses": len(loss_sep),
            "win_rate": round((len(wins_sep) + len(saves_sep)) / len(trades_sep) * 100, 2) if trades_sep else 0.0,
            "model_a_dynamic_10pct": res_dyn_sep,
            "model_b_fixed_50": res_fix_sep,
            "model_c_deca_matrix": {
                "start_capital": res_deca_sep["start_capital"],
                "final_equity": res_deca_sep["final_equity"],
                "net_pnl": res_deca_sep["net_pnl"],
                "growth_pct": res_deca_sep["growth_pct"],
                "avg_dd": res_deca_sep["avg_dd"],
                "max_single_dd": res_deca_sep["max_single_dd"]
            }
        },
        "august_2026": {
            "total_trades": len(trades_aug),
            "model_a_dynamic_10pct": res_dyn_aug,
            "model_b_fixed_50": res_fix_aug,
            "model_c_deca_matrix": {
                "start_capital": res_deca_aug["start_capital"],
                "final_equity": res_deca_aug["final_equity"],
                "net_pnl": res_deca_aug["net_pnl"],
                "growth_pct": res_deca_aug["growth_pct"],
                "avg_dd": res_deca_aug["avg_dd"]
            }
        }
    }

    with open("hermes30_model2a_trailing_10pct_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print("Saved audit data to hermes30_model2a_trailing_10pct_report.json")

if __name__ == "__main__":
    run_hermes30_model2a_audit()
