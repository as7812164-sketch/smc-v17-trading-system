import os
import sys
import json
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.run_hermes30_zero_phantom_audit import unique_events

print("=" * 85)
print("   HERMES 3.0 MODEL 2A: ATR-BASED STOP LOSS ALGORITHMIC EXPERIMENT   ")
print("=" * 85)
print("Evaluating Dynamic ATR Stop Loss Buffers across 1-Year Top-20 Champion Dataset")
print("Zero Phantom Fills, 0.10% Roundtrip Friction, Sequential Trade Queue")
print("=" * 85)

# Calculate ATR(14) for each bar in dataset
def compute_atr14(candles):
    n = len(candles)
    atrs = [0.0] * n
    trs = [0.0] * n
    for i in range(1, n):
        h = float(candles[i]["high"])
        l = float(candles[i]["low"])
        prev_c = float(candles[i-1]["close"])
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs[i] = tr
        if i >= 14:
            atrs[i] = sum(trs[i-13:i+1]) / 14.0
        else:
            atrs[i] = sum(trs[1:i+1]) / i if i > 0 else tr
    return atrs

# Cache ATRs for each unique dataset
atr_cache = {}
for ev in unique_events:
    ds = ev["dataset"]
    ds_id = id(ds)
    if ds_id not in atr_cache:
        atr_cache[ds_id] = compute_atr14(ds)

# Simulation Engine with configurable SL/TP logic
def run_simulation(events, sl_mode="FIXED_1_5", atr_multiplier=1.0, dynamic_tp=False):
    start_equity = 50.00
    balance = start_equity
    peak_balance = start_equity
    max_drawdown = 0.0

    busy_until = 0
    tps, sls, bes = 0, 0, 0
    absorbed_wicks = 0
    trades = []

    for ev in events:
        t_entry = ev["tap_time"]
        if t_entry < busy_until:
            continue

        ds = ev["dataset"]
        t_idx = ev["tap_idx"]
        side = ev["side"]
        ep = ev["entry_price"]
        ds_atrs = atr_cache[id(ds)]
        atr_val = ds_atrs[t_idx] if t_idx < len(ds_atrs) else (ep * 0.015)
        if atr_val <= 0:
            atr_val = ep * 0.015

        # Determine SL and TP based on mode
        if sl_mode == "FIXED_1_5":
            # Baseline Model 2A: Fixed 1.50% Soft SL, 3.00% TP
            soft_sl_dist = ep * 0.0150
            hard_sl_dist = ep * 0.0300
            tp_dist = ep * 0.0300
            be_trig_dist = ep * 0.0150
        elif sl_mode == "ATR_ENTRY_BUFFER":
            # SL = Entry +- (multiplier * ATR_14)
            soft_sl_dist = atr_multiplier * atr_val
            # Guard soft SL distance between 1.0% and 3.5%
            soft_sl_dist = max(ep * 0.010, min(ep * 0.035, soft_sl_dist))
            hard_sl_dist = soft_sl_dist * 1.5
            be_trig_dist = soft_sl_dist
            tp_dist = (soft_sl_dist * 2.0) if dynamic_tp else (ep * 0.0300)
        elif sl_mode == "ATR_HYBRID_CLAMPED":
            # Clamped ATR buffer around 1.5%: base 1.5% +- 0.35 * ATR
            base_dist = ep * 0.0150
            atr_pct = (atr_val / ep)
            # Adapt: volatile coins get slightly wider SL (up to 2.2%), low vol get 1.2%
            soft_sl_dist = ep * max(0.012, min(0.022, 0.008 + (0.5 * atr_pct)))
            hard_sl_dist = soft_sl_dist * 1.6
            be_trig_dist = soft_sl_dist
            tp_dist = (soft_sl_dist * 2.0) if dynamic_tp else (ep * 0.0300)

        if side == "LONG":
            tp = round(ep + tp_dist, 8)
            soft_sl = round(ep - soft_sl_dist, 8)
            hard_sl = round(ep - hard_sl_dist, 8)
            be_trig = round(ep + be_trig_dist, 8)
        else:
            tp = round(ep - tp_dist, 8)
            soft_sl = round(ep + soft_sl_dist, 8)
            hard_sl = round(ep + hard_sl_dist, 8)
            be_trig = round(ep - be_trig_dist, 8)

        be_locked = False
        outcome = None
        exit_p = ep
        exit_t = t_entry

        for k in range(t_idx + 1, len(ds)):
            b = ds[k]
            b_h, b_l, b_c, b_t = float(b["high"]), float(b["low"]), float(b["close"]), b["time"]

            if side == "LONG":
                if not be_locked and b_h >= be_trig:
                    be_locked = True

                # Pessimistic intra-bar conflict
                if b_h >= tp and b_l <= hard_sl:
                    outcome = "HARD_SL"
                    exit_p = hard_sl
                    exit_t = b_t
                    break

                if b_h >= tp:
                    outcome = "TP_HIT"
                    exit_p = tp
                    exit_t = b_t
                    break

                if b_l <= hard_sl:
                    outcome = "HARD_SL"
                    exit_p = hard_sl
                    exit_t = b_t
                    break

                if be_locked and b_l <= ep:
                    outcome = "BE_SAVE"
                    exit_p = ep
                    exit_t = b_t
                    break

                # Soft SL on Candle Body Close
                if b_l <= soft_sl:
                    if b_c <= soft_sl:
                        outcome = "SOFT_SL_BODY_CLOSE"
                        exit_p = b_c
                        exit_t = b_t
                        break
                    else:
                        absorbed_wicks += 1

            else: # SHORT
                if not be_locked and b_l <= be_trig:
                    be_locked = True

                if b_l <= tp and b_h >= hard_sl:
                    outcome = "HARD_SL"
                    exit_p = hard_sl
                    exit_t = b_t
                    break

                if b_l <= tp:
                    outcome = "TP_HIT"
                    exit_p = tp
                    exit_t = b_t
                    break

                if b_h >= hard_sl:
                    outcome = "HARD_SL"
                    exit_p = hard_sl
                    exit_t = b_t
                    break

                if be_locked and b_h >= ep:
                    outcome = "BE_SAVE"
                    exit_p = ep
                    exit_t = b_t
                    break

                if b_h >= soft_sl:
                    if b_c >= soft_sl:
                        outcome = "SOFT_SL_BODY_CLOSE"
                        exit_p = b_c
                        exit_t = b_t
                        break
                    else:
                        absorbed_wicks += 1

        if not outcome:
            continue

        busy_until = exit_t
        leverage = 5.0
        margin = balance
        pos_size = margin * leverage

        if side == "LONG":
            gross_pct = (exit_p - ep) / ep
        else:
            gross_pct = (ep - exit_p) / ep

        net_pct = gross_pct - 0.0010  # 0.10% friction fee
        pnl = pos_size * net_pct

        balance = max(1.0, balance + pnl)
        if balance > peak_balance:
            peak_balance = balance
        dd = (peak_balance - balance) / peak_balance * 100.0 if peak_balance > 0 else 0.0
        if dd > max_drawdown:
            max_drawdown = dd

        if outcome == "TP_HIT":
            tps += 1
        elif outcome == "BE_SAVE":
            bes += 1
        else:
            sls += 1

        trades.append({
            "symbol": ev["symbol"], "side": side, "tf": ev["timeframe"],
            "outcome": outcome, "pnl": round(pnl, 2), "balance": round(balance, 2)
        })

    completed = tps + sls
    wr = (tps / completed * 100.0) if completed > 0 else 0.0
    g_prof = sum(t["pnl"] for t in trades if t["pnl"] > 0)
    g_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))
    pf = (g_prof / g_loss) if g_loss > 0 else float("inf")

    return {
        "trades_count": len(trades),
        "tp": tps, "sl": sls, "be": bes,
        "win_rate": round(wr, 2),
        "absorbed_wicks": absorbed_wicks,
        "final_balance": round(balance, 2),
        "max_dd": round(max_drawdown, 2),
        "profit_factor": round(pf, 2)
    }

# Run Experiment Across 5 Different Variations
experiments = [
    ("Baseline Model 2A (Fixed 1.50% Soft SL / 3.0% TP)", "FIXED_1_5", 1.0, False),
    ("ATR SL Variant 1: 0.75x ATR Soft SL (TP fixed 3.0%)", "ATR_ENTRY_BUFFER", 0.75, False),
    ("ATR SL Variant 2: 1.00x ATR Soft SL (TP fixed 3.0%)", "ATR_ENTRY_BUFFER", 1.00, False),
    ("ATR SL Variant 3: 1.25x ATR Soft SL (TP fixed 3.0%)", "ATR_ENTRY_BUFFER", 1.25, False),
    ("ATR SL Variant 4: Clamped Dynamic ATR (1.2% - 2.2% SL)", "ATR_HYBRID_CLAMPED", 1.0, False),
    ("ATR SL Variant 5: Pure Dynamic 1:2 R:R (1.0x ATR SL / 2.0x ATR TP)", "ATR_ENTRY_BUFFER", 1.00, True),
]

print(f"\n{'Variation / Model':<48} | {'Trades':<6} | {'TP':<4} | {'SL':<4} | {'BE':<4} | {'Win Rate':<9} | {'Absorbed':<8} | {'PF':<5} | {'Final Equity':<12} | {'Max DD'}")
print("-" * 125)

exp_results = []
for label, mode, mult, dyn_tp in experiments:
    res = run_simulation(unique_events, sl_mode=mode, atr_multiplier=mult, dynamic_tp=dyn_tp)
    exp_results.append((label, res))
    print(f"{label:<48} | {res['trades_count']:<6} | {res['tp']:<4} | {res['sl']:<4} | {res['be']:<4} | {res['win_rate']:<8.1f}% | {res['absorbed_wicks']:<8} | {res['profit_factor']:<5} | ${res['final_balance']:<11,.2f} | {res['max_dd']:.1f}%")

print("=" * 125)

# Save to JSON
with open("atr_sl_experiment_results.json", "w", encoding="utf-8") as f:
    json.dump([{"model": l, "metrics": r} for l, r in exp_results], f, indent=2)
print(" Experiment data saved to atr_sl_experiment_results.json")
