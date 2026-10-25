import urllib.request
import json
import ssl

ctx = ssl._create_unverified_context()

targets = [
    ("HERMES 3.0 Production (smc-ai-agent.onrender.com)", "https://smc-ai-agent.onrender.com"),
    ("NexusPro BB 3.0 Production (nexuspro-terminal.onrender.com)", "https://nexuspro-terminal.onrender.com")
]

endpoints = [
    "/api/status",
    "/api/bb20/status",
    "/api/trade/positions",
    "/api/trade/history",
    "/api/deca/summary",
    "/api/deca/sections",
    "/api/deca/setups",
    "/trade",
    "/hologram",
    "/nexus/deca"
]

for name, base in targets:
    print(f"\n{'='*70}\n{name}: {base}\n{'='*70}")
    for ep in endpoints:
        url = base + ep
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Sentinel/1.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
                code = r.status
                ct = r.headers.get("Content-Type", "")
                raw = r.read()
                print(f"[HTTP {code}] {ep:<22} | CT: {ct:<30} | {len(raw)} bytes")
                
                if "application/json" in ct:
                    data = json.loads(raw.decode("utf-8"))
                    if ep == "/api/status":
                        print(f"       Status: {data.get('status')}, Version/Mode: {data.get('version') or data.get('mode')}")
                    elif ep == "/api/bb20/status":
                        print(f"       BB20 Total Initial: ${data.get('total_initial_capital')}, Current Equity: ${data.get('total_current_equity')}")
                    elif ep == "/api/trade/positions":
                        pos = data.get("positions", [])
                        syms = [p.get("symbol") for p in pos]
                        print(f"       Positions ({len(pos)}): {syms}")
                        for p in pos:
                            print(f"         * {p.get('symbol')} {p.get('side')}: Entry={p.get('entry_price')} Mark={p.get('mark_price')} Margin=${p.get('margin_usdt')} Sec={p.get('section_id')}")
                    elif ep == "/api/trade/history":
                        th = data.get("trades", data if isinstance(data, list) else [])
                        print(f"       History trades count: {len(th)}")
                        if th:
                            last_3 = th[:3]
                            for t in last_3:
                                print(f"         * ID={t.get('id')} {t.get('symbol')} {t.get('side')} PnL=${t.get('pnl_usdt', t.get('realized_pnl'))} Status={t.get('status', t.get('exit_reason'))}")
                    elif ep == "/api/deca/summary":
                        print(f"       Equity: ${data.get('total_equity')}, Bal: ${data.get('total_balance')}, Free: ${data.get('free_margin')}, Net Return: {data.get('pnl_pct') or data.get('net_return_pct')}%")
                    elif ep == "/api/deca/sections":
                        secs = data.get("sections", data if isinstance(data, list) else [])
                        sum_bal = sum(float(s.get("balance", s.get("current_balance", 0.0)) or 0.0) for s in secs)
                        print(f"       Sections count: {len(secs)}, Sum Balance: ${sum_bal:.2f}")
                        for s in secs[:5]:
                            print(f"         * Sec {s.get('id')}: Bal=${s.get('balance', s.get('current_balance'))} Status={s.get('status')} Coins={s.get('coins') or s.get('assigned_coins')}")
                    elif ep == "/api/deca/setups":
                        setups = data.get("setups", [])
                        act = data.get("active_trades", [])
                        print(f"       Setups count: {len(setups)}, Active trades count: {len(act)}")
                        for st in setups[:3]:
                            print(f"         * Setup: {st.get('symbol')} {st.get('side')} (Sec {st.get('section_id')}) Status={st.get('status')}")
                elif "text/html" in ct:
                    html_text = raw.decode("utf-8", errors="replace")
                    has_opp = "opposite" in html_text.lower() or "liquidity" in html_text.lower()
                    has_killzone = "killzone" in html_text.lower()
                    has_script_error_trap = "onerror" in html_text.lower() or "catch" in html_text.lower()
                    print(f"       HTML checks: title in page? {'<title>' in html_text}, has 'liquidity': {has_opp}, has 'killzone': {has_killzone}")
        except Exception as e:
            print(f"[ERROR]   {ep:<22} | {e}")
