import urllib.request
import json
import time
import sys
import numpy as np
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def fetch_data_pair(sym):
    url_k = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=1h&limit=500"
    url_oi = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={sym}&period=1h&limit=500"
    
    candles = []
    running_cvd = 0.0
    try:
        req_k = urllib.request.Request(url_k, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_k, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            for k in data:
                t = int(k[0])
                o = float(k[1])
                h = float(k[2])
                l = float(k[3])
                c = float(k[4])
                vol = float(k[5])
                taker_buy = float(k[9]) if len(k) > 9 else vol * 0.5
                taker_sell = max(0.0, vol - taker_buy)
                delta = taker_buy - taker_sell
                running_cvd += delta
                candles.append({
                    "time": t, "open": o, "high": h, "low": l, "close": c,
                    "volume": vol, "taker_buy": taker_buy, "taker_sell": taker_sell,
                    "delta": delta, "cvd": running_cvd
                })
    except Exception as e:
        print(f"Error klines for {sym}: {e}", flush=True)

    oi_map = {}
    try:
        req_oi = urllib.request.Request(url_oi, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_oi, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            for item in data:
                ts = int(item["timestamp"])
                oi = float(item["sumOpenInterest"])
                oi_map[ts] = oi
    except Exception as e:
        print(f"Error OI for {sym}: {e}", flush=True)

    return sym, candles, oi_map

def run_analysis():
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "SUIUSDT", "DOGEUSDT", "AVAXUSDT", "UNIUSDT", "NEARUSDT", "ARBUSDT"]
    print("Fetching data concurrently...", flush=True)
    all_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_data_pair, s) for s in symbols]
        for f in concurrent.futures.as_completed(futures):
            s, c, o = f.result()
            all_data[s] = (c, o)
            print(f"Loaded {s}: {len(c)} candles, {len(o)} OI points", flush=True)

    tp_pct = 0.015    # +1.50% move
    be_pct = 0.0075   # +0.75% move
    sl_pct = 0.020    # -2.00% move

    records = []
    for sym, (candles, oi_map) in all_data.items():
        if len(candles) < 80:
            continue

        for i in range(15, len(candles) - 15):
            c = candles[i]
            # Order Block condition
            is_bullish_ob = (c["close"] < c["open"]) and (i + 2 < len(candles))
            if not is_bullish_ob:
                continue

            ob_high = c["high"]
            ob_low = c["low"]
            max_rally = max(candles[i+1]["high"], candles[i+2]["high"])
            if (max_rally - ob_high) / ob_high < 0.015:
                continue

            entry_p = ob_high
            tp_target = entry_p * (1.0 + tp_pct)
            be_target = entry_p * (1.0 + be_pct)
            sl_target = entry_p * (1.0 - sl_pct)

            entry_idx = -1
            for k in range(i + 3, min(i + 45, len(candles))):
                if candles[k]["low"] <= entry_p and candles[k]["high"] >= entry_p:
                    entry_idx = k
                    break

            if entry_idx == -1:
                continue

            entry_c = candles[entry_idx]
            entry_ts = entry_c["time"]

            d_ratio = entry_c["taker_buy"] / entry_c["volume"] if entry_c["volume"] > 0 else 0.5
            
            # CVD trend leading to entry: did selling taper off?
            cvd_prev3 = candles[entry_idx - 3]["cvd"] if entry_idx >= 3 else candles[0]["cvd"]
            cvd_reversal = (entry_c["cvd"] - cvd_prev3) > 0 # CVD turning back up on OB touch

            # OI change over previous 1h and 4h
            oi_curr = oi_map.get(entry_ts, 0.0)
            oi_1h_prev = oi_map.get(entry_ts - 3600000, 0.0)
            oi_1h_chg = ((oi_curr - oi_1h_prev) / oi_1h_prev * 100) if (oi_1h_prev > 0 and oi_curr > 0) else 0.0

            # Forward outcome
            trade_res = None
            be_active = False
            bars = 0
            for m in range(entry_idx, min(entry_idx + 40, len(candles))):
                curr = candles[m]
                bars += 1
                if not be_active and curr["high"] >= be_target:
                    be_active = True
                if curr["high"] >= tp_target:
                    trade_res = "WIN"
                    break
                if be_active and curr["low"] <= entry_p:
                    trade_res = "BREAKEVEN"
                    break
                if curr["close"] <= sl_target:
                    trade_res = "LOSS"
                    break

            if not trade_res:
                trade_res = "BREAKEVEN" if be_active else "LOSS"

            records.append({
                "symbol": sym,
                "result": trade_res,
                "bars": bars,
                "d_ratio": d_ratio,
                "cvd_reversal": cvd_reversal,
                "oi_1h_chg": oi_1h_chg
            })

    print(f"\n=========================================================================================")
    print(f"                      SMC V17 + CVD & OI CONFLUENCE BACKTEST MATRIX")
    print(f"=========================================================================================")
    print(f"Total historical trades captured: {len(records)}\n")

    def test_filter(name, func):
        sub = [r for r in records if func(r)]
        if not sub:
            return
        n = len(sub)
        w = sum(1 for r in sub if r["result"] == "WIN")
        b = sum(1 for r in sub if r["result"] == "BREAKEVEN")
        l = sum(1 for r in sub if r["result"] == "LOSS")
        wr = w / n * 100
        lr = l / n * 100
        avg_h = np.mean([r["bars"] for r in sub if r["result"] == "WIN"]) if w > 0 else 0
        safety = (w + b) / n * 100
        print(f"  {name:<48} | N={n:>3} | WR={wr:>5.1f}% | Loss={lr:>4.1f}% | Safety={safety:>5.1f}% | TP Time={avg_h:.1f}h")

    test_filter("1. BASELINE SMC (No Filter)", lambda r: True)
    test_filter("2. DELTA ABSORPTION (Taker Buy Ratio >= 51%)", lambda r: r["d_ratio"] >= 0.51)
    test_filter("3. DELTA BUY DOMINANCE (Taker Buy Ratio >= 54%)", lambda r: r["d_ratio"] >= 0.54)
    test_filter("4. CVD REVERSAL (CVD Turns Up on OB Retest)", lambda r: r["cvd_reversal"])
    test_filter("5. OI ACCUMULATION (+OI Change > 0.0%)", lambda r: r["oi_1h_chg"] > 0.0)
    test_filter("6. STRONG OI EXPANSION (+OI Change > +0.5%)", lambda r: r["oi_1h_chg"] > 0.5)
    test_filter("7. CVD REVERSAL + OI EXPANSION (+OI > 0)", lambda r: r["cvd_reversal"] and r["oi_1h_chg"] > 0.0)
    test_filter("8. DELTA >= 52% + CVD REVERSAL + OI > 0", lambda r: r["d_ratio"] >= 0.52 and r["cvd_reversal"] and r["oi_1h_chg"] > 0.0)
    print("=========================================================================================\n")

if __name__ == "__main__":
    run_analysis()
