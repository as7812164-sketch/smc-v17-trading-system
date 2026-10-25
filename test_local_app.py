import sys
import os

try:
    from fastapi.testclient import TestClient
    from app import app

    client = TestClient(app)

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
        "/api/markets"
    ]

    print("=== TESTING LOCAL FASTAPI APP VIA TESTCLIENT ===")
    for ep in endpoints:
        try:
            resp = client.get(ep)
            print(f"[LOCAL OK {resp.status_code}] {ep} ({len(resp.content)} bytes)")
            if "application/json" in resp.headers.get("content-type", ""):
                data = resp.json()
                if ep == "/api/trade/positions":
                    pos = data.get("positions", [])
                    print(f"  Live Positions Count: {len(pos)}")
                    for p in pos:
                        print(f"    - {p.get('symbol')} ({p.get('side')}): Entry={p.get('entry_price')}, Mark={p.get('mark_price')}, Margin={p.get('margin_usdt')}, ROE={p.get('roe_str')}, Sec={p.get('section_id')}")
                elif ep == "/api/trade/history":
                    th = data if isinstance(data, list) else data.get("trades", [])
                    print(f"  History count: {len(th)}")
                    for t in th[:5]:
                        print(f"    - ID={t.get('id')} {t.get('symbol')} ({t.get('side')}): Status={t.get('status')}")
                elif ep == "/api/deca/summary":
                    print(f"  Summary: Eq=${data.get('total_equity')}, Used Margin=${data.get('used_margin')}, Free Margin=${data.get('free_margin')}, Net Return={data.get('pnl_pct')}%, Win Rate={data.get('win_rate')}%")
                elif ep == "/api/deca/sections":
                    secs = data.get("sections", [])
                    print(f"  Sections count: {len(secs)}")
                    for s in secs:
                        print(f"    - Sec {s.get('id')}: Bal=${s.get('current_balance')}, Status={s.get('status')}, Active={s.get('active_trade', {}).get('symbol') if s.get('active_trade') else 'None'}")
                elif ep == "/api/markets":
                    champs = data.get("champions", [])
                    print(f"  Champions count: {len(champs)}")
                    champ_syms = [c.get("symbol") for c in champs]
                    print(f"  Champions: {champ_syms}")
                    print(f"  Deduplicated: {len(champ_syms) == len(set(champ_syms))}")
        except Exception as ex:
            print(f"[LOCAL FAIL] {ep}: {ex}")

except Exception as e:
    print(f"Failed to initialize TestClient or app: {e}")
    import traceback
    traceback.print_exc()
