"""
Forensic Audit of all 4H Trade Setups Formed on Today (28-Sep-2026) across Top-22 Champions.
Compares trades taken by the bot vs setups that formed while the queue was occupied,
and verifies their forward market outcome.
"""

import sys
import json
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))
TODAY_START_MS = int(datetime(2026, 9, 28, 0, 0, 0, tzinfo=IST).timestamp() * 1000)
NOW_MS = int(time.time() * 1000)

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

BINANCE_BASE = "https://data-api.binance.vision/api/v3/klines"

def fetch_klines(symbol: str, interval: str = "4h", limit: int = 150) -> List[Dict[str, Any]]:
    # Handle SHIB 1000 multiplier
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
        # Fallback to standard symbol
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
    print("[*] Fetching BTC 4H benchmark...")
    btc_candles = fetch_klines("BTCUSDT", "4h", 100)
    btc_map_4h = {c["time"]: c for c in btc_candles}

    print("[*] Fetching live trades taken by bot from Render API...")
    bot_trades = []
    try:
        url = "https://smc-ai-agent.onrender.com/api/paper/trades"
        data = json.loads(urllib.request.urlopen(url).read())
        for t in data.get("trades", []):
            if str(t.get("timeframe", "")).upper() == "4H" and "2026-09-28" in str(t.get("timestamp_ist", "")):
                bot_trades.append(t)
    except Exception as e:
        print(f"Error fetching bot trades: {e}")

    print(f"[*] Bot took {len(bot_trades)} trades on 4H today.")

    all_todays_setups = []

    for sym in TOP_22_CHAMPIONS:
        candles = fetch_klines(sym, "4h", 100)
        n = len(candles)
        if n < 30:
            continue

        tp_pct = 0.028
        soft_sl_pct = 0.028
        hard_sl_pct = 0.038
        min_displacement = 0.050
        max_tap_window = 28

        for i in range(15, n - 2):
            # 1. LONG SETUP CHECK
            if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                sub_w = candles[i:min(i+16, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx > i + 2:
                    gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                    if gain >= min_displacement:
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
                                for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                    tap_c = candles[t]
                                    if tap_c["low"] <= dec_top * 1.0005:
                                        tap_time = tap_c["time"]
                                        if tap_time >= TODAY_START_MS:
                                            # Sentry 1 BTC Brake
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                            sentry1_ok = btc_dump < 0.020

                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                            l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                            w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            if swept and w_ratio >= 0.18 and tap_c["close"] >= mt and sentry1_ok:
                                                entry = dec_top
                                                tp_p = entry * (1.0 + tp_pct)
                                                sl_p = entry * (1.0 - soft_sl_pct)

                                                # Simulate forward
                                                result = "IN_PROGRESS"
                                                highest = entry
                                                lowest = entry
                                                exit_time = None
                                                exit_price = None

                                                for f in range(t + 1, n):
                                                    bar = candles[f]
                                                    highest = max(highest, bar["high"])
                                                    lowest = min(lowest, bar["low"])

                                                    if bar["high"] >= tp_p:
                                                        result = "TP_HIT (+14.0% ROE)"
                                                        exit_time = bar["time"]
                                                        exit_price = tp_p
                                                        break
                                                    elif bar["low"] <= sl_p:
                                                        result = "SL_HIT (-14.0% ROE)"
                                                        exit_time = bar["time"]
                                                        exit_price = sl_p
                                                        break

                                                all_todays_setups.append({
                                                    "symbol": sym,
                                                    "side": "LONG",
                                                    "entry": entry,
                                                    "tp": tp_p,
                                                    "sl": sl_p,
                                                    "tap_time": tap_time,
                                                    "tap_time_ist": datetime.fromtimestamp(tap_time / 1000, IST).strftime("%Y-%m-%d %H:%M:%S IST"),
                                                    "result": result,
                                                    "highest_mfe": round((highest - entry) / entry * 100 * 5, 2),
                                                    "lowest_mae": round((entry - lowest) / entry * 100 * 5, 2)
                                                })
                                        break

            # 2. SHORT SETUP CHECK
            if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
                sub_w = candles[i:min(i+16, n)]
                lows = [c["low"] for c in sub_w]
                min_low = min(lows)
                low_idx = i + lows.index(min_low)
                if low_idx > i + 2:
                    drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                    if drop >= min_displacement:
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
                            dec_top = dec_c["high"]
                            dec_bot = min(dec_c["open"], dec_c["close"])
                            has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False

                            if has_bear_fvg:
                                for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                    tap_c = candles[t]
                                    if tap_c["high"] >= dec_bot * 1.0005:
                                        tap_time = tap_c["time"]
                                        if tap_time >= TODAY_START_MS:
                                            # Sentry 1 BTC Macro Pump check (< 2%)
                                            curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                            prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                            btc_c = btc_map_4h.get(prev_4h_ts)
                                            btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                            sentry1_ok = btc_pump < 0.020

                                            c_range = tap_c["high"] - tap_c["low"]
                                            swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                            u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                            w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                            mt = (dec_top + dec_bot) / 2.0

                                            if swept and w_ratio >= 0.18 and tap_c["close"] <= mt and sentry1_ok:
                                                entry = dec_bot
                                                tp_p = entry * (1.0 - tp_pct)
                                                sl_p = entry * (1.0 + soft_sl_pct)

                                                # Simulate forward
                                                result = "IN_PROGRESS"
                                                lowest = entry
                                                highest = entry
                                                for f in range(t + 1, n):
                                                    bar = candles[f]
                                                    lowest = min(lowest, bar["low"])
                                                    highest = max(highest, bar["high"])

                                                    if bar["low"] <= tp_p:
                                                        result = "TP_HIT (+14.0% ROE)"
                                                        break
                                                    elif bar["high"] >= sl_p:
                                                        result = "SL_HIT (-14.0% ROE)"
                                                        break

                                                all_todays_setups.append({
                                                    "symbol": sym,
                                                    "side": "SHORT",
                                                    "entry": entry,
                                                    "tp": tp_p,
                                                    "sl": sl_p,
                                                    "tap_time": tap_time,
                                                    "tap_time_ist": datetime.fromtimestamp(tap_time / 1000, IST).strftime("%Y-%m-%d %H:%M:%S IST"),
                                                    "result": result,
                                                    "highest_mfe": round((entry - lowest) / entry * 100 * 5, 2),
                                                    "lowest_mae": round((highest - entry) / entry * 100 * 5, 2)
                                                })
                                        break

    # Deduplicate setups by symbol, side, entry
    unique_setups = []
    seen = set()
    for s in all_todays_setups:
        sig = (s["symbol"], s["side"], round(s["entry"], 4), s["tap_time"])
        if sig not in seen:
            seen.add(sig)
            unique_setups.append(s)

    unique_setups.sort(key=lambda x: x["tap_time"])

    with open("todays_4h_setups_forensic.json", "w", encoding="utf-8") as f:
        json.dump(unique_setups, f, indent=2)

    print(f"\n================================================================================")
    print(f"📊 ALL 4H SETUPS FORMED TODAY (28-SEP-2026): Total {len(unique_setups)} Setups")
    print(f"================================================================================")
    for idx, s in enumerate(unique_setups, 1):
        print(f"#{idx} | {s['symbol']} | {s['side']} | Entry: {s['entry']} | TP: {s['tp']} | SL: {s['sl']} | Triggered: {s['tap_time_ist']} | Result: {s['result']} | MFE: +{s['highest_mfe']}%")

if __name__ == "__main__":
    main()
