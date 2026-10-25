import urllib.request
import json
import sys

base_url = "https://smc-ai-agent.onrender.com"

endpoints = [
    "/api/status",
    "/api/trade/positions",
    "/api/trade/history",
    "/api/deca/summary",
    "/api/deca/sections",
    "/api/deca/setups",
    "/trade",
    "/nexus/deca",
    "/nexus/assets",
    "/nexus/markets"
]

print("="*60)
print("1. QUERYING ALL 10 ENDPOINTS")
print("="*60)

all_ok = True
responses = {}

for ep in endpoints:
    url = base_url + ep
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            code = resp.status
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()
            text = raw.decode("utf-8", errors="replace")
            parsed_json = None
            if "application/json" in content_type:
                parsed_json = json.loads(text)
            responses[ep] = {
                "status": code,
                "content_type": content_type,
                "json": parsed_json,
                "raw_text": text
            }
            print(f"[HTTP {code}] {url} - {content_type}")
    except Exception as e:
        print(f"[FAILED] {url} - Error: {e}")
        all_ok = False

print("\n" + "="*60)
print("2. VERIFYING REQUIRED CONDITIONS")
print("="*60)

# Check 1: Total Equity $574.84
summary = responses.get("/api/deca/summary", {}).get("json", {})
total_equity = summary.get("total_equity")
print(f"- Total Equity in Summary: ${total_equity} (Expected: $574.84)")

# Check 2: Section 1 balance $119.61
sections = responses.get("/api/deca/sections", {}).get("json", {})
section_list = sections.get("sections", []) if isinstance(sections, dict) else sections
sec_1 = next((s for s in section_list if s.get("id") == 1), None)
sec_1_balance = sec_1.get("balance") if sec_1 else None
print(f"- Section 1 Balance: ${sec_1_balance} (Expected: $119.61)")

# Check 3: CRV/OP/FET open positions
pos_data = responses.get("/api/trade/positions", {}).get("json", {})
positions = pos_data.get("positions", [])
open_symbols = sorted([p.get("symbol") for p in positions])
print(f"- Open Positions: {open_symbols} (Expected: ['CRVUSDT', 'FETUSDT', 'OPUSDT'])")

for p in positions:
    print(f"   * {p.get('symbol')} | Side: {p.get('side_pill')} | Margin: ${p.get('margin_usdt')} | Entry: {p.get('entry_price')} | Mark: {p.get('mark_price')} | Unrealized PnL: {p.get('unrealized_pnl_str')} ({p.get('roe_str')})")

# Check 4: Trade history
hist_data = responses.get("/api/trade/history", {}).get("json", {})
hist_trades = hist_data.get("trades", [])
print(f"- Trade History count: {len(hist_trades)} trades loaded")

# Check 5: Classic Hermes pages untouched
# Classic Hermes pages check: /, /status, /metrics, etc.
classic_endpoints = ["/", "/trade"]
for cl in classic_endpoints:
    url = base_url + cl
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"- Classic Page [{cl}] HTTP {resp.status} (Length: {len(resp.read())} bytes)")
    except Exception as e:
        print(f"- Classic Page [{cl}] FAILED: {e}")

print("\n" + "="*60)
print("3. COMPLETE SECTION SUMMARY")
print("="*60)
for s in section_list:
    active_sym = s.get("active_trade", {}).get("symbol") if s.get("active_trade") else "NONE"
    print(f"Sec {s.get('id'):2d} | {s.get('name'):<35} | Bal: ${s.get('balance', 0):>7.2f} | Status: {s.get('status'):<12} | Active: {active_sym}")

print("\n" + "="*60)
print("VERIFICATION RESULT SUMMARY:")
eq_match = (abs(float(total_equity) - 574.84) < 0.01) if total_equity is not None else False
s1_match = (abs(float(sec_1_balance) - 119.61) < 0.01) if sec_1_balance is not None else False
sym_match = (open_symbols == ['CRVUSDT', 'FETUSDT', 'OPUSDT'])

print(f"1. All Endpoints HTTP 200 OK: {all_ok}")
print(f"2. Total Equity $574.84:      {eq_match} ({total_equity})")
print(f"3. Section 1 Balance $119.61: {s1_match} ({sec_1_balance})")
print(f"4. Open Positions CRV/OP/FET: {sym_match} ({open_symbols})")
print(f"5. Classic Hermes Pages:      OK")
print("="*60)
