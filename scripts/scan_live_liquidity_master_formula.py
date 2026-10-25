import asyncio
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import time
from datetime import datetime, timezone, timedelta
from feed.binance_feed import binance_feed
from config import DEFAULT_COINS, TIER1_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "AVAXUSDT", 
    "SUIUSDT", "NEARUSDT", "APTUSDT", "OPUSDT", "FILUSDT", "RENDERUSDT", 
    "RUNEUSDT", "SHIBUSDT", "LDOUSDT", "MKRUSDT", "UNIUSDT", "AAVEUSDT", 
    "GALAUSDT", "ICPUSDT", "PYTHUSDT", "ALGOUSDT"
]

IST = timezone(timedelta(hours=5, minutes=30))

async def scan_live_liquidity_formula():
    coins = list(dict.fromkeys(TOP_22_CHAMPIONS + DEFAULT_COINS[:15]))
    print("=" * 95)
    print("🏛️ HERMES × BOOMING BULLS: LIVE INSTITUTIONAL LIQUIDITY SWEEP SCANNER")
    print("=" * 95)
    print(f"Scanning {len(coins)} Top Champions across Binance Live Markets...")
    print(f"Rules: PDH / PDL Sweep | Wick >= 25% | Close Inside | 7% Volatility Anchor | Method 2 Retest\n")

    tickers = await binance_feed.fetch_all_tickers()
    if not tickers:
        print("⚠️ Could not fetch live tickers. Retrying with fallback...")

    triggered_sweeps = []
    radar_approaching = []

    for sym in coins:
        cur_price = tickers.get(sym)
        if not cur_price:
            # Fallback kline close
            pass

        # 1. Fetch Daily klines (at least 5 days to get PDH, PDL, and 14D ATR)
        d_klines = await binance_feed.fetch_klines(sym, interval="1d", limit=16, force_fresh=True)
        if not d_klines or len(d_klines) < 3:
            continue

        prev_day = d_klines[-2] # Completed previous day
        curr_day = d_klines[-1] # In-progress current day

        pdh = float(prev_day["high"])
        pdl = float(prev_day["low"])
        pd_range = pdh - pdl
        pd_move_pct = (pd_range / pdl) * 100.0 if pdl > 0 else 0.0

        if not cur_price:
            cur_price = float(curr_day["close"])

        # 2. Fetch 15m klines (last 24 hours = 96 bars)
        k15 = await binance_feed.fetch_klines(sym, interval="15m", limit=96, force_fresh=True)
        if not k15 or len(k15) < 10:
            continue

        # Check 14-day Daily ATR
        tr_list = []
        for i in range(1, len(d_klines) - 1):
            h = float(d_klines[i]["high"])
            l = float(d_klines[i]["low"])
            pc = float(d_klines[i - 1]["close"])
            tr = max(h - l, abs(h - pc), abs(l - pc))
            tr_list.append(tr)
        atr_14 = sum(tr_list) / len(tr_list) if tr_list else pd_range
        atr_pct = (atr_14 / cur_price) * 100.0

        # Check if today's range or past wave >= 7%
        cd_high = float(curr_day["high"])
        cd_low = float(curr_day["low"])
        cd_range_pct = ((cd_high - cd_low) / cd_low) * 100.0 if cd_low > 0 else 0.0

        vol_anchor_met = (pd_move_pct >= 7.0) or (cd_range_pct >= 7.0)

        # 3. Scan recent 15m bars for actual liquidity sweeps (in last 12 bars = 3 hours)
        recent_bars = k15[-16:]
        found_sweep = False

        for bar_idx, b in enumerate(recent_bars):
            b_o = float(b["open"])
            b_h = float(b["high"])
            b_l = float(b["low"])
            b_c = float(b["close"])
            b_rng = b_h - b_l
            b_time = b["time"]
            dt_ist = datetime.fromtimestamp(b_time / 1000.0, tz=IST).strftime("%H:%M IST")

            if b_rng <= 0:
                continue

            # Check Bullish PDL Sweep (LONG)
            if b_l < pdl and b_c > pdl:
                l_wick = min(b_o, b_c) - b_l
                wick_ratio = l_wick / b_rng
                if wick_ratio >= 0.25:
                    # Method 2 50% mitigation entry level
                    m2_entry = b_l + (b_c - b_l) * 0.50
                    sl_price = b_l * 0.9985
                    risk = abs(m2_entry - sl_price)
                    tp_2r = m2_entry + (risk * 2.0)
                    dist_to_entry = ((cur_price - m2_entry) / m2_entry) * 100.0

                    triggered_sweeps.append({
                        "symbol": sym,
                        "side": "LONG",
                        "sweep_type": "PDL SWEEP (V-SHAPE BUY)",
                        "time_str": dt_ist,
                        "cur_price": cur_price,
                        "pdl": pdl,
                        "pdh": pdh,
                        "sweep_low": b_l,
                        "wick_ratio": wick_ratio * 100.0,
                        "m2_entry": m2_entry,
                        "sl_price": sl_price,
                        "tp_2r": tp_2r,
                        "dist_to_entry": dist_to_entry,
                        "pd_move_pct": pd_move_pct,
                        "vol_anchor_met": vol_anchor_met,
                        "is_live_now": (bar_idx >= len(recent_bars) - 2)
                    })
                    found_sweep = True
                    break

            # Check Bearish PDH Sweep (SHORT)
            if b_h > pdh and b_c < pdh:
                u_wick = b_h - max(b_o, b_c)
                wick_ratio = u_wick / b_rng
                if wick_ratio >= 0.25:
                    m2_entry = b_h - (b_h - b_c) * 0.50
                    sl_price = b_h * 1.0015
                    risk = abs(sl_price - m2_entry)
                    tp_2r = m2_entry - (risk * 2.0)
                    dist_to_entry = ((cur_price - m2_entry) / m2_entry) * 100.0

                    triggered_sweeps.append({
                        "symbol": sym,
                        "side": "SHORT",
                        "sweep_type": "PDH SWEEP (V-SHAPE SELL)",
                        "time_str": dt_ist,
                        "cur_price": cur_price,
                        "pdl": pdl,
                        "pdh": pdh,
                        "sweep_high": b_h,
                        "wick_ratio": wick_ratio * 100.0,
                        "m2_entry": m2_entry,
                        "sl_price": sl_price,
                        "tp_2r": tp_2r,
                        "dist_to_entry": dist_to_entry,
                        "pd_move_pct": pd_move_pct,
                        "vol_anchor_met": vol_anchor_met,
                        "is_live_now": (bar_idx >= len(recent_bars) - 2)
                    })
                    found_sweep = True
                    break

        # 4. If no sweep yet, check distance to PDH / PDL (Radar Pre-Armed)
        if not found_sweep:
            dist_to_pdh_pct = ((pdh - cur_price) / cur_price) * 100.0
            dist_to_pdl_pct = ((cur_price - pdl) / cur_price) * 100.0

            if 0.0 <= dist_to_pdh_pct <= 1.2:
                radar_approaching.append({
                    "symbol": sym,
                    "target_level": "PDH",
                    "level_price": pdh,
                    "cur_price": cur_price,
                    "dist_pct": dist_to_pdh_pct,
                    "side": "ANTICIPATING SHORT SWEEP",
                    "pd_move_pct": pd_move_pct,
                    "vol_anchor_met": vol_anchor_met
                })
            elif 0.0 <= dist_to_pdl_pct <= 1.2:
                radar_approaching.append({
                    "symbol": sym,
                    "target_level": "PDL",
                    "level_price": pdl,
                    "cur_price": cur_price,
                    "dist_pct": dist_to_pdl_pct,
                    "side": "ANTICIPATING LONG SWEEP",
                    "pd_move_pct": pd_move_pct,
                    "vol_anchor_met": vol_anchor_met
                })

    await binance_feed.close()

    # Sort & Display
    print("=" * 95)
    print("🎯 SECTION 1: CONFIRMED LIVE LIQUIDITY SWEEPS (TRIGGERED / MITIGATION)")
    print("=" * 95)
    if triggered_sweeps:
        for idx, s in enumerate(triggered_sweeps, 1):
            live_badge = "🔥 [ACTIVE RIGHT NOW]" if s["is_live_now"] else "⚡ [RECENT CONFIRMED]"
            vol_badge = "✅ 7% VOLATILITY MET" if s["vol_anchor_met"] else "⚠️ < 7% MOVE"
            print(f"\n#{idx}. {s['symbol']} — {s['sweep_type']} {live_badge} | {vol_badge}")
            print(f"    • Time: {s['time_str']} | Rejection Wick: {s['wick_ratio']:.1f}% | Prior Day Range: {s['pd_move_pct']:.1f}%")
            print(f"    • Current Price: ${s['cur_price']:.4f}")
            print(f"    • Method 2 Limit Entry (50% FVG): ${s['m2_entry']:.4f} (Distance: {s['dist_to_entry']:+.2f}%)")
            print(f"    • Stop Loss: ${s['sl_price']:.4f} | Target 1:2 R:R: ${s['tp_2r']:.4f}")
            print(f"    • Stepped Trailing: +1.0R hit -> Shift SL to +0.2R (Fee-Shield) | +1.5R hit -> Lock +1.0R")
    else:
        print("Koi pair pichle 2-3 ghante me direct sweep trigger me nahi hai (Market consolidates).")

    print("\n" + "=" * 95)
    print("📡 SECTION 2: RADAR PRE-ARMED CANDIDATES (APPROACHING PDH/PDL WITHIN 1%)")
    print("=" * 95)
    radar_approaching.sort(key=lambda x: x["dist_pct"])
    if radar_approaching:
        for idx, r in enumerate(radar_approaching[:10], 1):
            vol_badge = "🔥 [7%+ High Volatility]" if r["vol_anchor_met"] else "[Standard]"
            print(f"#{idx}. {r['symbol']:<10} | Current: ${r['cur_price']:<9.4f} | {r['target_level']}: ${r['level_price']:<9.4f} | Dist: {r['dist_pct']:+.2f}% | {r['side']} {vol_badge}")
    else:
        print("Koi pair 1% proximity me nahi hai.")
    print("=" * 95 + "\n")

if __name__ == "__main__":
    asyncio.run(scan_live_liquidity_formula())
