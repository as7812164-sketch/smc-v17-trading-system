import urllib.request
import json
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    url = "https://smc-ai-agent.onrender.com/api/paper/trades"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode())
    
    trades = res if isinstance(res, list) else res.get("trades", [])
    print(f"Total Trades Recorded: {len(trades)}")
    print("-" * 110)
    print(f"{'ID':<5} {'Symbol':<12} {'Side':<6} {'Entry Price':<14} {'Exit Price':<14} {'Realized PnL':<18} {'Result':<16} {'Exit Time (UTC)'}")
    print("-" * 110)
    
    # Sort by exit_time descending
    trades.sort(key=lambda x: x.get("exit_time", x.get("entry_time", 0)), reverse=True)
    
    total_2day_pnl = 0.0
    count_2day = 0
    
    for t in trades:
        ts = t.get("exit_time", t.get("entry_time", 0))
        dt_str = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        pnl = float(t.get("realized_pnl", 0))
        pnl_pct = float(t.get("pnl_pct", 0))
        sym = t.get("symbol", "")
        side = t.get("side", "")
        entry = float(t.get("entry_price", 0))
        exit_p = float(t.get("exit_price", 0))
        res_str = t.get("result", t.get("exit_reason", ""))
        
        # Check if in last 2 days (Oct 13, 14, 15)
        if "2026-10-13" in dt_str or "2026-10-14" in dt_str or "2026-10-15" in dt_str:
            total_2day_pnl += pnl
            count_2day += 1
            print(f"#{t.get('id', 0):<4} {sym:<12} {side:<6} {entry:<14.4f} {exit_p:<14.4f} ${pnl:+8.2f} ({pnl_pct:+6.2f}%)   {res_str:<16} {dt_str}")
            
    print("-" * 110)
    print(f"Recent 2-Day Trades Count: {count_2day}")
    print(f"Total 2-Day Realized PnL: ${total_2day_pnl:+.2f} USDT")

    # Also check current open positions
    url_pos = "https://smc-ai-agent.onrender.com/api/paper/positions"
    req_pos = urllib.request.Request(url_pos, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_pos, timeout=10) as resp:
        res_pos = json.loads(resp.read().decode())
    
    positions = res_pos.get("positions", [])
    print("\n" + "=" * 110)
    print("CURRENT OPEN POSITIONS (HERMES 3.0 MODEL 2A LIVE ENGINE):")
    print("=" * 110)
    if not positions:
        print("No open positions right now.")
    for p in positions:
        print(f"ID #{p.get('id')} | {p.get('symbol')} {p.get('side')} | Entry: ${p.get('entry_price')} | Mark: ${p.get('mark_price')} | Unrealized PnL: ${p.get('unrealized_pnl'):.2f} ({p.get('pnl_pct'):.2f}%) | Size: ${p.get('size_usdt')} | Margin: ${p.get('margin_usdt')}")

    # Check account balance
    url_acc = "https://smc-ai-agent.onrender.com/api/paper/account"
    req_acc = urllib.request.Request(url_acc, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_acc, timeout=10) as resp:
        res_acc = json.loads(resp.read().decode())
    print(f"\nCurrent Paper Balance: ${res_acc.get('balance')} USDT | Total Equity: ${res_acc.get('equity')} USDT | Realized PnL: ${res_acc.get('realized_pnl')} USDT")

except Exception as e:
    print(f"Error: {e}")
