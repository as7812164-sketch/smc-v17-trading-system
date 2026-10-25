import sys
import json
import time
import urllib.request
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))
# 29 Sep 2026 IST window:
# 29-Sep-2026 00:00:00 IST to 29-Sep-2026 23:59:59 IST
START_29_MS = int(datetime(2026, 9, 29, 0, 0, 0, tzinfo=IST).timestamp() * 1000)
END_29_MS = int(datetime(2026, 9, 29, 23, 59, 59, tzinfo=IST).timestamp() * 1000)

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

BINANCE_BASE = "https://data-api.binance.vision/api/v3/klines"

def fetch_klines(symbol: str, interval: str = "4h", limit: int = 150) -> List[Dict[str, Any]]:
    api_sym = symbol
    if symbol == "SHIBUSDT":
        api_sym = "1000SHIBUSDT"
    url = f"{BINANCE_BASE}?symbol={api_sym}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candles = []
            for c in data:
                candles.append({
                    "time": int(c[0]),
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": float(c[5])
                })
            return candles
    except Exception as e:
        if api_sym != symbol:
            try:
                url = f"{BINANCE_BASE}?symbol={symbol}&interval={interval}&limit={limit}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return [{"time": int(c[0]), "open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4]), "volume": float(c[5])} for c in data]
            except Exception:
                pass
        return []

def main():
    print(f"[*] Auditing Yesterday: 29-Sep-2026 IST ({datetime.fromtimestamp(START_29_MS/1000, tz=IST)} to {datetime.fromtimestamp(END_29_MS/1000, tz=IST)})")

    # Fetch DB executed trades
    conn = sqlite3.connect("database/smc_v17.db")
    conn.row_factory = sqlite3.Row
    db_trades = conn.execute("""
        SELECT * FROM paper_trades 
        WHERE entry_time >= ? AND entry_time <= ?
        ORDER BY entry_time ASC
    """, (START_29_MS, END_29_MS)).fetchall()
    
    taken_trades = [dict(t) for t in db_trades]
    print(f"[*] Bot executed {len(taken_trades)} trades yesterday.")

    btc_candles = fetch_klines("BTCUSDT", "4h", 120)
    btc_map_4h = {c["time"]: c for c in btc_candles}

    # Detect all setups that qualified & tapped yesterday across 4H & 1H
    all_setups = []

    for tf in ["4h", "1h"]:
        limit = 120 if tf == "4h" else 150
        min_disp = 0.050 if tf == "4h" else 0.035
        tp_pct = 0.028 if tf == "4h" else 0.022
        soft_sl_pct = 0.028 if tf == "4h" else 0.022
        hard_sl_pct = 0.038 if tf == "4h" else 0.030

        for sym in TOP_22_CHAMPIONS:
            candles = fetch_klines(sym, tf, limit)
            n = len(candles)
            if n < 30:
                continue

            for i in range(15, n - 2):
                # LONG CHECK
                if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    highs = [c["high"] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 2:
                        gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                        if gain >= min_disp:
                            idm_low = candles[high_idx - 1]["low"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, high_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid

                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False

                                if has_fvg:
                                    for t in range(high_idx + 1, min(high_idx + 28, n)):
                                        tap_c = candles[t]
                                        if tap_c["low"] <= dec_top * 1.0005:
                                            tap_time = tap_c["time"]
                                            if START_29_MS <= tap_time <= END_29_MS:
                                                c_range = tap_c["high"] - tap_c["low"]
                                                swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                                l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                                w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                                mt = (dec_top + dec_bot) / 2.0

                                                if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                    entry_p = dec_top
                                                    target_tp = entry_p * (1.0 + tp_pct)
                                                    hard_sl = entry_p * (1.0 - hard_sl_pct)

                                                    # Check forward outcome
                                                    outcome = "STILL_OPEN"
                                                    for fwd in range(t + 1, n):
                                                        fc = candles[fwd]
                                                        if fc["high"] >= target_tp:
                                                            outcome = "TP_HIT"
                                                            break
                                                        elif fc["low"] <= hard_sl:
                                                            outcome = "SL_HIT"
                                                            break

                                                    all_setups.append({
                                                        "symbol": sym,
                                                        "side": "LONG",
                                                        "timeframe": tf,
                                                        "tap_time": tap_time,
                                                        "entry_price": entry_p,
                                                        "tp_price": target_tp,
                                                        "sl_price": hard_sl,
                                                        "outcome": outcome
                                                    })
                                            break

                # SHORT CHECK
                if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
                    sub_w = candles[i:min(i+16, n)]
                    lows = [c["low"] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 2:
                        drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                        if drop >= min_disp:
                            idm_high = candles[low_idx - 1]["high"]
                            best_mid = -1
                            max_bg = 0.0
                            for mid in range(i+1, low_idx):
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                                fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                                if 0.30 <= fib <= 0.70 and bg > max_bg:
                                    max_bg = bg
                                    best_mid = mid

                            if best_mid != -1:
                                dec_c = candles[best_mid - 1]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                dec_top = dec_c["high"]
                                has_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False

                                if has_fvg:
                                    for t in range(low_idx + 1, min(low_idx + 28, n)):
                                        tap_c = candles[t]
                                        if tap_c["high"] >= dec_bot * 0.9995:
                                            tap_time = tap_c["time"]
                                            if START_29_MS <= tap_time <= END_29_MS:
                                                c_range = tap_c["high"] - tap_c["low"]
                                                swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                                u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                                w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                                mt = (dec_top + dec_bot) / 2.0

                                                if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                    entry_p = dec_bot
                                                    target_tp = entry_p * (1.0 - tp_pct)
                                                    hard_sl = entry_p * (1.0 + hard_sl_pct)

                                                    outcome = "STILL_OPEN"
                                                    for fwd in range(t + 1, n):
                                                        fc = candles[fwd]
                                                        if fc["low"] <= target_tp:
                                                            outcome = "TP_HIT"
                                                            break
                                                        elif fc["high"] >= hard_sl:
                                                            outcome = "SL_HIT"
                                                            break

                                                    all_setups.append({
                                                        "symbol": sym,
                                                        "side": "SHORT",
                                                        "timeframe": tf,
                                                        "tap_time": tap_time,
                                                        "entry_price": entry_p,
                                                        "tp_price": target_tp,
                                                        "sl_price": hard_sl,
                                                        "outcome": outcome
                                                    })
                                            break

    print(f"\n==================== TOTAL SETUPS FORMED YESTERDAY: {len(all_setups)} ====================")
    for s in all_setups:
        t_dt = datetime.fromtimestamp(s["tap_time"]/1000, tz=IST)
        # Check if this setup was executed in taken_trades
        is_taken = False
        trade_id = None
        for tk in taken_trades:
            if tk["symbol"] == s["symbol"] and tk["side"].upper() == s["side"].upper():
                if abs(tk["entry_time"] - s["tap_time"]) < 3600 * 1000 * 4:
                    is_taken = True
                    trade_id = tk["id"]
                    break
        
        status_label = f"TAKEN (Trade #{trade_id})" if is_taken else "NOT TAKEN (Queue Occupied)"
        print(f"• {s['symbol']:10s} | {s['side']:5s} ({s['timeframe'].upper()}) | Tap Time: {t_dt.strftime('%d-%b %I:%M %p')} | Status: {status_label:25s} | Outcome: {s['outcome']}")

if __name__ == "__main__":
    main()
