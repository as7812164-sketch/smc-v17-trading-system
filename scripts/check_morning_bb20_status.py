"""
MORNING STATUS INSPECTOR: BB 2.0 (OCTOBER 15, 2026)
===================================================
Fetches live Binance Futures data for Top 20 Champions:
- Yesterday's PDH and PDL (Oct 14)
- Today's high and low (Oct 15)
- Current live price
- Proximity to PDH/PDL and status of liquidity sweep
"""

import urllib.request
import json
import time
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

CHAMPIONS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT",
    "DOGEUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "NEARUSDT",
    "OPUSDT", "RENDERUSDT", "SUIUSDT", "TIAUSDT", "UNIUSDT",
    "XRPUSDT", "1000PEPEUSDT", "APTUSDT", "ARBUSDT", "FETUSDT"
]

def fetch_daily_and_live(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1d&limit=3"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        
        # data[-1] is today (Oct 15), data[-2] is yesterday (Oct 14)
        if len(data) >= 2:
            yest = data[-2]
            today = data[-1]
            pdh = float(yest[2])
            pdl = float(yest[3])
            cur_p = float(today[4])
            today_h = float(today[2])
            today_l = float(today[3])
            
            dist_pdh_pct = ((pdh - cur_p) / cur_p) * 100.0
            dist_pdl_pct = ((cur_p - pdl) / cur_p) * 100.0
            
            swept_pdh = today_h >= pdh
            swept_pdl = today_l <= pdl
            
            return {
                "symbol": symbol,
                "cur_p": cur_p,
                "pdh": pdh,
                "pdl": pdl,
                "today_h": today_h,
                "today_l": today_l,
                "dist_pdh_pct": dist_pdh_pct,
                "dist_pdl_pct": dist_pdl_pct,
                "swept_pdh": swept_pdh,
                "swept_pdl": swept_pdl
            }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}

def main():
    results = []
    for sym in CHAMPIONS:
        res = fetch_daily_and_live(sym)
        if res and "error" not in res:
            results.append(res)
        time.sleep(0.05)

    # Sort by closest to any boundary (PDH or PDL)
    for r in results:
        r["min_dist"] = min(abs(r["dist_pdh_pct"]), abs(r["dist_pdl_pct"]))
    
    results.sort(key=lambda x: x["min_dist"])

    print("=" * 95)
    print("🌅 BB 2.0 MORNING MARKET PULSE: PROXIMITY TO OCT 15 PDH/PDL")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 95)
    print(f"{'Rank':<5} {'Symbol':<14} {'Current Price':<14} {'PDH (Resist)':<14} {'PDL (Supp)':<14} {'Dist to PDH':<13} {'Dist to PDL':<13} {'Sweep Status':<12}")
    print("-" * 95)

    for idx, r in enumerate(results, 1):
        status = "INSIDE RANGE"
        if r["swept_pdh"] and r["swept_pdl"]:
            status = "BOTH SWEPT!"
        elif r["swept_pdh"]:
            status = "🔥 PDH SWEPT"
        elif r["swept_pdl"]:
            status = "🔥 PDL SWEPT"
        elif r["min_dist"] <= 1.0:
            status = "⚡ IN STRIKE ZONE"

        print(f"#{idx:<4} {r['symbol']:<14} {r['cur_p']:<14.4f} {r['pdh']:<14.4f} {r['pdl']:<14.4f} {r['dist_pdh_pct']:+6.2f}%{'':<6} {r['dist_pdl_pct']:+6.2f}%{'':<6} {status}")
    print("=" * 95)

if __name__ == "__main__":
    main()
