import os
import sys
import ssl
import json
import urllib.request
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl._create_unverified_context()
symbols = [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'AVAXUSDT', 'DOGEUSDT',
    'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'NEARUSDT', 'OPUSDT', 'RENDERUSDT',
    'SUIUSDT', 'TIAUSDT', 'UNIUSDT', 'XRPUSDT', '1000PEPEUSDT', 'APTUSDT',
    'ARBUSDT', 'FETUSDT'
]

results = []

for sym in symbols:
    try:
        url_d = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=1d&limit=3"
        req_d = urllib.request.Request(url_d, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_d, context=ctx, timeout=5) as r:
            d_data = json.loads(r.read().decode("utf-8"))
        
        url_15m = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=15m&limit=16"
        req_15m = urllib.request.Request(url_15m, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_15m, context=ctx, timeout=5) as r:
            k_data = json.loads(r.read().decode("utf-8"))

        prev_day = d_data[-2]
        pdh = float(prev_day[2])
        pdl = float(prev_day[3])
        curr_price = float(k_data[-1][4])

        dist_pdl_pct = abs(curr_price - pdl) / pdl * 100
        dist_pdh_pct = abs(curr_price - pdh) / pdh * 100

        # Check recent sweep in last 6 bars (last 1.5 hours)
        swept_pdl = any(float(k[3]) <= pdl for k in k_data[-6:])
        swept_pdh = any(float(k[2]) >= pdh for k in k_data[-6:])

        if dist_pdh_pct < dist_pdl_pct:
            target_level = "PDH RESIST (SHORT)"
            target_price = pdh
            min_dist = dist_pdh_pct
            is_swept = swept_pdh
        else:
            target_level = "PDL SUPPORT (LONG)"
            target_price = pdl
            min_dist = dist_pdl_pct
            is_swept = swept_pdl

        # Calculate estimated 50% MT if swept
        est_mt = None
        if is_swept:
            if target_level.startswith("PDH"):
                high_val = max(float(k[2]) for k in k_data[-4:])
                est_mt = (high_val + pdh) / 2.0
            else:
                low_val = min(float(k[3]) for k in k_data[-4:])
                est_mt = (low_val + pdl) / 2.0

        results.append({
            "symbol": sym,
            "price": curr_price,
            "target_level": target_level,
            "target_price": target_price,
            "dist_pct": min_dist,
            "is_swept": is_swept,
            "est_mt": est_mt
        })
    except Exception as e:
        pass

results.sort(key=lambda x: x["dist_pct"])

now_str = datetime.now(timezone.utc).strftime("%H:%M UTC")
print("=" * 85)
print(f"🎯 BB 2.0 ENTRY PROXIMITY RANKING ({now_str})")
print("=" * 85)
print(f"{'RANK':<5} | {'SYMBOL':<13} | {'PRICE':<12} | {'TARGET LEVEL':<20} | {'LEVEL PRICE':<12} | {'DISTANCE %':<11} | {'STATUS'}")
print("-" * 85)

for i, r in enumerate(results[:10]):
    status = "🔥 ALREADY SWEPT!" if r["is_swept"] else ("🚨 IN STRIKE ZONE" if r["dist_pct"] < 1.0 else "👀 APPROACHING")
    print(f"#{i+1:<4} | {r['symbol']:<13} | {r['price']:<12.4f} | {r['target_level']:<20} | {r['target_price']:<12.4f} | {r['dist_pct']:>9.2f}% | {status}")
print("=" * 85)
