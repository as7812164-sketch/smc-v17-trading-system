import json
import sys

with open("pure_touch_1to3_audit_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

mode_a = data["mode_a_per_coin"]

# ---------------------------------------------------------
# 1. TEST 1 (40 TRADES - STRICT 2 TRADES PER COIN)
# ---------------------------------------------------------
# Compile all 40 trades chronologically
trades_40 = []
for sym, rec in mode_a.items():
    st = rec.get("short_trade")
    lt = rec.get("long_trade")
    if st: trades_40.append(st)
    if lt: trades_40.append(lt)

trades_40.sort(key=lambda t: t["time"])

# Simulate Model 1A: $100 Start, $10 margin per trade, 5x leverage ($50 notional)
# SL = 1.5% spot (0.015 * $50 = $0.75 loss + $0.05 fee = $0.80 loss)
# TP = 4.5% spot (0.045 * $50 = $2.25 profit - $0.05 fee = $2.20 profit)
bal_100_a = 100.0
for t in trades_40:
    if t["outcome"] == "TP_HIT":
        bal_100_a += (50.0 * 0.045) - (50.0 * 0.0010)
    else:
        bal_100_a -= (50.0 * 0.015) + (50.0 * 0.0010)

# Simulate Model 1B: $500 Start Deca Compounding ($50 per section across 10 sections)
# Each trade risks 1 section ($50 margin, 5x leverage = $250 notional)
# SL = 1.5% spot -> $250 * 0.015 = $3.75 loss + $0.25 fee = $4.00 loss
# TP = 4.5% spot -> $250 * 0.045 = $11.25 profit - $0.25 fee = $11.00 profit
sec_b = {i: 50.0 for i in range(1, 11)}
rr_ptr = 1
for t in trades_40:
    s_id = rr_ptr
    rr_ptr = (rr_ptr % 10) + 1
    cur = sec_b[s_id]
    notional = cur * 5.0
    if t["outcome"] == "TP_HIT":
        pnl = notional * 0.045 - (notional * 0.0010)
    else:
        pnl = -(notional * 0.015) - (notional * 0.0010)
    sec_b[s_id] = round(cur + pnl, 2)

total_deca_40 = sum(sec_b.values())

# ---------------------------------------------------------
# 2. TEST 2 (FULL MONTH CONTINUOUS - 544 TRADES)
# ---------------------------------------------------------
# Let's run full month simulation from test_pure_pdh_pdl_touch_1to3
sys.path.insert(0, "scripts")
import test_pure_pdh_pdl_touch_1to3 as eng

_, all_544 = eng.run_pure_touch_audit(sl_pct=0.015)
all_544.sort(key=lambda t: t["time"])

# Simulate Model 2A: Fixed Risk ($10 margin per trade on 5x leverage = $50 notional)
# Starting balance: $100.00
bal_fixed_544 = 100.0
peak_bal_fixed = 100.0
max_dd_fixed = 0.0

for t in all_544:
    if t["outcome"] == "TP_HIT":
        pnl = (50.0 * 0.045) - (50.0 * 0.0010)
    else:
        pnl = -(50.0 * 0.015) - (50.0 * 0.0010)
    bal_fixed_544 += pnl
    if bal_fixed_544 > peak_bal_fixed: peak_bal_fixed = bal_fixed_544
    dd = (peak_bal_fixed - bal_fixed_544) / peak_bal_fixed * 100.0
    if dd > max_dd_fixed: max_dd_fixed = dd

# Simulate Model 2B: Deca Compounding ($500.00 start across 10 sections)
# Each section starts with $50.00 and compounds its own balance at 5x leverage
sec_deca_544 = {i: 50.0 for i in range(1, 11)}
sec_peaks = {i: 50.0 for i in range(1, 11)}
sec_dds = {i: 0.0 for i in range(1, 11)}

rr_ptr = 1
for t in all_544:
    s_id = rr_ptr
    rr_ptr = (rr_ptr % 10) + 1
    cur = sec_deca_544[s_id]
    notional = cur * 5.0
    if t["outcome"] == "TP_HIT":
        pnl = notional * 0.045 - (notional * 0.0010)
    else:
        pnl = -(notional * 0.015) - (notional * 0.0010)
    new_bal = round(max(5.0, cur + pnl), 2)
    sec_deca_544[s_id] = new_bal
    if new_bal > sec_peaks[s_id]: sec_peaks[s_id] = new_bal
    dd = (sec_peaks[s_id] - new_bal) / sec_peaks[s_id] * 100.0
    if dd > sec_dds[s_id]: sec_dds[s_id] = dd

final_deca_544 = sum(sec_deca_544.values())

print("=" * 85)
print("PORTFOLIO PERFORMANCE & FINAL BALANCE REPORT")
print("=" * 85)
print("\n--- TEST 1: STRICT 2 TRADES PER COIN (40 TRADES TOTAL) ---")
print(f"Starting Balance: $100.00 (Fixed $10 Margin) -> Final Balance: ${bal_100_a:.2f} ({((bal_100_a-100)/100*100):+.2f}%)")
print(f"Starting Balance: $500.00 (Deca Compounding) -> Final Balance: ${total_deca_40:.2f} ({((total_deca_40-500)/500*100):+.2f}%)")

print("\n--- TEST 2: FULL MONTH CONTINUOUS (544 TRADES ACROSS AUGUST 2026) ---")
print(f"Model A (Fixed Margin $10 / 5x Leverage on $100 Start):")
print(f"  Starting Balance: $100.00")
print(f"  Final Portfolio Balance: ${bal_fixed_544:.2f} ({((bal_fixed_544-100)/100*100):+.2f}% Growth!)")
print(f"  Max Drawdown: {max_dd_fixed:.2f}%")

print(f"\nModel B (Deca Compounding - $500.00 Start across 10 Sections):")
print(f"  Starting Portfolio Equity: $500.00 ($50.00 x 10 Sections)")
print(f"  Final Portfolio Equity:    ${final_deca_544:.2f} ({((final_deca_544-500)/500*100):+.2f}% Growth!)")
print(f"  Average Section Drawdown:  {sum(sec_dds.values())/10:.2f}%")
print(f"  Section Balances: {[round(v, 1) for v in sec_deca_544.values()]}")
print("=" * 85)
