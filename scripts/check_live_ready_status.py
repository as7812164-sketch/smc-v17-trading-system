import urllib.request
import json

url = "https://smc-ai-agent.onrender.com/api/hermes/apex/setups"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as res:
    data = json.loads(res.read().decode())
    setups = data.get("setups", [])

# Fetch current prices from Binance
ticker_url = "https://fapi.binance.com/fapi/v1/ticker/price"
with urllib.request.urlopen(ticker_url, timeout=10) as res:
    tickers = {item["symbol"]: float(item["price"]) for item in json.loads(res.read().decode())}

candidates = []
for s in setups:
    sym = s.get("symbol")
    mt = float(s.get("mean_threshold", 0))
    side = s.get("side", "BUY")
    interval = s.get("interval", "4h")
    cur_p = tickers.get(sym, 0.0)
    if cur_p > 0 and mt > 0:
        # Distance from current price to MT entry
        dist_pct = abs(cur_p - mt) / cur_p * 100.0
        # If SHORT, price needs to rise to MT. If LONG, price needs to fall to MT.
        condition_met = (cur_p >= mt) if side == "SHORT" else (cur_p <= mt)
        candidates.append({
            "symbol": sym,
            "side": side,
            "interval": interval,
            "current_price": cur_p,
            "entry_price": mt,
            "dist_pct": dist_pct,
            "condition_met": condition_met,
            "tp_price": s.get("tp_price"),
            "soft_sl_price": s.get("soft_sl_price")
        })

# Sort by closest distance
candidates.sort(key=lambda x: x["dist_pct"])

print(f"Total Evaluated Candidates: {len(candidates)}")
print("\n--- TOP 10 CLOSEST ACTIVE SETUPS READY FOR ENTRY ---")
for i, c in enumerate(candidates[:10], 1):
    ready_tag = "[TAP TRIGGER!]" if c["condition_met"] or c["dist_pct"] <= 0.1 else f"{c['dist_pct']:.2f}% away"
    print(f"{i:2d}. {c['symbol']:12s} {c['side']:5s} [{c['interval']:2s}] | Price: ${c['current_price']:.4f} -> Entry (50% MT): ${c['entry_price']:.4f} | Status: {ready_tag}")
