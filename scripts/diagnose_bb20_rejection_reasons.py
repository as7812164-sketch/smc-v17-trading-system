"""
Diagnose BB 2.0 setup formation for all 20 coins right now.
Explains exactly why a trade has or hasn't triggered today.
"""

import os
import sys
import json
import ssl
import urllib.request
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import bb20_config as cfg
from scripts.run_bb20_live_sniper import fetch_binance_klines

def diagnose():
    print("=" * 95)
    print("🔍 BB 2.0 LIVE MARKET FORENSIC DIAGNOSTIC (OCT 14, 2026)")
    print("=" * 95)

    for symbol in cfg.CHAMPIONS:
        daily = fetch_binance_klines(symbol, "1d", 3)
        if len(daily) < 2:
            print(f"[{symbol}] Failed to fetch daily candles")
            continue
        prev_day = daily[-2]
        pdh = prev_day["high"]
        pdl = prev_day["low"]

        candles_15m = fetch_binance_klines(symbol, "15m", 35)
        if len(candles_15m) < 10:
            print(f"[{symbol}] Failed to fetch 15m candles")
            continue

        last_c = candles_15m[-1]
        price = last_c["close"]

        dist_pdh = (price - pdh) / pdh * 100.0
        dist_pdl = (price - pdl) / pdl * 100.0

        c_base = candles_15m[-3]
        c_disp = candles_15m[-2]
        c_curr = candles_15m[-1]

        # Check Short at PDH
        near_pdh = abs(c_base["high"] - pdh) / pdh <= 0.015 or c_base["high"] >= pdh
        drop_1bar = (c_base["high"] - c_disp["low"]) / c_base["high"]
        drop_2bar = (c_base["high"] - c_curr["low"]) / c_base["high"]
        has_bear_fvg = c_curr["high"] < c_base["low"]
        disp_ok_short = drop_1bar >= 0.012 or drop_2bar >= 0.018

        # Check Long at PDL
        near_pdl = abs(c_base["low"] - pdl) / pdl <= 0.015 or c_base["low"] <= pdl
        gain_1bar = (c_disp["high"] - c_base["low"]) / c_base["low"]
        gain_2bar = (c_curr["high"] - c_base["low"]) / c_base["low"]
        has_bull_fvg = c_curr["low"] > c_base["high"]
        disp_ok_long = gain_1bar >= 0.012 or gain_2bar >= 0.018

        # Status determination
        reasons = []
        if near_pdh:
            reasons.append(f"Near PDH ({dist_pdh:+.2f}%)")
            if not disp_ok_short:
                reasons.append(f"Disp weak ({max(drop_1bar, drop_2bar)*100:.2f}% < 1.2%)")
            if not has_bear_fvg:
                reasons.append("No Bear FVG")
            if disp_ok_short and has_bear_fvg:
                reasons.append("🔥 VALID SHORT OB FORMED!")
        elif near_pdl:
            reasons.append(f"Near PDL ({dist_pdl:+.2f}%)")
            if not disp_ok_long:
                reasons.append(f"Disp weak ({max(gain_1bar, gain_2bar)*100:.2f}% < 1.2%)")
            if not has_bull_fvg:
                reasons.append("No Bull FVG")
            if disp_ok_long and has_bull_fvg:
                reasons.append("🔥 VALID LONG OB FORMED!")
        else:
            reasons.append(f"In Mid-Range (PDH {dist_pdh:+.2f}%, PDL {dist_pdl:+.2f}%)")

        print(f"#{symbol:<12} | Price: ${price:<9.4f} | PDH: ${pdh:<9.4f} | PDL: ${pdl:<9.4f} | {' | '.join(reasons)}")

if __name__ == "__main__":
    diagnose()
