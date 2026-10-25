import urllib.request
import json
import time
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "AVAXUSDT", "SUIUSDT", "NEARUSDT", "1000PEPEUSDT", "APTUSDT"]

def fetch_klines(sym, interval="1h", limit=100):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        candles = []
        for k in data:
            candles.append({
                "time": k[0],
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5])
            })
        return candles
    except Exception as e:
        return []

print("="*80)
print("🔍 SCANNING LAST 48 HOURS (2 DAYS) OF LIVE BINANCE FUTURES MARKET DATA")
print("="*80)

setups_found = []
executed_trades = []

# Scan 1H and 4H
for sym in TOP_COINS:
    for tf in ["1h", "4h"]:
        candles = fetch_klines(sym, interval=tf, limit=100)
        if len(candles) < 40:
            continue
        
        n = len(candles)
        # Scan for Hermes 3.5 setups formed in the last 48 hours
        # 48 hours = last 48 candles on 1h, last 12 candles on 4h
        lookback_bars = 48 if tf == "1h" else 12
        cutoff_time = candles[-lookback_bars]["time"]
        
        tp_pct = 0.022 if tf == "1h" else 0.028
        soft_sl_pct = 0.025 if tf == "1h" else 0.028
        
        for i in range(20, n - 5):
            # Check if this impulse formed within the last 48h
            if candles[i]["time"] < cutoff_time:
                continue
                
            # Bullish check
            if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                sub_w = candles[i:min(i+16, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx > i + 2:
                    gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                    if gain >= 0.045:
                        idm_low = candles[high_idx-1]["low"]
                        # find decisional OB
                        for mid in range(i+1, high_idx):
                            fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                            if 0.30 <= fib <= 0.70:
                                dec_c = candles[mid-1]
                                dec_top = max(dec_c["open"], dec_c["close"])
                                dec_bot = dec_c["low"]
                                mt = (dec_top + dec_bot) / 2.0
                                # check tap
                                for t in range(high_idx+1, n):
                                    if candles[t]["low"] <= dec_top * 1.0005:
                                        tap_c = candles[t]
                                        swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t+1))
                                        c_range = max(tap_c["high"] - tap_c["low"], 1e-6)
                                        w_ratio = (min(tap_c["open"], tap_c["close"]) - tap_c["low"]) / c_range
                                        if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                            entry = dec_top
                                            tp_p = entry * (1.0 + tp_pct)
                                            sl_p = entry * (1.0 - soft_sl_pct)
                                            # forward simulate to current bar
                                            status = "OPEN"
                                            pnl = (candles[-1]["close"] - entry) / entry
                                            for m in range(t+1, n):
                                                if candles[m]["high"] >= tp_p:
                                                    status = "TP_HIT (+2.2%)"
                                                    pnl = tp_pct
                                                    break
                                                if candles[m]["close"] <= sl_p:
                                                    status = "SL_HIT (-2.5%)"
                                                    pnl = -soft_sl_pct
                                                    break
                                            dt = datetime.fromtimestamp(tap_c["time"]/1000.0, tz=timezone.utc)
                                            executed_trades.append({
                                                "sym": sym, "tf": tf, "side": "LONG",
                                                "tap_time": dt.strftime("%Y-%m-%d %H:%M UTC"),
                                                "entry": entry, "tp": tp_p, "sl": sl_p,
                                                "status": status, "pnl_pct": round(pnl*100, 2)
                                            })
                                        break
                                break

            # Bearish check
            if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                sub_w = candles[i:min(i+16, n)]
                lows = [c["low"] for c in sub_w]
                min_low = min(lows)
                low_idx = i + lows.index(min_low)
                if low_idx > i + 2:
                    drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                    if drop >= 0.045:
                        idm_high = candles[low_idx-1]["high"]
                        for mid in range(i+1, low_idx):
                            fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                            if 0.30 <= fib <= 0.70:
                                dec_c = candles[mid-1]
                                dec_top = dec_c["high"]
                                dec_bot = min(dec_c["open"], dec_c["close"])
                                mt = (dec_top + dec_bot) / 2.0
                                for t in range(low_idx+1, n):
                                    if candles[t]["high"] >= dec_bot * 0.9995:
                                        tap_c = candles[t]
                                        swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t+1))
                                        c_range = max(tap_c["high"] - tap_c["low"], 1e-6)
                                        w_ratio = (tap_c["high"] - max(tap_c["open"], tap_c["close"])) / c_range
                                        if swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                            entry = dec_bot
                                            tp_p = entry * (1.0 - tp_pct)
                                            sl_p = entry * (1.0 + soft_sl_pct)
                                            status = "OPEN"
                                            pnl = (entry - candles[-1]["close"]) / entry
                                            for m in range(t+1, n):
                                                if candles[m]["low"] <= tp_p:
                                                    status = "TP_HIT (+2.2%)"
                                                    pnl = tp_pct
                                                    break
                                                if candles[m]["close"] >= sl_p:
                                                    status = "SL_HIT (-2.5%)"
                                                    pnl = -soft_sl_pct
                                                    break
                                            dt = datetime.fromtimestamp(tap_c["time"]/1000.0, tz=timezone.utc)
                                            executed_trades.append({
                                                "sym": sym, "tf": tf, "side": "SHORT",
                                                "tap_time": dt.strftime("%Y-%m-%d %H:%M UTC"),
                                                "entry": entry, "tp": tp_p, "sl": sl_p,
                                                "status": status, "pnl_pct": round(pnl*100, 2)
                                            })
                                        break
                                break

print(f"Total Trades Identified in Last 48 Hours: {len(executed_trades)}")
for t in executed_trades:
    print(t)
