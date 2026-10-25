import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = "https://smc-ai-agent.onrender.com"

endpoints = [
    "/trade",
    "/nexus/markets",
    "/nexus/deca",
    "/nexus/assets",
    "/api/trade/positions",
    "/api/trade/history",
    "/api/deca/summary",
    "/api/deca/setups",
    "/api/deca/sections",
    "/api/markets/overview"
]

print(f"=== TESTING PRODUCTION APIS: {BASE_URL} ===")
for ep in endpoints:
    url = f"{BASE_URL}{ep}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = resp.read()
            ct = resp.headers.get('Content-Type', '')
            print(f"\n[OK 200] {ep} ({len(data)} bytes, {ct})")
            if 'json' in ct:
                j = json.loads(data.decode('utf-8'))
                if ep == "/api/trade/positions":
                    positions = j.get('positions', [])
                    print(f"  Live Positions Count: {len(positions)}")
                    for p in positions:
                        print(f"    - {p.get('symbol')} ({p.get('side')}): Entry={p.get('entry_price')}, Mark={p.get('mark_price')}, Margin={p.get('margin_usdt')}, ROE={p.get('roe_str')}, Section={p.get('section_id')}")
                elif ep == "/api/trade/history":
                    trades = j.get('trades', j if isinstance(j, list) else [])
                    print(f"  Closed Trades Count: {len(trades)}")
                    for t in trades[:10]:
                        print(f"    - ID={t.get('id')} {t.get('symbol')} ({t.get('side')}): Entry={t.get('entry_price')}, Exit={t.get('exit_price')}, PnL={t.get('pnl_usdt')}, Status={t.get('status')}")
                elif ep == "/api/deca/summary":
                    print(f"  Deca Summary: Equity=${j.get('total_equity')}, Used Margin=${j.get('used_margin')}, Free Margin=${j.get('free_margin')}, Net Return={j.get('pnl_pct')}%, Win Rate={j.get('win_rate')}%")
                elif ep == "/api/deca/setups":
                    setups = j.get('setups', [])
                    active = j.get('active_trades', [])
                    radar = j.get('radar', [])
                    print(f"  Setups count={len(setups)}, Active={len(active)}, Approaching={len(radar)}")
                    for s in setups[:5]:
                        print(f"    - {s.get('symbol')} {s.get('side')} (Sec {s.get('section_id')}): Status={s.get('status')}, Dist={s.get('distance_pct')}%")
                elif ep == "/api/deca/sections":
                    secs = j.get('sections', [])
                    print(f"  Sections count={len(secs)}")
                    for s in secs:
                        print(f"    - Sec {s.get('id')}: Bal=${s.get('current_balance')}, Status={s.get('status')}, Coins={s.get('assigned_coins')}")
                elif ep == "/api/markets/overview":
                    champs = j.get('champions', [])
                    all_m = j.get('all_markets', [])
                    print(f"  Champions count={len(champs)}, All markets count={len(all_m)}")
                    champ_syms = [c.get('symbol') for c in champs]
                    print(f"  Champions list: {champ_syms}")
                    print(f"  Deduplicated? {len(champ_syms) == len(set(champ_syms))}")
    except Exception as e:
        print(f"\n[FAIL] {ep}: {e}")
