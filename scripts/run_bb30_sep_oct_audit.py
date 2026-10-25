import os
import sys
import json
import glob
from datetime import datetime, timezone
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

CACHE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\market_data_cache_15m"

CHAMPIONS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT",
    "DOGEUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "NEARUSDT",
    "OPUSDT", "RENDERUSDT", "SUIUSDT", "TIAUSDT", "UNIUSDT",
    "XRPUSDT", "1000PEPEUSDT", "APTUSDT", "ARBUSDT", "FETUSDT"
]

PAIR_MAPPING = {
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

def get_day_key(ts_ms):
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")

def exec_bb30_trade(candles, fill_idx, side, entry_price, sl_price, risk, sym, day_str, max_hold_bars=96, friction_r=0.06):
    active_sl = sl_price
    current_tier = 0
    n = len(candles)
    fill_time = candles[fill_idx]["time"]

    highest_fav_r = 0.0

    for idx in range(fill_idx + 1, min(fill_idx + 1 + max_hold_bars, n)):
        b = candles[idx]
        b_h, b_l = b["high"], b["low"]
        exit_time = b["time"]

        if side == "LONG":
            cur_r = (b_h - entry_price) / risk
            if cur_r > highest_fav_r:
                highest_fav_r = cur_r

            if b_l <= active_sl:
                if current_tier == 0:
                    return {
                        "symbol": sym, "day": day_str, "side": side,
                        "entry": entry_price, "exit": active_sl,
                        "fill_time": fill_time, "exit_time": exit_time,
                        "outcome": "LOSS", "pnl_r": -1.0 - friction_r,
                        "highest_r": highest_fav_r
                    }
                elif current_tier == 1:
                    return {
                        "symbol": sym, "day": day_str, "side": side,
                        "entry": entry_price, "exit": active_sl,
                        "fill_time": fill_time, "exit_time": exit_time,
                        "outcome": "FEE_SHIELD_SAVE", "pnl_r": 0.2 - friction_r,
                        "highest_r": highest_fav_r
                    }
                else:
                    locked_r = (current_tier - 1) * 0.5
                    return {
                        "symbol": sym, "day": day_str, "side": side,
                        "entry": entry_price, "exit": active_sl,
                        "fill_time": fill_time, "exit_time": exit_time,
                        "outcome": "WIN", "pnl_r": locked_r - friction_r,
                        "highest_r": highest_fav_r
                    }

            if cur_r >= 1.0:
                tier_candidate = int((cur_r - 1.0) / 0.5) + 1
                if tier_candidate > current_tier:
                    current_tier = tier_candidate
                    locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                    active_sl = entry_price + (locked_r * risk)

        else: # SHORT
            cur_r = (entry_price - b_l) / risk
            if cur_r > highest_fav_r:
                highest_fav_r = cur_r

            if b_h >= active_sl:
                if current_tier == 0:
                    return {
                        "symbol": sym, "day": day_str, "side": side,
                        "entry": entry_price, "exit": active_sl,
                        "fill_time": fill_time, "exit_time": exit_time,
                        "outcome": "LOSS", "pnl_r": -1.0 - friction_r,
                        "highest_r": highest_fav_r
                    }
                elif current_tier == 1:
                    return {
                        "symbol": sym, "day": day_str, "side": side,
                        "entry": entry_price, "exit": active_sl,
                        "fill_time": fill_time, "exit_time": exit_time,
                        "outcome": "FEE_SHIELD_SAVE", "pnl_r": 0.2 - friction_r,
                        "highest_r": highest_fav_r
                    }
                else:
                    locked_r = (current_tier - 1) * 0.5
                    return {
                        "symbol": sym, "day": day_str, "side": side,
                        "entry": entry_price, "exit": active_sl,
                        "fill_time": fill_time, "exit_time": exit_time,
                        "outcome": "WIN", "pnl_r": locked_r - friction_r,
                        "highest_r": highest_fav_r
                    }

            if cur_r >= 1.0:
                tier_candidate = int((cur_r - 1.0) / 0.5) + 1
                if tier_candidate > current_tier:
                    current_tier = tier_candidate
                    locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                    active_sl = entry_price - (locked_r * risk)

    last_c = candles[min(fill_idx + max_hold_bars, n - 1)]
    pnl_r = ((last_c["close"] - entry_price) / risk) if side == "LONG" else ((entry_price - last_c["close"]) / risk)
    return {
        "symbol": sym, "day": day_str, "side": side,
        "entry": entry_price, "exit": last_c["close"],
        "fill_time": fill_time, "exit_time": last_c["time"],
        "outcome": "WIN" if pnl_r > 0 else "LOSS",
        "pnl_r": pnl_r - friction_r,
        "highest_r": highest_fav_r
    }

def run_audit():
    all_trades = []

    for sym in CHAMPIONS:
        fpath = os.path.join(CACHE_DIR, f"{sym}_15m.json")
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            candles = json.load(f)

        day_buckets = defaultdict(list)
        for idx, c in enumerate(candles):
            d_key = get_day_key(c["time"])
            day_buckets[d_key].append((idx, c))

        sorted_days = sorted(day_buckets.keys())

        for d_i in range(1, len(sorted_days)):
            prev_day_key = sorted_days[d_i - 1]
            curr_day_key = sorted_days[d_i]

            # We care about Sep 2026 and Oct 2026
            if not (curr_day_key.startswith("2026-09") or curr_day_key.startswith("2026-10")):
                continue

            prev_day_candles = [c for _, c in day_buckets[prev_day_key]]
            curr_day_entries = day_buckets[curr_day_key]

            if len(prev_day_candles) < 20 or len(curr_day_entries) < 20:
                continue

            pdh = max(c["high"] for c in prev_day_candles)
            pdl = min(c["low"] for c in prev_day_candles)

            long_taken = False
            short_taken = False

            for pos_in_day, (g_idx, c) in enumerate(curr_day_entries):
                if g_idx + 2 >= len(candles):
                    continue

                c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
                next_c = candles[g_idx + 1]
                next_c2 = candles[g_idx + 2]

                # 1. LONG at PDL
                if not long_taken:
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
                                    long_taken = True
                                    trade = exec_bb30_trade(candles, fill_idx, "LONG", mt, sl, risk, sym, curr_day_key)
                                    all_trades.append(trade)

                # 2. SHORT at PDH
                if not short_taken:
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
                                    short_taken = True
                                    trade = exec_bb30_trade(candles, fill_idx, "SHORT", mt, sl, risk, sym, curr_day_key)
                                    all_trades.append(trade)

                if long_taken and short_taken:
                    break

    all_trades.sort(key=lambda t: t["fill_time"])
    return all_trades

trades = run_audit()

sep_trades = [t for t in trades if t["day"].startswith("2026-09")]
oct_trades = [t for t in trades if t["day"].startswith("2026-10")]

def analyze_set(t_list, label):
    total = len(t_list)
    if total == 0:
        return f"\n=== {label} ===\nNo trades executed."

    wins = [t for t in t_list if t["outcome"] == "WIN"]
    saves = [t for t in t_list if t["outcome"] == "FEE_SHIELD_SAVE"]
    losses = [t for t in t_list if t["outcome"] == "LOSS"]

    pure_wr = (len(wins) / total) * 100
    green_rate = ((len(wins) + len(saves)) / total) * 100
    tot_r = sum(t["pnl_r"] for t in t_list)

    # Deca Compounding simulation starting at $500 ($50 per section, 5% risk)
    sections = {i: {"balance": 50.0, "busy_until": 0, "wins": 0, "saves": 0, "losses": 0, "trades": 0} for i in range(1, 11)}
    
    for t in t_list:
        sec_id = PAIR_MAPPING.get(t["symbol"], 1)
        sec = sections[sec_id]
        if sec["busy_until"] > t["fill_time"]:
            continue
        sec["busy_until"] = t["exit_time"]
        sec["trades"] += 1
        risk_usd = sec["balance"] * 0.05
        dollar_pnl = risk_usd * t["pnl_r"]
        sec["balance"] = max(1.0, round(sec["balance"] + dollar_pnl, 2))
        if t["outcome"] == "WIN": sec["wins"] += 1
        elif t["outcome"] == "FEE_SHIELD_SAVE": sec["saves"] += 1
        else: sec["losses"] += 1

    final_portfolio = sum(s["balance"] for s in sections.values())
    net_profit = final_portfolio - 500.0
    roi = (net_profit / 500.0) * 100

    report = f"\n======================================================\n"
    report += f"📊 {label.upper()} RESULTS\n"
    report += f"======================================================\n"
    report += f"• Total Trades: {total}\n"
    report += f"• Pure Wins: {len(wins)} ({pure_wr:.1f}%)\n"
    report += f"• Fee Shield Saves (+0.2R Breakeven): {len(saves)} (Losses avoided!)\n"
    report += f"• Stop Losses Hit (-1.0R): {len(losses)} ({(len(losses)/total)*100:.1f}%)\n"
    report += f"• Green / Protected Accuracy: {green_rate:.1f}%\n"
    report += f"• Total Net Gain: {tot_r:+.1f} R\n"
    report += f"• Portfolio (Deca 5% Compounding): $500.00 ➔ ${final_portfolio:,.2f} USDT ({roi:+.1f}% Net Return)\n"
    report += f"• Average Win Size: +{sum(w['pnl_r'] for w in wins)/len(wins):.2f} R\n" if wins else ""
    return report

print(analyze_set(sep_trades, "September 2026 Month (Sep 01 - Sep 30)"))
print(analyze_set(oct_trades, "October 2026 Month (Oct 01 - Oct 16)"))
print(analyze_set(trades, "Combined September + October 2026 Overall"))

# Save detailed trades JSON for user reference
with open(r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\scripts\bb30_sep_oct_trades.json", "w", encoding="utf-8") as f:
    json.dump({"september": sep_trades, "october": oct_trades}, f, indent=2)

print("\nTrade details saved to scripts/bb30_sep_oct_trades.json")
