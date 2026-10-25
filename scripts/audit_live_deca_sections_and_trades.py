import urllib.request
import json
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

headers = {"User-Agent": "Mozilla/5.0"}

def query_endpoint(url):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"Error querying {url}: {e}")
        return None

def main():
    print("=" * 100)
    print("🔍 LIVE FORENSIC AUDIT: DECA SECTIONS, SETUPS & RECENT TRADES")
    print("=" * 100)

    sections_data = query_endpoint("https://smc-ai-agent.onrender.com/api/deca/sections")
    sections = sections_data.get("sections", sections_data) if isinstance(sections_data, dict) else sections_data
    if isinstance(sections, list):
        print(f"\n[1] DECA SECTIONS STATUS (Total {len(sections)} Sections):")
        print("-" * 100)
        print(f"{'Sec ID':<8} | {'Section Name':<24} | {'Balance':<10} | {'Busy?':<8} | {'Active Symbol':<16} | {'Trades':<8}")
        print("-" * 100)
        blocked_sections = []
        for s in sections:
            s_id = s.get("id")
            name = s.get("name")
            bal = s.get("balance", s.get("current_balance", 0.0))
            busy = s.get("is_busy")
            sym = s.get("active_symbol")
            tr_cnt = s.get("total_trades", s.get("win_count", 0) + s.get("loss_count", 0))
            if busy and not sym:
                blocked_sections.append(s_id)
            print(f"Sec #{s_id:<4} | {str(name):<24} | ${bal:<9.2f} | {str(busy):<8} | {str(sym):<16} | {tr_cnt:<8}")
        if blocked_sections:
            print(f"\n⚠️ WARNING: Sections marked busy without active symbol: {blocked_sections}")
        else:
            print("\n✅ All busy flags match their active symbols!")
    else:
        print("Sections data structure:", sections_data)

    # 2. Open Positions
    positions = query_endpoint("https://smc-ai-agent.onrender.com/api/trade/positions")
    print(f"\n[2] CURRENT OPEN POSITIONS:")
    print("-" * 100)
    pos_list = positions.get("positions", positions) if isinstance(positions, dict) else positions
    if isinstance(pos_list, list):
        for p in pos_list:
            print(f"  #{p.get('id')} | {p.get('symbol')} {p.get('side')} | Entry: ${p.get('entry_price')} | Mark: ${p.get('mark_price') or p.get('current_price')} | PnL: ${p.get('pnl')} ({p.get('roe_pct') or p.get('pnl_pct')}%) | Sec: #{p.get('section_id')}")

    # 3. Trade History
    hist_data = query_endpoint("https://smc-ai-agent.onrender.com/api/trade/history")
    hist = hist_data.get("trades", hist_data.get("history", hist_data)) if isinstance(hist_data, dict) else hist_data
    if isinstance(hist, list):
        print(f"\n[3] RECENT TRADES HISTORY (Last 15):")
        print("-" * 100)
        print(f"{'ID':<6} | {'Symbol':<14} | {'Side':<6} | {'Entry':<12} | {'Exit':<12} | {'PnL ($)':<10} | {'Reason':<16} | {'Exit Time'}")
        print("-" * 100)
        for h in hist[:15]:
            print(f"#{str(h.get('id')):<5} | {str(h.get('symbol')):<14} | {str(h.get('side')):<6} | ${str(h.get('entry_price')):<11} | ${str(h.get('exit_price')):<11} | ${str(h.get('pnl')):<9} | {str(h.get('exit_reason')):<16} | {str(h.get('exit_time'))}")
    else:
        print("Hist data structure:", hist_data)

    # 4. Setups Radar
    setups_data = query_endpoint("https://smc-ai-agent.onrender.com/api/deca/setups")
    setups = setups_data.get("setups", setups_data) if isinstance(setups_data, dict) else setups_data
    if isinstance(setups, list):
        print(f"\n[4] LIVE BB SETUPS RADAR (Top 10 Active Candidates):")
        print("-" * 100)
        for st in setups[:10]:
            print(f"  {str(st.get('symbol')):<14} | {str(st.get('side')):<6} | Status: {str(st.get('status')):<12} | Dist: {str(st.get('distance_pct')):<6}% | Sec: #{str(st.get('section_id'))}")
    else:
        print("Setups data structure:", setups_data)

if __name__ == "__main__":
    main()
