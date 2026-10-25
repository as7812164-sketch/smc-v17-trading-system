import sys
import json
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))

# Window: Last 2 Days (29-Sep-2026 00:00:00 IST to 30-Sep-2026 23:59:59 IST)
START_2DAY_MS = int(datetime(2026, 9, 29, 0, 0, 0, tzinfo=IST).timestamp() * 1000)
END_2DAY_MS = int(datetime(2026, 9, 30, 23, 59, 59, tzinfo=IST).timestamp() * 1000)

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SOLUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

BINANCE_BASE = "https://data-api.binance.vision/api/v3/klines"

def fetch_klines(symbol: str, interval: str = "1h", limit: int = 200) -> List[Dict[str, Any]]:
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
        return []

def main():
    print("=" * 75)
    print("🔬 AUDITING LAST 2 DAYS (29-SEP & 30-SEP) ON REAL BINANCE MARKET CANDLES")
    print(f"Window: {datetime.fromtimestamp(START_2DAY_MS/1000, tz=IST)} to {datetime.fromtimestamp(END_2DAY_MS/1000, tz=IST)}")
    print("=" * 75)

    btc_4h = fetch_klines("BTCUSDT", "4h", 120)
    btc_map_4h = {c["time"]: c for c in btc_4h}
    btc_1h = fetch_klines("BTCUSDT", "1h", 200)
    btc_map_1h = {c["time"]: c for c in btc_1h}

    # Harvest all setups that triggered in these 2 days
    setups_2days = []

    for tf in ["4h", "1h"]:
        min_disp = 0.050 if tf == "4h" else 0.035
        std_tp_pct = 0.028 if tf == "4h" else 0.022
        soft_sl_pct = 0.028 if tf == "4h" else 0.022
        hard_sl_pct = 0.038 if tf == "4h" else 0.032
        max_tap_window = 28
        limit = 150 if tf == "4h" else 200

        for sym in TOP_22_CHAMPIONS:
            candles = fetch_klines(sym, tf, limit)
            n = len(candles)
            if n < 40:
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
                                    for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                        tap_c = candles[t]
                                        if tap_c["low"] <= dec_top * 1.0005:
                                            tap_time = tap_c["time"]
                                            if START_2DAY_MS <= tap_time <= END_2DAY_MS:
                                                c_range = tap_c["high"] - tap_c["low"]
                                                swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                                l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                                w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                                mt = (dec_top + dec_bot) / 2.0

                                                curr_4h = tap_time - (tap_time % (4 * 3600 * 1000))
                                                prev_4h = curr_4h - 4 * 3600 * 1000
                                                b_c = btc_map_4h.get(prev_4h)
                                                b_dump = (b_c["open"] - b_c["close"]) / b_c["open"] if b_c else 0.0
                                                b_clean = b_dump < 0.020

                                                if b_clean and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                    setups_2days.append({
                                                        "sym": sym, "tf": tf, "side": "LONG", "time": tap_time,
                                                        "t_idx": t, "candles": candles, "dec_top": dec_top, "dec_bot": dec_bot,
                                                        "mt": mt, "tap_c": tap_c, "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                        "hard_sl_pct": hard_sl_pct, "wick_ratio": w_ratio, "gain": gain
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
                                bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
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
                                        if tap_c["high"] >= dec_bot * 0.9995:
                                            tap_time = tap_c["time"]
                                            if START_2DAY_MS <= tap_time <= END_2DAY_MS:
                                                c_range = tap_c["high"] - tap_c["low"]
                                                swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                                u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                                w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                                mt = (dec_top + dec_bot) / 2.0

                                                curr_4h = tap_time - (tap_time % (4 * 3600 * 1000))
                                                prev_4h = curr_4h - 4 * 3600 * 1000
                                                b_c = btc_map_4h.get(prev_4h)
                                                b_pump = (b_c["close"] - b_c["open"]) / b_c["open"] if b_c else 0.0
                                                b_clean_short = b_pump < 0.020

                                                if b_clean_short and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                                    setups_2days.append({
                                                        "sym": sym, "tf": tf, "side": "SHORT", "time": tap_time,
                                                        "t_idx": t, "candles": candles, "dec_top": dec_top, "dec_bot": dec_bot,
                                                        "mt": mt, "tap_c": tap_c, "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                        "hard_sl_pct": hard_sl_pct, "wick_ratio": w_ratio, "gain": drop
                                                    })
                                                    break

    setups_2days.sort(key=lambda x: x["time"])
    print(f"Total triggered candidate setups in last 2 days: {len(setups_2days)}")

    # SIMULATE HERMES 2.5 VS HERMES 3.0 ON THESE SETUPS
    for engine_name in ["HERMES_2.5_APEX_HYBRID", "HERMES_3.0_QUANTUM"]:
        print(f"\n================= {engine_name} SIMULATION =================")
        trades_executed = []
        for s in setups_2days:
            sym = s["sym"]
            tf = s["tf"]
            side = s["side"]
            candles = s["candles"]
            t = s["t_idx"]
            n = len(candles)
            tap_c = s["tap_c"]
            mt = s["mt"]
            time_ist = datetime.fromtimestamp(s["time"]/1000, tz=IST).strftime("%d-%b %I:%M %p")

            if engine_name == "HERMES_2.5_APEX_HYBRID":
                entry = s["dec_top"] if side == "LONG" else s["dec_bot"]
                tp = entry * (1.0 + s["std_tp_pct"]) if side == "LONG" else entry * (1.0 - s["std_tp_pct"])
                sl = entry * (1.0 - s["soft_sl_pct"]) if side == "LONG" else entry * (1.0 + s["soft_sl_pct"])
                hard_sl = entry * (1.0 - s["hard_sl_pct"]) if side == "LONG" else entry * (1.0 + s["hard_sl_pct"])
            else: # HERMES 3.0
                if side == "LONG":
                    entry = mt if tap_c["low"] <= mt else (s["dec_top"] + mt) / 2.0
                    tp = entry * (1.0 + s["std_tp_pct"])
                    hard_sl = min(s["dec_bot"] - 0.005 * entry, entry * (1.0 - s["hard_sl_pct"]))
                    sl = (entry + hard_sl) / 2.0
                else:
                    entry = mt if tap_c["high"] >= mt else (s["dec_bot"] + mt) / 2.0
                    tp = entry * (1.0 - s["std_tp_pct"])
                    hard_sl = max(s["dec_top"] + 0.005 * entry, entry * (1.0 + s["hard_sl_pct"]))
                    sl = (entry + hard_sl) / 2.0

            # Forward track outcome
            outcome = "OPEN"
            exit_price = entry
            exit_bar = t
            current_sl = sl
            be_locked = False

            for m in range(t + 1, min(t + 40, n)):
                cm = candles[m]
                if side == "LONG":
                    # Stage 1 Profit armor
                    if cm["high"] >= entry * 1.016:
                        current_sl = max(current_sl, entry * 1.002)
                        be_locked = True
                    if cm["high"] >= entry * 1.022 and engine_name == "HERMES_3.0_QUANTUM":
                        current_sl = max(current_sl, entry * 1.012)
                    
                    if cm["high"] >= tp:
                        outcome = "TP_HIT"
                        exit_price = tp
                        exit_bar = m
                        break
                    if cm["low"] <= hard_sl:
                        outcome = "SL_HIT"
                        exit_price = hard_sl
                        exit_bar = m
                        break
                    if cm["close"] <= current_sl:
                        outcome = "BE_PROFIT" if be_locked and current_sl > entry else "SOFT_SL"
                        exit_price = cm["close"]
                        exit_bar = m
                        break
                else:
                    if cm["low"] <= entry * 0.984:
                        current_sl = min(current_sl, entry * 0.998)
                        be_locked = True
                    if cm["low"] <= entry * 0.978 and engine_name == "HERMES_3.0_QUANTUM":
                        current_sl = min(current_sl, entry * 0.988)

                    if cm["low"] <= tp:
                        outcome = "TP_HIT"
                        exit_price = tp
                        exit_bar = m
                        break
                    if cm["high"] >= hard_sl:
                        outcome = "SL_HIT"
                        exit_price = hard_sl
                        exit_bar = m
                        break
                    if cm["close"] >= current_sl:
                        outcome = "BE_PROFIT" if be_locked and current_sl < entry else "SOFT_SL"
                        exit_price = cm["close"]
                        exit_bar = m
                        break

            # Calculate PnL (at $50 margin, 5x leverage = $250 position)
            pos = 250.0
            if side == "LONG":
                pct = (exit_price - entry) / entry * 100.0
            else:
                pct = (entry - exit_price) / entry * 100.0
            pnl = pos * (pct / 100.0) - (pos * 0.0016)
            roe = pct * 5.0

            trades_executed.append({
                "sym": sym, "tf": tf, "side": side, "time": time_ist,
                "entry": entry, "exit": exit_price, "outcome": outcome,
                "pct": pct, "pnl": pnl, "roe": roe
            })
            print(f"• {time_ist} | {sym:8s} | {side:5s} ({tf.upper()}) | Entry: {entry:.4f} | Exit: {exit_price:.4f} | Outcome: {outcome:10s} | PnL: ${pnl:+6.2f} (ROE: {roe:+5.1f}%)")

        wins = sum(1 for t in trades_executed if t["pnl"] > 0)
        losses = sum(1 for t in trades_executed if t["pnl"] <= 0)
        tot_pnl = sum(t["pnl"] for t in trades_executed)
        print(f"Total: {len(trades_executed)} trades | Wins: {wins} | Losses: {losses} | Net PnL: ${tot_pnl:+.2f} USDT")

if __name__ == "__main__":
    main()
