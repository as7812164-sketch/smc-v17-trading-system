import urllib.request
import ssl
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
ctx = ssl._create_unverified_context()

print("=" * 80)
print("LIVE BB 3.0 PORTFOLIO AUDIT REPORT")
print("=" * 80)

# 1. Live Render Terminal (nexuspro-terminal.onrender.com)
print("\n--- 1. LIVE RENDER TERMINAL (https://nexuspro-terminal.onrender.com) ---")
try:
    url_sum = "https://nexuspro-terminal.onrender.com/api/deca/summary"
    req = urllib.request.Request(url_sum, headers={"User-Agent": "Verifier"})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        summary = json.loads(r.read().decode())
    
    tot_bal = summary.get("total_balance", 0.0)
    tot_eq = summary.get("total_equity", 0.0)
    u_pnl = summary.get("unrealized_pnl", 0.0)
    tot_pnl = summary.get("total_pnl", 0.0)
    pnl_pct = summary.get("pnl_pct", 0.0)
    trades = summary.get("total_trades", 0)
    wins = summary.get("total_wins", 0)
    losses = summary.get("total_losses", 0)
    wr = summary.get("win_rate", 0.0)
    pos_count = summary.get("active_positions_count", 0)

    print(f"Starting Capital: $500.00 USDT")
    print(f"Total Balance (Cash): ${tot_bal:.2f} USDT")
    print(f"Unrealized PnL: ${u_pnl:+.2f} USDT")
    print(f"Total Portfolio Equity: ${tot_eq:.2f} USDT (Net PnL: ${tot_pnl:+.2f} / +{pnl_pct:.2f}%)")
    print(f"Total Trades: {trades} | Wins: {wins} | Losses: {losses} | Win Rate: {wr:.1f}%")
    print(f"Active Open Positions: {pos_count}")

    url_sec = "https://nexuspro-terminal.onrender.com/api/deca/sections"
    req_sec = urllib.request.Request(url_sec, headers={"User-Agent": "Verifier"})
    with urllib.request.urlopen(req_sec, context=ctx, timeout=10) as r:
        sec_data = json.loads(r.read().decode())
    
    print("\n10-Section Balance Breakdown (Website):")
    for s in sec_data.get("sections", []):
        sid = s.get("id")
        coins = s.get("assigned_coins")
        bal = s.get("current_balance", 0.0)
        pnl = s.get("total_pnl", 0.0)
        print(f"  Section #{sid:<2} ({coins:<25}): Balance = ${bal:>6.2f} (PnL: ${pnl:>+6.2f})")

except Exception as e:
    print("Error querying Render:", e)

# 2. Local Shadow Ledger
print("\n--- 2. LOCAL SHADOW SNIPER LEDGER ---")
try:
    with open("bb20_shadow_ledger.json", "r", encoding="utf-8") as f:
        bb = json.load(f)
    print(f"Total Equity: ${bb.get('total_current_equity', 0.0):.2f} USDT")
    for sid, s in sorted(bb.get("sections", {}).items(), key=lambda x: int(x[0])):
        coins = "/".join(s.get("assigned_coins", []))
        bal = s.get("balance", 0.0)
        print(f"  Section #{sid:<2} ({coins:<18}): ${bal:.2f}")
except Exception as e:
    print("Error reading local ledger:", e)
