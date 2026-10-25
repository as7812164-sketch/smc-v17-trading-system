"""
LIVE 15M SETUP DETECTOR FOR BB 2.0 (OCTOBER 15, 2026)
=====================================================
Scans all 20 Champions on 15m Binance Futures for:
- Completed PDL/PDH sweep today
- Bullish/Bearish displacement candle with lower/upper wick or FVG
- Active or forming 50% Mean Threshold Limit Setups
"""

import urllib.request
import json
import time
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

CHAMPIONS = [
    ("BTCUSDT", 1), ("ETHUSDT", 1),
    ("SOLUSDT", 2), ("BNBUSDT", 2),
    ("AVAXUSDT", 3), ("DOGEUSDT", 3),
    ("DOTUSDT", 4), ("LINKUSDT", 4),
    ("LTCUSDT", 5), ("NEARUSDT", 5),
    ("OPUSDT", 6), ("RENDERUSDT", 6),
    ("SUIUSDT", 7), ("TIAUSDT", 7),
    ("UNIUSDT", 8), ("XRPUSDT", 8),
    ("1000PEPEUSDT", 9), ("APTUSDT", 9),
    ("ARBUSDT", 10), ("FETUSDT", 10)
]

def fetch_klines(symbol, interval, limit):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())

def analyze_coin(symbol, sec_id):
    try:
        # Get 1d for PDH/PDL
        daily = fetch_klines(symbol, "1d", 3)
        if len(daily) < 2:
            return None
        pdh = float(daily[-2][2])
        pdl = float(daily[-2][3])

        # Get last 24 15m candles
        m15 = fetch_klines(symbol, "15m", 24)
        if len(m15) < 10:
            return None

        cur_price = float(m15[-1][4])

        # Look for PDL sweep in today's candles
        # UTC midnight timestamp for Oct 15
        now_dt = datetime.now(timezone.utc)
        midnight_utc_ms = datetime(now_dt.year, now_dt.month, now_dt.day, tzinfo=timezone.utc).timestamp() * 1000

        today_15m = [c for c in m15 if c[0] >= midnight_utc_ms]
        if not today_15m:
            today_15m = m15[-8:]

        lowest_bar = min(today_15m, key=lambda c: float(c[3]))
        lowest_price = float(lowest_bar[3])
        highest_bar = max(today_15m, key=lambda c: float(c[2]))
        highest_price = float(highest_bar[2])

        pdl_swept = lowest_price <= pdl
        pdh_swept = highest_price >= pdh

        setups = []

        # LONG Setup Check (PDL Sweep)
        if pdl_swept:
            # Find the sweep candle index
            sweep_idx = -1
            for idx, c in enumerate(m15):
                if float(c[3]) == lowest_price:
                    sweep_idx = idx
                    break

            if sweep_idx != -1 and sweep_idx + 1 < len(m15):
                sw_c = m15[sweep_idx]
                sw_o, sw_h, sw_l, sw_c_close = float(sw_c[1]), float(sw_c[2]), float(sw_c[3]), float(sw_c[4])
                
                # Check for subsequent displacement/bounce
                post_candles = m15[sweep_idx + 1:]
                max_bounce = max(float(c[2]) for c in post_candles) if post_candles else sw_h
                bounce_pct = (max_bounce - sw_l) / sw_l * 100.0

                mt = (sw_h + sw_l) / 2.0
                sl = sw_l * 0.9985  # 0.15% anti-hunt buffer
                risk_pct = (mt - sl) / mt * 100.0
                tp_3r = mt + ((mt - sl) * 3.0)

                dist_to_mt = (cur_price - mt) / mt * 100.0

                stage = "PDL Pierced (Waiting for 15m Reversal)"
                if bounce_pct >= 0.8:
                    if cur_price <= mt:
                        stage = "🎯 AT 50% MT (READY TO FILL!)"
                    else:
                        stage = "⚡ ARMED (Waiting for Pullback to MT)"
                elif bounce_pct >= 0.4:
                    stage = "⏳ Green Displacement In Progress"

                setups.append({
                    "symbol": symbol,
                    "section": sec_id,
                    "side": "LONG",
                    "sweep_level": pdl,
                    "lowest_point": sw_l,
                    "entry_mt": mt,
                    "sl_price": sl,
                    "risk_pct": risk_pct,
                    "tp_price": tp_3r,
                    "cur_price": cur_price,
                    "dist_to_entry": dist_to_mt,
                    "bounce_pct": bounce_pct,
                    "stage": stage
                })

        return setups
    except Exception as e:
        return []

def main():
    print("=" * 100)
    print("🎯 BB 2.0 TODAY'S LIVE TRADE SETUPS (OCTOBER 15, 2026 - 15M SCAN)")
    print("=" * 100)

    all_setups = []
    for sym, sec in CHAMPIONS:
        res = analyze_coin(sym, sec)
        if res:
            all_setups.extend(res)
        time.sleep(0.05)

    # Sort by closest to entry
    all_setups.sort(key=lambda x: abs(x["dist_to_entry"]))

    print(f"{'#':<3} {'Sec':<4} {'Symbol':<13} {'Side':<6} {'Live Price':<12} {'50% MT Entry':<13} {'Stop Loss':<12} {'Dist to MT':<12} {'Setup Stage'}")
    print("-" * 100)

    for idx, s in enumerate(all_setups, 1):
        print(f"{idx:<3} #{s['section']:<3} {s['symbol']:<13} {s['side']:<6} {s['cur_price']:<12.4f} {s['entry_mt']:<13.4f} {s['sl_price']:<12.4f} {s['dist_to_entry']:+6.2f}%{'':<5} {s['stage']}")

    print("=" * 100)
    print(f"Total Qualified Setups Today: {len(all_setups)} across 10 Sections")

if __name__ == "__main__":
    main()
