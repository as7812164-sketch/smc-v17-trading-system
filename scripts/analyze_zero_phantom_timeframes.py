import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.run_hermes30_zero_phantom_audit import unique_events, simulate_execution

print("=" * 80)
print("   ZERO-PHANTOM BREAKDOWN: 4H MACRO SWING VS 1H INTRADAY   ")
print("=" * 80)

print("\n--- 1. 4H TIMEFRAME ONLY (ZERO PHANTOM) ---")
ev_4h = [e for e in unique_events if e['timeframe'] == '4h']
res_4h = simulate_execution(ev_4h, body_close_sl=True, conservative_same_bar=True)
print(f"Total Trades: {res_4h['total_trades']}")
print(f"TP Hits (+15% ROE): {res_4h['tps']}")
print(f"SL Hits (-7.5% ROE): {res_4h['sls']}")
print(f"BE Saves ($0 risk): {res_4h['bes']}")
print(f"Absorbed Stop Hunts: {res_4h['absorbed_wicks']}")
print(f"Win Rate: {res_4h['win_rate']}%")
print(f"Profit Factor: {res_4h['profit_factor']}")
print(f"Final Balance: ${res_4h['final_balance']:,.2f} (from $50 start)")
print(f"Max Drawdown: {res_4h['max_drawdown_pct']}%")

print("\n--- 2. 1H TIMEFRAME ONLY (ZERO PHANTOM) ---")
ev_1h = [e for e in unique_events if e['timeframe'] == '1h']
res_1h = simulate_execution(ev_1h, body_close_sl=True, conservative_same_bar=True)
print(f"Total Trades: {res_1h['total_trades']}")
print(f"TP Hits (+15% ROE): {res_1h['tps']}")
print(f"SL Hits (-7.5% ROE): {res_1h['sls']}")
print(f"BE Saves ($0 risk): {res_1h['bes']}")
print(f"Absorbed Stop Hunts: {res_1h['absorbed_wicks']}")
print(f"Win Rate: {res_1h['win_rate']}%")
print(f"Profit Factor: {res_1h['profit_factor']}")
print(f"Final Balance: ${res_1h['final_balance']:,.2f} (from $50 start)")
print(f"Max Drawdown: {res_1h['max_drawdown_pct']}%")

print("\n--- 3. 10-SECTION MATRIX SIMULATION ($50 x 10 = $500 START) ---")
# 5 Sections 4H (accounts 1-5), 5 Sections 1H (accounts 6-10)
sec_balances = {i: 50.00 for i in range(1, 11)}
sec_busy = {i: 0 for i in range(1, 11)}
sec_trades = []

for ev in unique_events:
    tf = ev["timeframe"]
    cand_sections = list(range(1, 6)) if tf == "4h" else list(range(6, 11))
    
    # Find free section
    allocated = None
    for s_id in cand_sections:
        if ev["tap_time"] >= sec_busy[s_id]:
            allocated = s_id
            break
            
    if not allocated:
        continue # all sections busy
        
    ds = ev["dataset"]
    t_idx = ev["tap_idx"]
    side = ev["side"]
    ep = ev["entry_price"]
    tp = ev["tp_price"]
    soft_sl = ev["soft_sl_price"]
    hard_sl = ev["hard_sl_price"]
    be_trig = ev["be_price"]

    be_locked = False
    outcome = None
    exit_p = ep
    exit_t = ev["tap_time"]

    for k in range(t_idx + 1, len(ds)):
        b = ds[k]
        b_h, b_l, b_c, b_t = float(b["high"]), float(b["low"]), float(b["close"]), b["time"]

        if side == "LONG":
            if not be_locked and b_h >= be_trig:
                be_locked = True
            # Conservative intra-bar
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
            if b_l <= soft_sl:
                if b_c <= soft_sl:
                    outcome = "SOFT_SL"
                    exit_p = b_c
                    exit_t = b_t
                    break
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
                    outcome = "SOFT_SL"
                    exit_p = b_c
                    exit_t = b_t
                    break

    if not outcome:
        continue

    sec_busy[allocated] = exit_t
    mrg = sec_balances[allocated]
    pos = mrg * 5.0
    
    if side == "LONG":
        gross = (exit_p - ep) / ep
    else:
        gross = (ep - exit_p) / ep
        
    net = gross - 0.0010 # 0.10% friction fee
    pnl = pos * net
    sec_balances[allocated] = max(1.0, sec_balances[allocated] + pnl)
    sec_trades.append({
        "section": allocated,
        "tf": tf,
        "outcome": outcome,
        "pnl": pnl
    })

tps_mat = sum(1 for t in sec_trades if t["outcome"] == "TP_HIT")
sls_mat = sum(1 for t in sec_trades if "SL" in t["outcome"])
bes_mat = sum(1 for t in sec_trades if t["outcome"] == "BE_SAVE")
wr_mat = (tps_mat / (tps_mat + sls_mat) * 100.0) if (tps_mat + sls_mat) > 0 else 0.0
total_end_equity = sum(sec_balances.values())

print(f"Matrix Total Trades Executed: {len(sec_trades)}")
print(f"TP Hits (+15% ROE): {tps_mat}")
print(f"SL Hits (-7.5% ROE): {sls_mat}")
print(f"BE Saves ($0 risk): {bes_mat}")
print(f"Matrix Win Rate: {wr_mat:.1f}%")
print(f"Total Starting Equity: $500.00 ($50 x 10 sections)")
print(f"Total Final Equity: ${total_end_equity:,.2f} ({((total_end_equity-500)/500*100):+,.1f}% Return)")
print("Individual Section Balances:")
for s_id in range(1, 11):
    lbl = "4H Macro" if s_id <= 5 else "1H Intraday"
    print(f"  Section {s_id} ({lbl}): ${sec_balances[s_id]:,.2f}")
