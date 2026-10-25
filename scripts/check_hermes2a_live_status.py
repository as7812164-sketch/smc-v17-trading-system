import sqlite3
import json
import urllib.request
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def check_local():
    db_path = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\database\smc_v17.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("=" * 85)
    print("🏛️ LOCAL SMC_V17.DB STATUS (HERMES 3.0 MODEL 2A)")
    print("=" * 85)

    c.execute("SELECT id, name, initial_balance, current_balance, total_pnl, win_count, loss_count, mode FROM paper_account WHERE id BETWEEN 1 AND 10")
    secs = c.fetchall()
    print(f"\nDeca Compounding Sections ({len(secs)}):")
    tot_sec_bal = 0.0
    for s in secs:
        tot_sec_bal += s[3] if s[3] else 0.0
        print(f"  Sec #{s[0]:<2} | {s[1]:<24} | Balance: ${s[3]:<8.2f} | PnL: ${s[4]:<+7.2f} | {s[5]}W {s[6]}L | Mode: {s[7]}")
    print(f"Total Sections Current Equity: ${tot_sec_bal:.2f} USDT")

    c.execute("SELECT id, symbol, side, entry_price, sl_price, tp_price, pnl_usdt, pnl_pct, status, account_id, mode, entry_time FROM paper_trades WHERE status='OPEN'")
    open_pos = c.fetchall()
    print(f"\nOpen Paper Trades ({len(open_pos)}):")
    for op in open_pos:
        print(f"  Trade #{op[0]} | {op[1]} {op[2]} | Entry: ${op[3]} | SL: ${op[4]} | TP: ${op[5]} | PnL: ${op[6]} ({op[7]}%) | Sec #{op[9]} | Mode: {op[10]} | Opened: {op[11]}")

    c.execute("SELECT id, symbol, side, entry_price, exit_price, pnl_usdt, pnl_pct, exit_time FROM paper_trades WHERE status='CLOSED' ORDER BY id DESC LIMIT 5")
    closed = c.fetchall()
    print(f"\nRecent Closed Trades (Last 5):")
    for cl in closed:
        print(f"  Trade #{cl[0]} | {cl[1]} {cl[2]} | Entry: ${cl[3]} | Exit: ${cl[4]} | PnL: ${cl[5]} ({cl[6]}%) | Closed: {cl[7]}")

    conn.close()

def check_render():
    print("\n" + "=" * 85)
    print("☁️ LIVE RENDER PRODUCTION STATUS (https://smc-ai-agent.onrender.com)")
    print("=" * 85)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        req = urllib.request.Request("https://smc-ai-agent.onrender.com/api/status", headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            st = json.loads(r.read().decode())
            print(f"  Active Mode     : {st.get('strategy_mode')}")
            print(f"  Active Strategy : {st.get('active_strategy')}")
            print(f"  Paper Balance   : ${st.get('paper_balance')}")
            print(f"  Total Equity    : ${st.get('equity')}")
            print(f"  Open Positions  : {st.get('open_positions_count')}")
            print(f"  Win Rate        : {st.get('win_rate')}%")
            print(f"  Total Trades    : {st.get('total_trades')}")
    except Exception as e:
        print("Error fetching /api/status:", e)

    try:
        req = urllib.request.Request("https://smc-ai-agent.onrender.com/api/trade/positions", headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            pos_data = json.loads(r.read().decode())
            positions = pos_data.get('positions', pos_data) if isinstance(pos_data, dict) else pos_data
            cnt = len(positions) if isinstance(positions, list) else 0
            print(f"\nLive Open Positions ({cnt}):")
            if isinstance(positions, list):
                for p in positions:
                    print(f"  #{p.get('id', p.get('symbol'))} | {p.get('symbol')} {p.get('side')} | Entry: ${p.get('entry_price')} | Mark: ${p.get('mark_price') or p.get('current_price')} | PnL: ${p.get('pnl') or p.get('unrealized_pnl')} ({p.get('roe_pct') or p.get('pnl_pct')}%) | Margin: ${p.get('margin')} | Mode: {p.get('mode', 'HERMES_3.0_MODEL_2A')}")
    except Exception as e:
        print("Error fetching /api/trade/positions:", e)

    try:
        req = urllib.request.Request("https://smc-ai-agent.onrender.com/api/deca/summary", headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            deca = json.loads(r.read().decode())
            print("\nDeca Summary:")
            print(f"  Total Equity: ${deca.get('total_equity')}")
            print(f"  Free Margin : ${deca.get('free_margin')}")
            print(f"  Used Margin : ${deca.get('used_margin')}")
            print(f"  Net Return  : {deca.get('net_return_pct')}%")
            print(f"  Win Rate    : {deca.get('win_rate_pct')}%")
    except Exception as e:
        print("Error fetching /api/deca/summary:", e)

if __name__ == "__main__":
    check_local()
    check_render()
