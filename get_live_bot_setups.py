import urllib.request
import json
import time
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def fetch_live_bot_state():
    base_urls = ["https://smc-ai-agent.onrender.com", "http://127.0.0.1:8000"]
    data = None
    active_base = None
    
    for base in base_urls:
        try:
            req = urllib.request.Request(f"{base}/api/hermes/apex/setups", headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req, timeout=12).read().decode()
            data = json.loads(raw)
            active_base = base
            print(f"Connected successfully to {base}!")
            break
        except Exception as e:
            print(f"Failed {base}: {e}")
            
    if not data:
        print("Could not connect to server.")
        return

    # Fetch fresh live prices from Binance
    try:
        t_req = urllib.request.Request("https://fapi.binance.com/fapi/v1/ticker/price", headers={"User-Agent": "Mozilla/5.0"})
        t_raw = urllib.request.urlopen(t_req, timeout=8).read().decode()
        tickers = {item["symbol"]: float(item["price"]) for item in json.loads(t_raw)}
    except Exception as e:
        print(f"Warning: could not fetch live tickers: {e}")
        tickers = {}

    setups = data.get("setups", [])
    btc_macro = data.get("btc_macro_sentry", {})
    
    print("=" * 90)
    print(" 🤖 LIVE HERMES 2.5 APEX BOT WATCHDOG & SETUP SCANNER")
    print("=" * 90)
    print(f"BTC Macro Sentry: {btc_macro.get('bias', 'NEUTRAL')} | 4H Bar Change: {btc_macro.get('change_pct', 0.0)}% | Long Veto: {btc_macro.get('long_veto')} | Short Veto: {btc_macro.get('short_veto')}")
    print(f"Total Detected / Armed Setups: {len(setups)}")
    print("-" * 90)

    # Calculate distance to entry
    annotated = []
    for s in setups:
        sym = s.get("symbol")
        cur_p = tickers.get(sym, 0.0)
        entry_p = float(s.get("entry_price", 0.0))
        side = s.get("side", "LONG")
        ob_high = float(s.get("ob_high", entry_p))
        ob_low = float(s.get("ob_low", entry_p))
        
        dist_pct = 0.0
        if cur_p > 0 and entry_p > 0:
            dist_pct = (cur_p - entry_p) / entry_p * 100.0
            
        annotated.append({
            "symbol": sym,
            "side": side,
            "tf": s.get("interval"),
            "current_price": cur_p,
            "entry_price": entry_p,
            "ob_range": f"[{ob_low:.4f} - {ob_high:.4f}]",
            "tp_price": float(s.get("tp_price", 0.0)),
            "sl_price": float(s.get("hard_sl_price", 0.0)),
            "status": s.get("status"),
            "is_fresh": s.get("is_fresh_trigger"),
            "dist_pct": dist_pct,
            "abs_dist": abs(dist_pct),
            "reason": s.get("sentry_reasons", "")
        })

    # Sort by nearest distance to entry
    annotated.sort(key=lambda x: x["abs_dist"])

    # Categorize into:
    # 1. Fresh / Imminent Tap (within <= 1.0% of Order Block)
    # 2. Armed & Stalking (within 1.0% - 3.5% of Order Block)
    # 3. Wider Watchlist
    imminent = [s for s in annotated if s["abs_dist"] <= 1.2]
    stalking = [s for s in annotated if 1.2 < s["abs_dist"] <= 3.5]
    watchlist = [s for s in annotated if s["abs_dist"] > 3.5]

    print(f"\n🚨 1. IMMINENT / NEAREST SETUPS (Price within ~1% of Order Block Trigger):")
    if imminent:
        for s in imminent:
            direction_arrow = "⬇️ Dropping into OB" if (s["side"] == "LONG" and s["dist_pct"] > 0) else "⬆️ Pushing up into OB"
            print(f"  • {s['symbol']} ({s['tf'].upper()} {s['side']}) | Cur: {s['current_price']} | Entry: {s['entry_price']} | Dist: {s['dist_pct']:+.2f}% ({direction_arrow}) | Status: {s['status']}")
            print(f"    TP: {s['tp_price']:.4f} | SL: {s['sl_price']:.4f} | Zone: {s['ob_range']}")
            print(f"    Confluence: {s['reason']}")
    else:
        print("  (Koi coin abhi exact 1.2% boundary ke andar nahi hai, agle 1H/4H bar close ka wait ho raha hai)")

    print(f"\n🎯 2. ARMED & STALKING SETUPS (Watching for pullback, within 1.2% - 3.5%):")
    for s in stalking[:8]:
        direction_arrow = "Needs small dip" if s["side"] == "LONG" else "Needs small bounce"
        print(f"  • {s['symbol']} ({s['tf'].upper()} {s['side']}) | Cur: {s['current_price']} | OB Entry: {s['entry_price']} | Dist: {s['dist_pct']:+.2f}% ({direction_arrow})")
        print(f"    TP: {s['tp_price']:.4f} | SL: {s['sl_price']:.4f} | Status: {s['status']}")

    print(f"\n📋 3. TOTAL ARMED ZONES SUMMARY:")
    longs_count = sum(1 for s in annotated if s['side'] == 'LONG')
    shorts_count = sum(1 for s in annotated if s['side'] == 'SHORT')
    print(f"  Total Bullish (LONG) Zones Armed:  {longs_count}")
    print(f"  Total Bearish (SHORT) Zones Armed: {shorts_count}")
    print("=" * 90)

if __name__ == "__main__":
    fetch_live_bot_state()
