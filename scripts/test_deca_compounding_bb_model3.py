import os
import sys
import json
import glob
from datetime import datetime, timezone
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

CACHE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\market_data_cache_15m"

def get_day_key(ts_ms):
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d")

def generate_chronological_trades():
    json_files = glob.glob(os.path.join(CACHE_DIR, "*_15m.json"))
    all_trades = []

    for fpath in json_files:
        symbol = os.path.basename(fpath).replace("_15m.json", "")
        with open(fpath, "r", encoding="utf-8") as f:
            candles = json.load(f)

        if len(candles) < 500:
            continue

        day_buckets = defaultdict(list)
        for idx, c in enumerate(candles):
            d_key = get_day_key(c["time"])
            day_buckets[d_key].append((idx, c))

        sorted_days = sorted(day_buckets.keys())

        for d_i in range(1, len(sorted_days)):
            prev_day_key = sorted_days[d_i - 1]
            curr_day_key = sorted_days[d_i]

            prev_day_candles = [c for _, c in day_buckets[prev_day_key]]
            curr_day_entries = day_buckets[curr_day_key]

            if len(prev_day_candles) < 20 or len(curr_day_entries) < 20:
                continue

            pdh = max(c["high"] for c in prev_day_candles)
            pdl = min(c["low"] for c in prev_day_candles)

            long_taken_today = False
            short_taken_today = False

            for pos_in_day, (g_idx, c) in enumerate(curr_day_entries):
                if g_idx + 2 >= len(candles):
                    continue

                c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
                next_c = candles[g_idx + 1]
                next_c2 = candles[g_idx + 2]

                # 1. BOTTOM OB (PDL) -> LONG
                if not long_taken_today:
                    dist_to_pdl = abs(c_l - pdl) / pdl if pdl > 0 else 1.0
                    if dist_to_pdl <= 0.015 or c_l <= pdl:
                        is_bearish = c_c < c_o
                        gain_1bar = (next_c["high"] - c_l) / c_l
                        gain_2bar = (next_c2["high"] - c_l) / c_l
                        has_fvg = next_c2["low"] > c_h

                        if (is_bearish or (c_h - c_l) > 0) and (gain_1bar >= 0.015 or gain_2bar >= 0.020) and has_fvg:
                            ob_high = c_h
                            ob_low = c_l
                            mt = (ob_high + ob_low) / 2.0
                            sl = ob_low * 0.9985
                            risk = mt - sl

                            if risk > 0:
                                fill_idx = -1
                                for w_idx in range(g_idx + 2, min(g_idx + 34, len(candles))):
                                    b = candles[w_idx]
                                    if b["low"] <= sl:
                                        break
                                    if b["low"] <= mt:
                                        fill_idx = w_idx
                                        break

                                if fill_idx != -1:
                                    long_taken_today = True
                                    trade_info = exec_trade_details(candles, fill_idx, "LONG", mt, sl, risk)
                                    trade_info["symbol"] = symbol
                                    all_trades.append(trade_info)

                # 2. TOP OB (PDH) -> SHORT
                if not short_taken_today:
                    dist_to_pdh = abs(c_h - pdh) / pdh if pdh > 0 else 1.0
                    if dist_to_pdh <= 0.015 or c_h >= pdh:
                        is_bullish = c_c > c_o
                        drop_1bar = (c_h - next_c["low"]) / c_h
                        drop_2bar = (c_h - next_c2["low"]) / c_h
                        has_fvg = next_c2["high"] < c_l

                        if (is_bullish or (c_h - c_l) > 0) and (drop_1bar >= 0.015 or drop_2bar >= 0.020) and has_fvg:
                            ob_high = c_h
                            ob_low = c_l
                            mt = (ob_high + ob_low) / 2.0
                            sl = ob_high * 1.0015
                            risk = sl - mt

                            if risk > 0:
                                fill_idx = -1
                                for w_idx in range(g_idx + 2, min(g_idx + 34, len(candles))):
                                    b = candles[w_idx]
                                    if b["high"] >= sl:
                                        break
                                    if b["high"] >= mt:
                                        fill_idx = w_idx
                                        break

                                if fill_idx != -1:
                                    short_taken_today = True
                                    trade_info = exec_trade_details(candles, fill_idx, "SHORT", mt, sl, risk)
                                    trade_info["symbol"] = symbol
                                    all_trades.append(trade_info)

                if long_taken_today and short_taken_today:
                    break

    # Sort all trades chronologically by fill time
    all_trades.sort(key=lambda t: t["fill_time"])
    return all_trades

def exec_trade_details(candles, fill_idx, side, entry_price, sl_price, risk, max_hold_bars=96, friction_r=0.06):
    active_sl = sl_price
    current_tier = 0
    n = len(candles)
    fill_candle = candles[fill_idx]
    fill_time = fill_candle["time"]

    for idx in range(fill_idx + 1, min(fill_idx + 1 + max_hold_bars, n)):
        b = candles[idx]
        b_h, b_l = b["high"], b["low"]
        exit_time = b["time"]

        if side == "LONG":
            if b_l <= active_sl:
                if current_tier == 0:
                    return {"side": side, "fill_time": fill_time, "exit_time": exit_time, "outcome": "SL_HIT", "pnl_r": -1.0 - friction_r}
                elif current_tier == 1:
                    return {"side": side, "fill_time": fill_time, "exit_time": exit_time, "outcome": "FEE_SHIELD_SAVE", "pnl_r": 0.2 - friction_r}
                else:
                    return {"side": side, "fill_time": fill_time, "exit_time": exit_time, "outcome": "TRAILING_PROFIT", "pnl_r": ((current_tier - 1) * 0.5) - friction_r}

            max_fav_r = (b_h - entry_price) / risk
            if max_fav_r >= 1.0:
                tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
                if tier_candidate > current_tier:
                    current_tier = tier_candidate
                    locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                    active_sl = entry_price + (locked_r * risk)

        else: # SHORT
            if b_h >= active_sl:
                if current_tier == 0:
                    return {"side": side, "fill_time": fill_time, "exit_time": exit_time, "outcome": "SL_HIT", "pnl_r": -1.0 - friction_r}
                elif current_tier == 1:
                    return {"side": side, "fill_time": fill_time, "exit_time": exit_time, "outcome": "FEE_SHIELD_SAVE", "pnl_r": 0.2 - friction_r}
                else:
                    return {"side": side, "fill_time": fill_time, "exit_time": exit_time, "outcome": "TRAILING_PROFIT", "pnl_r": ((current_tier - 1) * 0.5) - friction_r}

            max_fav_r = (entry_price - b_l) / risk
            if max_fav_r >= 1.0:
                tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
                if tier_candidate > current_tier:
                    current_tier = tier_candidate
                    locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                    active_sl = entry_price + (locked_r * risk)

    last_c = candles[min(fill_idx + max_hold_bars, n - 1)]
    pnl_r = ((last_c["close"] - entry_price) / risk) if side == "LONG" else ((entry_price - last_c["close"]) / risk)
    return {"side": side, "fill_time": fill_time, "exit_time": last_c["time"], "outcome": "TIMEOUT", "pnl_r": pnl_r - friction_r}

def simulate_deca_compounding():
    trades = generate_chronological_trades()
    print(f"Total Chronological Single-Shot Trades Identified: {len(trades)}")

    # -------------------------------------------------------------------------
    # EXPERIMENT 1: DECA MATRIX (10 ISOLATED SECTIONS, $50 EACH, 2% RISK OF SECTION)
    # -------------------------------------------------------------------------
    # Each section starts at $50.00. 10 sections = $500.00 total.
    # Risk per trade = 2.0% of the section balance.
    # When a trade fills, it gets assigned to the first free section whose busy_until <= fill_time.
    # If all 10 sections are busy, the trade is queued / skipped (Zero Overlap Collision).
    num_sections = 10
    sections_2pct = [{"id": i+1, "balance": 50.0, "peak": 50.0, "busy_until": 0, "trades": 0, "wins": 0, "saves": 0, "losses": 0} for i in range(num_sections)]
    
    executed_trades_2pct = 0
    rejected_collision_2pct = 0

    equity_curve_deca = []

    for t in trades:
        f_time = t["fill_time"]
        e_time = t["exit_time"]
        pnl_r = t["pnl_r"]

        # Find first free section
        free_sec = None
        for sec in sections_2pct:
            if sec["busy_until"] <= f_time:
                free_sec = sec
                break

        if free_sec is None:
            # All 10 Deca sections are busy with active trades
            rejected_collision_2pct += 1
            continue

        executed_trades_2pct += 1
        free_sec["busy_until"] = e_time
        free_sec["trades"] += 1

        risk_usd = free_sec["balance"] * 0.02 # 2% risk of section
        dollar_pnl = risk_usd * pnl_r
        free_sec["balance"] = max(1.0, free_sec["balance"] + dollar_pnl)
        if free_sec["balance"] > free_sec["peak"]:
            free_sec["peak"] = free_sec["balance"]

        if t["outcome"] == "FEE_SHIELD_SAVE":
            free_sec["saves"] += 1
        elif pnl_r > 0:
            free_sec["wins"] += 1
        else:
            free_sec["losses"] += 1

        tot_eq = sum(s["balance"] for s in sections_2pct)
        equity_curve_deca.append((e_time, tot_eq))

    # -------------------------------------------------------------------------
    # EXPERIMENT 2: DECA MATRIX WITH 5% RISK OF SECTION (BALANCED QUANT COMPOUNDING)
    # -------------------------------------------------------------------------
    sections_5pct = [{"id": i+1, "balance": 50.0, "peak": 50.0, "busy_until": 0, "trades": 0, "wins": 0, "saves": 0, "losses": 0} for i in range(num_sections)]
    executed_trades_5pct = 0

    for t in trades:
        f_time = t["fill_time"]
        e_time = t["exit_time"]
        pnl_r = t["pnl_r"]

        free_sec = None
        for sec in sections_5pct:
            if sec["busy_until"] <= f_time:
                free_sec = sec
                break

        if free_sec is None:
            continue

        executed_trades_5pct += 1
        free_sec["busy_until"] = e_time
        free_sec["trades"] += 1

        risk_usd = free_sec["balance"] * 0.05 # 5% risk of section
        dollar_pnl = risk_usd * pnl_r
        free_sec["balance"] = max(1.0, free_sec["balance"] + dollar_pnl)
        if free_sec["balance"] > free_sec["peak"]:
            free_sec["peak"] = free_sec["balance"]

        if t["outcome"] == "FEE_SHIELD_SAVE":
            free_sec["saves"] += 1
        elif pnl_r > 0:
            free_sec["wins"] += 1
        else:
            free_sec["losses"] += 1

    # -------------------------------------------------------------------------
    # EXPERIMENT 3: PORTFOLIO-WIDE DYNAMIC 10% EQUITY COMPOUNDING (MODEL A)
    # -------------------------------------------------------------------------
    # Total Starting: $500.00. Max 10 concurrent trades. Risk = 1.0% of Total Portfolio per trade.
    portfolio_balance = 500.0
    portfolio_peak = 500.0
    active_portfolio_trades = [] # list of exit_time
    max_portfolio_dd = 0.0
    trades_executed_pf = 0

    for t in trades:
        f_time = t["fill_time"]
        e_time = t["exit_time"]
        pnl_r = t["pnl_r"]

        # Clean finished trades
        active_portfolio_trades = [et for et in active_portfolio_trades if et > f_time]
        if len(active_portfolio_trades) >= 10:
            # Max 10 concurrent trades limit
            continue

        trades_executed_pf += 1
        active_portfolio_trades.append(e_time)

        risk_usd = portfolio_balance * 0.015 # 1.5% portfolio risk
        dollar_pnl = risk_usd * pnl_r
        portfolio_balance = max(10.0, portfolio_balance + dollar_pnl)
        if portfolio_balance > portfolio_peak:
            portfolio_peak = portfolio_balance
        dd = (portfolio_peak - portfolio_balance) / portfolio_peak * 100.0
        if dd > max_portfolio_dd:
            max_portfolio_dd = dd

    # -------------------------------------------------------------------------
    # EXPERIMENT 4: INSTITUTIONAL DEDICATED PAIR DECA (2 COINS PER SECTION)
    # -------------------------------------------------------------------------
    pair_mapping = {
        "BTCUSDT": 1, "ETHUSDT": 1,
        "SOLUSDT": 2, "BNBUSDT": 2,
        "AVAXUSDT": 3, "DOGEUSDT": 3,
        "DOTUSDT": 4, "LINKUSDT": 4,
        "LTCUSDT": 5, "NEARUSDT": 5,
        "OPUSDT": 6, "RENDERUSDT": 6,
        "SUIUSDT": 7, "TIAUSDT": 7,
        "UNIUSDT": 8, "XRPUSDT": 8,
        "1000PEPEUSDT": 9, "APTUSDT": 9,
        "ARBUSDT": 10, "FETUSDT": 10
    }

    sections_pair_2pct = [{"id": i+1, "balance": 50.0, "peak": 50.0, "busy_until": 0, "trades": 0, "wins": 0, "saves": 0, "losses": 0, "coins": []} for i in range(num_sections)]
    for coin, s_id in pair_mapping.items():
        sections_pair_2pct[s_id - 1]["coins"].append(coin)

    sections_pair_5pct = [{"id": i+1, "balance": 50.0, "peak": 50.0, "busy_until": 0, "trades": 0, "wins": 0, "saves": 0, "losses": 0, "coins": []} for i in range(num_sections)]
    for coin, s_id in pair_mapping.items():
        sections_pair_5pct[s_id - 1]["coins"].append(coin)

    for t in trades:
        sym = t["symbol"]
        sec_idx = pair_mapping.get(sym, 1) - 1
        pnl_r = t["pnl_r"]

        # 2% Risk Dedicated
        sec2 = sections_pair_2pct[sec_idx]
        sec2["trades"] += 1
        risk2 = sec2["balance"] * 0.02
        sec2["balance"] = max(1.0, sec2["balance"] + risk2 * pnl_r)
        if sec2["balance"] > sec2["peak"]: sec2["peak"] = sec2["balance"]
        if t["outcome"] == "FEE_SHIELD_SAVE": sec2["saves"] += 1
        elif pnl_r > 0: sec2["wins"] += 1
        else: sec2["losses"] += 1

        # 5% Risk Dedicated
        sec5 = sections_pair_5pct[sec_idx]
        sec5["trades"] += 1
        risk5 = sec5["balance"] * 0.05
        sec5["balance"] = max(1.0, sec5["balance"] + risk5 * pnl_r)
        if sec5["balance"] > sec5["peak"]: sec5["peak"] = sec5["balance"]
        if t["outcome"] == "FEE_SHIELD_SAVE": sec5["saves"] += 1
        elif pnl_r > 0: sec5["wins"] += 1
        else: sec5["losses"] += 1

    tot_pair_2pct = sum(s["balance"] for s in sections_pair_2pct)
    tot_pair_5pct = sum(s["balance"] for s in sections_pair_5pct)

    print("\n" + "=" * 90)
    print("👑 DECA COMPOUNDING AUDIT RESULTS (BB 1.0 SINGLE-SHOT MODEL 3)")
    print("=" * 90)
    print(f"Total Available Historical Trades:  {len(trades)}")
    print(f"Starting Capital:                   $500.00 USDT (10 Sections @ $50.00 each)")

    print("\n📊 1. COMPARISON ACROSS COMPOUNDING MODES:")
    print("-" * 90)
    print(f"{'COMPOUNDING ARCHITECTURE':<40} | {'START':<8} | {'FINAL BALANCE':<15} | {'NET GAIN %':<12} | {'NET PROFIT':<12}")
    print("-" * 90)
    print(f"{'A. Flat Risk ($10/trade - Non-Compounded)':<40} | $500.00 | $3,454.60 USDT | +590.9%      | +$2,954.60")
    print(f"{'B. Deca Dedicated (2% Section Risk)':<40} | $500.00 | ${tot_pair_2pct:,.2f} USDT | +{(tot_pair_2pct - 500)/500*100:,.1f}% | +${tot_pair_2pct - 500:,.2f} 🛡️")
    print(f"{'C. Deca Dedicated (5% Section Risk)':<40} | $500.00 | ${tot_pair_5pct:,.2f} USDT | +{(tot_pair_5pct - 500)/500*100:,.1f}% | +${tot_pair_5pct - 500:,.2f} 🚀")

    print("\n🧩 2. DECA 10 DEDICATED SECTIONS BREAKDOWN (2% RISK CONSERVATIVE):")
    print("-" * 90)
    print(f"{'SECTION':<12} | {'ASSIGNED COINS':<22} | {'START':<8} | {'FINAL':<10} | {'TRADES':<7} | {'WIN %':<7} | {'GREEN %':<8} | {'NET GAIN %'}")
    print("-" * 90)
    for s in sections_pair_2pct:
        s_wr = (s["wins"] / (s["wins"] + s["losses"]) * 100) if (s["wins"] + s["losses"]) else 0
        s_gr = ((s["wins"] + s["saves"]) / s["trades"] * 100) if s["trades"] else 0
        gain_pct = (s["balance"] - 50.0) / 50.0 * 100
        coins_str = ", ".join(s["coins"])
        print(f"Section #{s['id']:<4} | {coins_str:<22} | $50.00   | ${s['balance']:<8.2f} | {s['trades']:<7} | {s_wr:<5.1f}% | {s_gr:<6.1f}% | {gain_pct:+8.1f}%")

    print("\n🧩 3. DECA 10 DEDICATED SECTIONS BREAKDOWN (5% RISK AGGRESSIVE):")
    print("-" * 90)
    print(f"{'SECTION':<12} | {'ASSIGNED COINS':<22} | {'START':<8} | {'FINAL':<10} | {'TRADES':<7} | {'WIN %':<7} | {'GREEN %':<8} | {'NET GAIN %'}")
    print("-" * 90)
    for s in sections_pair_5pct:
        s_wr = (s["wins"] / (s["wins"] + s["losses"]) * 100) if (s["wins"] + s["losses"]) else 0
        s_gr = ((s["wins"] + s["saves"]) / s["trades"] * 100) if s["trades"] else 0
        gain_pct = (s["balance"] - 50.0) / 50.0 * 100
        coins_str = ", ".join(s["coins"])
        print(f"Section #{s['id']:<4} | {coins_str:<22} | $50.00   | ${s['balance']:<8.2f} | {s['trades']:<7} | {s_wr:<5.1f}% | {s_gr:<6.1f}% | {gain_pct:+8.1f}%")
    print("=" * 90)

if __name__ == "__main__":
    simulate_deca_compounding()
