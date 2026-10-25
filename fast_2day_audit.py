import asyncio
import sys
from datetime import datetime, timezone, timedelta
from feed.binance_feed import binance_feed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))

async def test_fet_and_recent():
    print("=" * 75)
    print("🔍 AUDITING LAST 2 DAYS ON LIVE REAL CANDLES (29 & 30 SEP 2026)")
    print("=" * 75)

    klines_1h = await binance_feed.fetch_klines("FETUSDT", interval="1h", limit=80)
    print(f"Fetched {len(klines_1h)} 1H candles for FETUSDT")
    
    # Check candles around 30-Sep
    for c in klines_1h[-30:]:
        t_ist = datetime.fromtimestamp(c["time"]/1000, tz=IST).strftime("%d-%b %I:%M %p")
        print(f"{t_ist} | O: {c['open']:.4f} | H: {c['high']:.4f} | L: {c['low']:.4f} | C: {c['close']:.4f} | Vol: {c['volume']:.0f}")

    # Now let's test all 22 coins across last 2 days
    from engine.hermes2_apex_live import TOP_22_CHAMPIONS
    btc_4h = await binance_feed.fetch_klines("BTCUSDT", interval="4h", limit=40)
    btc_map_4h = {c["time"]: c for c in btc_4h}
    
    START_2DAY_MS = int(datetime(2026, 9, 29, 0, 0, 0, tzinfo=IST).timestamp() * 1000)
    END_2DAY_MS = int(datetime(2026, 9, 30, 23, 59, 59, tzinfo=IST).timestamp() * 1000)

    all_2day_setups = []

    for sym in TOP_22_CHAMPIONS:
        for tf in ["4h", "1h"]:
            candles = await binance_feed.fetch_klines(sym, interval=tf, limit=80)
            n = len(candles)
            if n < 30:
                continue
            min_disp = 0.050 if tf == "4h" else 0.035
            tp_pct = 0.028 if tf == "4h" else 0.022
            soft_sl_pct = 0.028 if tf == "4h" else 0.022
            hard_sl_pct = 0.038 if tf == "4h" else 0.032

            for i in range(15, n - 2):
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
                                            if START_2DAY_MS <= tap_time <= END_2DAY_MS:
                                                c_range = tap_c["high"] - tap_c["low"]
                                                swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                                l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                                w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                                mt = (dec_top + dec_bot) / 2.0
                                                if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                                    all_2day_setups.append({
                                                        "sym": sym, "tf": tf, "side": "LONG", "time": tap_time,
                                                        "t_idx": t, "candles": candles, "dec_top": dec_top, "dec_bot": dec_bot,
                                                        "mt": mt, "tap_c": tap_c, "tp_pct": tp_pct, "soft_sl_pct": soft_sl_pct,
                                                        "hard_sl_pct": hard_sl_pct, "w_ratio": w_ratio
                                                    })
                                                    break

    print(f"\nTotal candidate setups found in last 2 days: {len(all_2day_setups)}")
    for s in all_2day_setups:
        t_ist = datetime.fromtimestamp(s["time"]/1000, tz=IST).strftime("%d-%b %I:%M %p")
        print(f"Setup: {t_ist} | {s['sym']} {s['side']} ({s['tf'].upper()}) | OB Top: {s['dec_top']} | MT: {s['mt']:.4f} | OB Bot: {s['dec_bot']}")

if __name__ == "__main__":
    asyncio.run(test_fet_and_recent())
