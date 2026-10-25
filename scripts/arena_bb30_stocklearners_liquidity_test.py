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

def exec_stepped_trailing(candles, fill_idx, side, entry_price, sl_price, risk, sym, day_str, step_size=0.5, max_hold_bars=96, friction_r=0.06):
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
            if cur_r > highest_fav_r: highest_fav_r = cur_r

            if b_l <= active_sl:
                if current_tier == 0:
                    return {"symbol": sym, "day": day_str, "side": side, "entry": entry_price, "exit": active_sl, "fill_time": fill_time, "exit_time": exit_time, "outcome": "LOSS", "pnl_r": -1.0 - friction_r, "highest_r": highest_fav_r}
                elif current_tier == 1:
                    return {"symbol": sym, "day": day_str, "side": side, "entry": entry_price, "exit": active_sl, "fill_time": fill_time, "exit_time": exit_time, "outcome": "FEE_SHIELD_SAVE", "pnl_r": 0.2 - friction_r, "highest_r": highest_fav_r}
                else:
                    locked_r = (current_tier - 1) * step_size
                    return {"symbol": sym, "day": day_str, "side": side, "entry": entry_price, "exit": active_sl, "fill_time": fill_time, "exit_time": exit_time, "outcome": "WIN", "pnl_r": locked_r - friction_r, "highest_r": highest_fav_r}

            if cur_r >= 1.0:
                tier_candidate = int((cur_r - 1.0) / step_size) + 1
                if tier_candidate > current_tier:
                    current_tier = tier_candidate
                    locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * step_size
                    active_sl = entry_price + (locked_r * risk)

        else: # SHORT
            cur_r = (entry_price - b_l) / risk
            if cur_r > highest_fav_r: highest_fav_r = cur_r

            if b_h >= active_sl:
                if current_tier == 0:
                    return {"symbol": sym, "day": day_str, "side": side, "entry": entry_price, "exit": active_sl, "fill_time": fill_time, "exit_time": exit_time, "outcome": "LOSS", "pnl_r": -1.0 - friction_r, "highest_r": highest_fav_r}
                elif current_tier == 1:
                    return {"symbol": sym, "day": day_str, "side": side, "entry": entry_price, "exit": active_sl, "fill_time": fill_time, "exit_time": exit_time, "outcome": "FEE_SHIELD_SAVE", "pnl_r": 0.2 - friction_r, "highest_r": highest_fav_r}
                else:
                    locked_r = (current_tier - 1) * step_size
                    return {"symbol": sym, "day": day_str, "side": side, "entry": entry_price, "exit": active_sl, "fill_time": fill_time, "exit_time": exit_time, "outcome": "WIN", "pnl_r": locked_r - friction_r, "highest_r": highest_fav_r}

            if cur_r >= 1.0:
                tier_candidate = int((cur_r - 1.0) / step_size) + 1
                if tier_candidate > current_tier:
                    current_tier = tier_candidate
                    locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * step_size
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

def simulate_strategy_model(mode="BASELINE", pre_min_dist=0.003, pre_max_dist=0.020, displacement=0.012, step_size=0.5):
    """
    mode:
      - BASELINE: BB 3.0 (Sweep or tap within 1.5% of PDL/PDH)
      - PURE_PRE_TURN: Only trades when price turns BEFORE PDL/PDH without ever touching it
      - BIFURCATION: Pre-turn = Long; Touch/Break = Trend Dead (Take Breakdown Short instead)
      - COMBINED_DUAL: Baseline + Pre-Turn Boost
    """
    all_trades = []

    for sym in CHAMPIONS:
        fpath = os.path.join(CACHE_DIR, f"{sym}_15m.json")
        if not os.path.exists(fpath): continue
        with open(fpath, "r", encoding="utf-8") as f: candles = json.load(f)

        day_buckets = defaultdict(list)
        for idx, c in enumerate(candles):
            d_key = get_day_key(c["time"])
            day_buckets[d_key].append((idx, c))

        sorted_days = sorted(day_buckets.keys())

        for d_i in range(1, len(sorted_days)):
            prev_day_key = sorted_days[d_i - 1]
            curr_day_key = sorted_days[d_i]

            # Focus strictly on SEPTEMBER 2026
            if not curr_day_key.startswith("2026-09"):
                continue

            prev_day_candles = [c for _, c in day_buckets[prev_day_key]]
            curr_day_entries = day_buckets[curr_day_key]
            if len(prev_day_candles) < 20 or len(curr_day_entries) < 20: continue

            pdh = max(c["high"] for c in prev_day_candles)
            pdl = min(c["low"] for c in prev_day_candles)

            long_taken = False
            short_taken = False

            for pos_in_day, (g_idx, c) in enumerate(curr_day_entries):
                if g_idx + 2 >= len(candles): continue
                c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
                next_c = candles[g_idx + 1]
                next_c2 = candles[g_idx + 2]

                # ----------------- LONG SCENARIOS -----------------
                if not long_taken:
                    dist_to_pdl = (c_l - pdl) / pdl if pdl > 0 else 1.0

                    # Check displacement & FVG
                    is_bull = (next_c["high"] - c_l) / c_l >= displacement or (next_c2["high"] - c_l) / c_l >= (displacement * 1.5)
                    has_fvg = next_c2["low"] > c_h

                    take_long = False
                    if mode == "BASELINE":
                        # Standard BB 3.0: Price touches PDL or within 1.5%
                        if (c_l <= pdl or abs(c_l - pdl) / pdl <= 0.015) and is_bull and has_fvg:
                            take_long = True
                    elif mode == "PURE_PRE_TURN":
                        # StockLearners Rule: Reverses strictly BEFORE touching PDL (Pre-turn cushion)
                        if pre_min_dist <= dist_to_pdl <= pre_max_dist and c_l > pdl and is_bull and has_fvg:
                            take_long = True
                    elif mode == "BIFURCATION":
                        # If turned before PDL -> Long
                        if pre_min_dist <= dist_to_pdl <= pre_max_dist and c_l > pdl and is_bull and has_fvg:
                            take_long = True
                    elif mode == "COMBINED_DUAL":
                        # Both standard sweep AND pre-turn allowed
                        if ((c_l <= pdl or abs(c_l - pdl) / pdl <= 0.015) or (pre_min_dist <= dist_to_pdl <= pre_max_dist)) and is_bull and has_fvg:
                            take_long = True

                    if take_long:
                        mt = (c_h + c_l) / 2.0
                        sl = c_l * 0.9985
                        risk = mt - sl
                        if risk > 0:
                            for w_idx in range(g_idx + 2, min(g_idx + 34, len(candles))):
                                if candles[w_idx]["low"] <= sl: break
                                if candles[w_idx]["low"] <= mt:
                                    long_taken = True
                                    all_trades.append(exec_stepped_trailing(candles, w_idx, "LONG", mt, sl, risk, sym, curr_day_key, step_size))
                                    break

                # ----------------- SHORT SCENARIOS -----------------
                if not short_taken:
                    dist_to_pdh = (pdh - c_h) / pdh if pdh > 0 else 1.0
                    is_bear = (c_h - next_c["low"]) / c_h >= displacement or (c_h - next_c2["low"]) / c_h >= (displacement * 1.5)
                    has_fvg = next_c2["high"] < c_l

                    take_short = False
                    if mode == "BASELINE":
                        if (c_h >= pdh or abs(c_h - pdh) / pdh <= 0.015) and is_bear and has_fvg:
                            take_short = True
                    elif mode == "PURE_PRE_TURN":
                        if pre_min_dist <= dist_to_pdh <= pre_max_dist and c_h < pdh and is_bear and has_fvg:
                            take_short = True
                    elif mode == "BIFURCATION":
                        # If price touches/breaks PDL downwards, StockLearners says: trend dead, dump to next liquidity!
                        if c_l < pdl and (c_h - next_c["low"]) / c_h >= displacement:
                            take_short = True
                    elif mode == "COMBINED_DUAL":
                        if ((c_h >= pdh or abs(c_h - pdh) / pdh <= 0.015) or (pre_min_dist <= dist_to_pdh <= pre_max_dist)) and is_bear and has_fvg:
                            take_short = True

                    if take_short:
                        mt = (c_h + c_l) / 2.0
                        sl = c_h * 1.0015
                        risk = sl - mt
                        if risk > 0:
                            for w_idx in range(g_idx + 2, min(g_idx + 34, len(candles))):
                                if candles[w_idx]["high"] >= sl: break
                                if candles[w_idx]["high"] >= mt:
                                    short_taken = True
                                    all_trades.append(exec_stepped_trailing(candles, w_idx, "SHORT", mt, sl, risk, sym, curr_day_key, step_size))
                                    break

                if long_taken and short_taken: break

    # Evaluate compounding & metrics
    all_trades.sort(key=lambda t: t["fill_time"])
    tot = len(all_trades)
    if tot == 0:
        return {"trades": 0, "win_rate": 0, "green_rate": 0, "net_r": 0, "final_eq": 500.0, "roi": 0}

    wins = [t for t in all_trades if t["outcome"] == "WIN"]
    saves = [t for t in all_trades if t["outcome"] == "FEE_SHIELD_SAVE"]
    losses = [t for t in all_trades if t["outcome"] == "LOSS"]

    pure_wr = (len(wins) / tot) * 100
    green_rate = ((len(wins) + len(saves)) / tot) * 100
    tot_r = sum(t["pnl_r"] for t in all_trades)

    # 10 Deca Sections ($50 start = $500 total, 5% compounding risk)
    sections = {i: {"balance": 50.0, "busy_until": 0} for i in range(1, 11)}
    for t in all_trades:
        sec = sections[PAIR_MAPPING.get(t["symbol"], 1)]
        if sec["busy_until"] > t["fill_time"]: continue
        sec["busy_until"] = t["exit_time"]
        dollar_pnl = (sec["balance"] * 0.05) * t["pnl_r"]
        sec["balance"] = max(1.0, round(sec["balance"] + dollar_pnl, 2))

    final_eq = sum(s["balance"] for s in sections.values())
    roi = ((final_eq - 500.0) / 500.0) * 100

    return {
        "trades": tot,
        "wins": len(wins),
        "saves": len(saves),
        "losses": len(losses),
        "win_rate": pure_wr,
        "green_rate": green_rate,
        "net_r": tot_r,
        "final_eq": final_eq,
        "roi": roi
    }

print("Running 4 Core Strategic Architectures on September 2026...")
res_base = simulate_strategy_model("BASELINE")
res_pre  = simulate_strategy_model("PURE_PRE_TURN", pre_min_dist=0.003, pre_max_dist=0.025)
res_bif  = simulate_strategy_model("BIFURCATION", pre_min_dist=0.003, pre_max_dist=0.025)
res_dual = simulate_strategy_model("COMBINED_DUAL", pre_min_dist=0.003, pre_max_dist=0.025)

print("\n=========================================================================================")
print("🏆 SEPTEMBER 2026: LIQUIDITY RESPECT vs SWEEP COMPARISON MATRIX")
print("=========================================================================================")
print(f"{'Strategy Architecture':<36} | {'Trades':<6} | {'Win %':<6} | {'Green%':<6} | {'Net R':<8} | {'Final Eq ($500)':<16} | {'Net Return %'}")
print("-" * 100)
print(f"{'1. Baseline BB 3.0 (Sweep/Retest)':<36} | {res_base['trades']:<6} | {res_base['win_rate']:<5.1f}% | {res_base['green_rate']:<5.1f}% | {res_base['net_r']:<+7.1f}R | ${res_base['final_eq']:<15,.2f} | {res_base['roi']:+6.1f}%")
print(f"{'2. Pure StockLearners (Pre-Turn Only)':<36} | {res_pre['trades']:<6} | {res_pre['win_rate']:<5.1f}% | {res_pre['green_rate']:<5.1f}% | {res_pre['net_r']:<+7.1f}R | ${res_pre['final_eq']:<15,.2f} | {res_pre['roi']:+6.1f}%")
print(f"{'3. Bifurcation Model (Pre-Turn + Dump)':<36} | {res_bif['trades']:<6} | {res_bif['win_rate']:<5.1f}% | {res_bif['green_rate']:<5.1f}% | {res_bif['net_r']:<+7.1f}R | ${res_bif['final_eq']:<15,.2f} | {res_bif['roi']:+6.1f}%")
print(f"{'4. Dual-Confluence BB 3.0 + Pre-Turn':<36} | {res_dual['trades']:<6} | {res_dual['win_rate']:<5.1f}% | {res_dual['green_rate']:<5.1f}% | {res_dual['net_r']:<+7.1f}R | ${res_dual['final_eq']:<15,.2f} | {res_dual['roi']:+6.1f}%")
print("=" * 100)

# ----------------- 50-AGENT ARENA SIMULATION -----------------
print("\nInitiating 50-Agent Quantitative Arena Simulation...")
arena_results = []
agent_id = 1

distances = [(0.002, 0.015), (0.003, 0.020), (0.004, 0.025), (0.005, 0.030)]
displacements = [0.010, 0.012, 0.015, 0.018]
step_sizes = [0.4, 0.5, 0.6]

for d_min, d_max in distances:
    for disp in displacements:
        for st in step_sizes:
            if agent_id > 50: break
            name = f"Agent-{agent_id:02d} [D:{d_min*100:.1f}-{d_max*100:.1f}%, Disp:{disp*100:.1f}%, Step:{st}R]"
            r = simulate_strategy_model("COMBINED_DUAL", pre_min_dist=d_min, pre_max_dist=d_max, displacement=disp, step_size=st)
            r["name"] = name
            r["id"] = agent_id
            arena_results.append(r)
            agent_id += 1

# If needed fill up to 50
while len(arena_results) < 50:
    st = 0.5
    disp = 0.012 + (len(arena_results) * 0.0002)
    name = f"Agent-{agent_id:02d} [Disp:{disp*100:.2f}%, Step:{st}R]"
    r = simulate_strategy_model("PURE_PRE_TURN", pre_min_dist=0.003, pre_max_dist=0.022, displacement=disp, step_size=st)
    r["name"] = name
    r["id"] = agent_id
    arena_results.append(r)
    agent_id += 1

arena_results.sort(key=lambda x: x["final_eq"], reverse=True)

print("\n" + "=" * 90)
print("⚔️ 50-AGENT GLADIATOR ARENA LEADERBOARD (TOP 10 CHAMPIONS vs BOTTOM 5)")
print("=" * 90)
print(f"{'Rank':<5} | {'Agent Configuration':<48} | {'Trades':<6} | {'Win%':<6} | {'Green%':<6} | {'Net R':<8} | {'Final Equity'}")
print("-" * 90)
for idx, ag in enumerate(arena_results[:10]):
    print(f"#{idx+1:<4} | {ag['name']:<48} | {ag['trades']:<6} | {ag['win_rate']:<5.1f}% | {ag['green_rate']:<5.1f}% | {ag['net_r']:<+7.1f}R | ${ag['final_eq']:<12,.2f} 👑")

print("...")
for idx, ag in enumerate(arena_results[-5:]):
    rank = len(arena_results) - 4 + idx
    print(f"#{rank:<4} | {ag['name']:<48} | {ag['trades']:<6} | {ag['win_rate']:<5.1f}% | {ag['green_rate']:<5.1f}% | {ag['net_r']:<+7.1f}R | ${ag['final_eq']:<12,.2f}")
print("=" * 90)

# Save Arena JSON
with open(r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\scripts\50_agent_arena_results.json", "w", encoding="utf-8") as f:
    json.dump(arena_results, f, indent=2)

print("\nArena results saved to scripts/50_agent_arena_results.json")
