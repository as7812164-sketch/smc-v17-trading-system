import sys
sys.path.append(r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system")
from trace_milestone import executed

cap = 50.0
vault = 0.0
hit_1k = None
hit_2k = None

for idx, trade in enumerate(executed):
    net_move = trade["gross"] - 0.0016
    pos = cap * 5.0
    pnl = pos * net_move
    if trade["res"] == "WIN":
        cap += (pnl * 0.85)
        vault += (pnl * 0.15)
    else:
        cap += pnl
    tot = cap + vault

    if tot >= 1000.0 and hit_1k is None:
        hit_1k = idx + 1
        print(f"--> HIT $1,000 AT TRADE #{hit_1k}: cap=${cap:,.2f}, vault=${vault:,.2f}, tot=${tot:,.2f}")
    if tot >= 2000.0 and hit_2k is None:
        hit_2k = idx + 1
        print(f"--> HIT $2,000 AT TRADE #{hit_2k}: cap=${cap:,.2f}, vault=${vault:,.2f}, tot=${tot:,.2f}")

print(f"Summary: Total Trades={len(executed)}, Final Equity=${tot:,.2f}, hit_1k={hit_1k}, hit_2k={hit_2k}")
