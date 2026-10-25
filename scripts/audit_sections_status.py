import json
import urllib.request
import ssl
import sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("DECA COMPOUNDING SECTIONS & EXECUTION READINESS AUDIT")
print("=" * 80)

# 1. Local Sniper Ledger
print("\n--- 1. LOCAL LIVE SNIPER (Telegram Bot Runner) ---")
with open("bb20_shadow_ledger.json", "r", encoding="utf-8") as f:
    bb = json.load(f)

print(f"Total Equity: ${bb.get('total_current_equity', 0.0):.2f} USDT")
active_pos = bb.get("active_positions", {})
print(f"Active Positions in Trade: {len(active_pos)}")
for sym, p in active_pos.items():
    print(f"  ⚡ {sym} ({p.get('side')}) | Entry: ${p.get('mt_entry')} | Current SL: ${p.get('active_sl')} | Section #{p.get('section_id')}")

active_setups = bb.get("active_setups", {})
print(f"\nArmed Pending Limit Setups: {len(active_setups)}")
now = datetime.now(timezone.utc)
for sym, s in active_setups.items():
    armed_at_str = s.get("armed_at", "")
    age_str = ""
    try:
        armed_dt = datetime.fromisoformat(armed_at_str)
        hours_old = (now - armed_dt).total_seconds() / 3600.0
        age_str = f"({hours_old:.1f} hrs ago)"
    except Exception:
        pass
    print(f"  🎯 {sym} ({s.get('side')}) @ 50% MT ${s.get('mt_entry')} | Sec #{s.get('section_id')} {age_str}")

print("\nLocal Section Status (1 to 10):")
for sid, s in sorted(bb.get("sections", {}).items(), key=lambda x: int(x[0])):
    status = s.get("status", "IDLE")
    coins = "/".join(s.get("assigned_coins", []))
    bal = s.get("balance", 0.0)
    print(f"  Section #{sid:<2} ({coins:<18}): Status = {status:<15} | Balance = ${bal:.2f}")

# 2. Live Website Terminal on Render
print("\n--- 2. LIVE WEBSITE TERMINAL (https://nexuspro-terminal.onrender.com) ---")
ctx = ssl._create_unverified_context()
try:
    url = "https://nexuspro-terminal.onrender.com/api/deca/sections"
    req = urllib.request.Request(url, headers={"User-Agent": "Auditor"})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        sec_data = json.loads(r.read().decode())
    
    sections = sec_data.get("sections", [])
    print(f"Total Sections on Render: {len(sections)}")
    for sec in sections:
        sid = sec.get("id")
        coins = sec.get("assigned_coins")
        status = sec.get("status")
        act_sym = sec.get("active_symbol")
        bal = sec.get("current_balance")
        flag = f"[IN TRADE: {act_sym}]" if status == "IN_TRADE" else "READY / IDLE"
        print(f"  Section #{sid:<2} ({coins:<24}): {flag:<22} | Balance = ${bal:.2f}")
except Exception as e:
    print("Error querying Render sections:", e)

# 3. Check Live Open Positions on Render
print("\n--- 3. OPEN POSITIONS ON RENDER ---")
try:
    pos_url = "https://nexuspro-terminal.onrender.com/api/trade/positions"
    req_pos = urllib.request.Request(pos_url, headers={"User-Agent": "Auditor"})
    with urllib.request.urlopen(req_pos, context=ctx, timeout=10) as r:
        pos_data = json.loads(r.read().decode())
    
    pos_list = pos_data.get("positions", [])
    print(f"Active Open Positions on Website: {len(pos_list)}")
    for p in pos_list:
        print(f"  #{p.get('id')} {p.get('symbol')} ({p.get('side')}) | Entry: ${p.get('entry_price')} | Mark: ${p.get('mark_price')} | PnL: ${p.get('unrealized_pnl'):+.2f} ({p.get('pnl_pct'):+.2f}%)")
except Exception as e:
    print("Error querying Render positions:", e)
