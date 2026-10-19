import urllib.request
import json

def analyze_all_trades():
    url = "https://smc-ai-agent.onrender.com/api/paper/trades"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    res = urllib.request.urlopen(req, timeout=15)
    data = json.loads(res.read().decode())
    trades = data.get("trades", [])
    print(f"Total trades returned: {len(trades)}")
    
    sec_stats = {i: {"trades": [], "pnl": 0.0, "wins": 0, "losses": 0} for i in range(1, 11)}
    
    for t in trades:
        acc = t.get("account_id")
        ch = str(t.get("channel", ""))
        sec = None
        if acc and 1 <= int(acc) <= 10:
            sec = int(acc)
        elif ch:
            for i in range(1, 11):
                if f"sec_{i}" in ch or f"section_{i}" in ch or f"bitget_4h_{i}" in ch or f"bitget_1h_{i}" in ch:
                    sec = i
                    break
        if not sec:
            sec = 1
            
        pnl = float(t.get("pnl_usdt") or 0.0)
        status = t.get("status", "")
        symbol = t.get("symbol", "")
        tid = t.get("id")
        
        sec_stats[sec]["trades"].append(t)
        sec_stats[sec]["pnl"] += pnl
        if pnl > 0:
            sec_stats[sec]["wins"] += 1
        elif pnl < 0:
            sec_stats[sec]["losses"] += 1
            
        print(f"ID {tid:3d}: {symbol:10} sec={sec:2d} pnl={pnl:+6.2f} ({status})")
        
    print("\n" + "="*60)
    print("EXACT SECTION BY SECTION BREAKDOWN (FROM ALL 62 TRADES):")
    total_balance = 0.0
    total_pnl = 0.0
    total_wins = 0
    total_losses = 0
    for s in range(1, 11):
        init_bal = 50.0
        pnl = round(sec_stats[s]["pnl"], 2)
        bal = round(init_bal + pnl, 2)
        total_balance += bal
        total_pnl += pnl
        w = sec_stats[s]["wins"]
        l = sec_stats[s]["losses"]
        total_wins += w
        total_losses += l
        wr = round((w / (w+l) * 100), 1) if (w+l) > 0 else 0.0
        print(f"Section {s:2d}: Start=$50.00 | PnL={pnl:+6.2f} | Balance=${bal:6.2f} | Wins={w:2d} Losses={l:2d} | WR={wr:5.1f}%")
        
    print("="*60)
    tot_completed = total_wins + total_losses
    overall_wr = round((total_wins / tot_completed * 100), 1) if tot_completed > 0 else 0.0
    print(f"TOTAL COMPLETED TRADES: {tot_completed}")
    print(f"TOTAL REALIZED PNL:     ${round(total_pnl, 2)}")
    print(f"TOTAL PORTFOLIO EQUITY: ${round(total_balance, 2)}")
    print(f"TOTAL WIN RATE:         {overall_wr}% ({total_wins}W {total_losses}L)")
    print("="*60)

if __name__ == "__main__":
    analyze_all_trades()
