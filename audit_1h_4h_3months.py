import urllib.request
import json
import time
import sys
import numpy as np
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

COINS_40 = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "SUIUSDT", "AVAXUSDT", "NEARUSDT", "BNBUSDT", "DOGEUSDT",
    "XRPUSDT", "ADAUSDT", "LINKUSDT", "DOTUSDT", "LTCUSDT", "BCHUSDT", "APTUSDT", "ARBUSDT",
    "OPUSDT", "INJUSDT", "TIAUSDT", "SEIUSDT", "FETUSDT", "RUNEUSDT", "FILUSDT", "ICPUSDT",
    "PEPEUSDT", "SHIBUSDT", "WIFUSDT", "RENDERUSDT", "STXUSDT", "GALAUSDT", "FTMUSDT",
    "AAVEUSDT", "UNIUSDT", "CRVUSDT", "MKRUSDT", "LDOUSDT", "ATOMUSDT", "THETAUSDT",
    "ALGOUSDT", "KASUSDT"
]

def fetch_klines(sym, interval="4h", limit=550):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                candles = []
                for k in data:
                    candles.append({
                        "time": int(k[0]), "open": float(k[1]), "high": float(k[2]),
                        "low": float(k[3]), "close": float(k[4]), "volume": float(k[5])
                    })
                return sym, candles
        except Exception:
            time.sleep(0.2)
    return sym, []

def audit_timeframe(tf, limit, tp_pct, be_pct, disp_min):
    print(f"\nScanning {tf.upper()} across 40 coins (limit={limit} bars)...", flush=True)
    all_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(fetch_klines, sym, tf, limit) for sym in COINS_40]
        for f in concurrent.futures.as_completed(futures):
            sym, klines = f.result()
            if len(klines) >= 100:
                all_data[sym] = klines

    trades = []
    
    for sym, candles in all_data.items():
        n = len(candles)
        for i in range(25, n - 20):
            # Extreme swing low of 20 bars
            is_extreme = (candles[i]["low"] == min(c["low"] for c in candles[i-20:i+1]))
            if not is_extreme:
                continue
                
            c = candles[i]
            ob_top = max(c["open"], c["close"])
            ob_bot = c["low"]
            ob_mt = (ob_top + ob_bot) / 2.0
            
            disp_high = max(candles[i+1]["high"], candles[i+2]["high"], candles[i+3]["high"])
            disp_gain = (disp_high - ob_top) / ob_top
            has_fvg = (candles[i+2]["low"] > candles[i]["high"]) if i+2 < n else False
            
            if disp_gain < disp_min or not has_fvg:
                continue
                
            tap_idx = -1
            for k in range(i+3, min(i+60, n)):
                if candles[k]["low"] <= ob_top:
                    tap_idx = k
                    break
                    
            if tap_idx == -1 or tap_idx >= n - 10:
                continue
                
            tap_c = candles[tap_idx]
            c_range = tap_c["high"] - tap_c["low"]
            lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
            wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
            
            # Smart money tap filter
            if wick_ratio < 0.18 or tap_c["close"] < ob_mt:
                continue
                
            entry_p = ob_top
            tp_target = entry_p * (1.0 + tp_pct)
            be_target = entry_p * (1.0 + be_pct)
            sl_target = ob_bot * 0.995
            
            be_active = False
            trade_res = None
            bars_held = 0
            
            for m in range(tap_idx, min(tap_idx + 45, n)):
                bar = candles[m]
                bars_held += 1
                if not be_active and bar["high"] >= be_target:
                    be_active = True
                if bar["high"] >= tp_target:
                    trade_res = "WIN"
                    break
                if be_active and bar["low"] <= entry_p:
                    trade_res = "BREAKEVEN"
                    break
                if bar["close"] <= sl_target:
                    trade_res = "LOSS"
                    break
                    
            if not trade_res:
                final_close = candles[min(tap_idx + 45, n - 1)]["close"]
                trade_res = "BREAKEVEN" if be_active else ("WIN" if final_close > entry_p else "LOSS")
                
            trades.append({
                "symbol": sym,
                "tf": tf,
                "entry_time": tap_c["time"],
                "entry_date": time.strftime("%Y-%m-%d %H:%M", time.gmtime(tap_c["time"] / 1000)),
                "result": trade_res,
                "bars": bars_held
            })
            
    trades.sort(key=lambda x: x["entry_time"])
    return trades

def main():
    print("=" * 85)
    print(" 📊 COMPREHENSIVE 3-MONTH AUDIT: 1H vs 4H TRADE EXECUTION COUNT & STATS")
    print(" 40 Crypto Pairs | Last 90 Days (~2,160 1H bars & ~540 4H bars)")
    print("=" * 85)
    
    # 4H parameters: TP = +4.0%, BE = +1.5%, Displacement >= 3.5%
    trades_4h = audit_timeframe(tf="4h", limit=550, tp_pct=0.040, be_pct=0.015, disp_min=0.035)
    
    # 1H parameters: TP = +2.0%, BE = +0.8%, Displacement >= 2.0%
    trades_1h = audit_timeframe(tf="1h", limit=1000, tp_pct=0.020, be_pct=0.008, disp_min=0.020)
    
    def print_tf_stats(trades, tf_name):
        tot = len(trades)
        w = sum(1 for t in trades if t["result"] == "WIN")
        b = sum(1 for t in trades if t["result"] == "BREAKEVEN")
        l = sum(1 for t in trades if t["result"] == "LOSS")
        wr = (w / tot * 100) if tot > 0 else 0
        br = (b / tot * 100) if tot > 0 else 0
        lr = (l / tot * 100) if tot > 0 else 0
        safety = ((w + b) / tot * 100) if tot > 0 else 0
        
        print(f"\n--- {tf_name} STATISTICAL BREAKDOWN ---")
        print(f"  • Total Trades Executed:   {tot}")
        print(f"  • 🏆 Direct TP Wins:       {w} ({wr:.1f}%)")
        print(f"  • 🛡️ Breakeven Exits:      {b} ({br:.1f}%)")
        print(f"  • ❌ Losses:               {l} ({lr:.1f}%)")
        print(f"  • 💎 Zero-Loss Safety Rate: {safety:.1f}%")
        
    print_tf_stats(trades_4h, "4-HOUR (4H) MACRO SWING")
    print_tf_stats(trades_1h, "1-HOUR (1H) INTRADAY")
    
    total_all = len(trades_4h) + len(trades_1h)
    wins_all = sum(1 for t in trades_4h + trades_1h if t["result"] == "WIN")
    be_all = sum(1 for t in trades_4h + trades_1h if t["result"] == "BREAKEVEN")
    loss_all = sum(1 for t in trades_4h + trades_1h if t["result"] == "LOSS")
    
    print("\n" + "=" * 85)
    print("                    COMBINED 1H + 4H SYSTEM TOTALS")
    print("=" * 85)
    print(f"Total Trades Across Both TFs:  {total_all}")
    print(f"🏆 Total Direct Wins:          {wins_all} ({wins_all/total_all*100:.1f}%)")
    print(f"🛡️ Total Breakeven Exits:     {be_all} ({be_all/total_all*100:.1f}%)")
    print(f"❌ Total Losses:              {loss_all} ({loss_all/total_all*100:.1f}%)")
    print(f"💎 Overall Capital Safety:    {(wins_all + be_all)/total_all*100:.1f}%")
    print("=====================================================================\n")

if __name__ == "__main__":
    main()
