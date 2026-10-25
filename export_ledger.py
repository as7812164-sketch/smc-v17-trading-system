import json
import csv

with open("godtier_smc_compounding_result.json", "r", encoding="utf-8") as f:
    data = json.load(f)

ledger = data["ledger"]
if ledger:
    keys = list(ledger[0].keys())
    with open("godtier_smc_compounding_ledger.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(ledger)
    print(f"Exported {len(ledger)} trades to godtier_smc_compounding_ledger.csv")

# Print the 100-trade milestone metrics
trades_100 = ledger[:100]
bal_100 = trades_100[-1]["end_balance"]
wins_100 = sum(1 for t in trades_100 if t["is_win"])
losses_100 = sum(1 for t in trades_100 if t["is_loss"])
bes_100 = sum(1 for t in trades_100 if t["is_be"])
dd_100 = max(t["drawdown_pct"] for t in trades_100)

print(f"\n--- 100 TRADES COMPOUNDING MILESTONE ---")
print(f"Start: $50.00 -> After 100 Trades: ${bal_100:.2f}")
print(f"Wins: {wins_100} | Losses: {losses_100} | Breakevens: {bes_100}")
print(f"Win Rate: {(wins_100/100)*100:.1f}%")
print(f"Loss Rate: {(losses_100/100)*100:.1f}%")
print(f"Capital Safety: {(1 - losses_100/100)*100:.1f}%")
print(f"Max Drawdown: {dd_100:.2f}%")
print(f"Net Growth: {((bal_100 - 50)/50)*100:.1f}%\n")
