import json
import urllib.request
import datetime
import sys
import os

sys.path.append(os.getcwd())
from engine.hermes30_apex_live import hermes30_live_engine

def run_detector(symbol, interval):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit=100"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw_klines = json.loads(resp.read().decode('utf-8'))
    
    candles = []
    for k in raw_klines:
        candles.append({
            "time": k[0],
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        })
    
    btc_sentry = {"long_veto": False, "short_veto": False}
    setups = hermes30_live_engine.detect_apex_setups_on_candles(symbol, candles, interval, btc_sentry)
    print(f"\n--- SETUPS FOR {symbol} {interval} --- (Total candles: {len(candles)})")
    for s in setups:
        tap_dt = datetime.datetime.fromtimestamp(s['tap_time']/1000.0)
        print(f"Side: {s['side']} | MT Entry: {s['entry_price']} | OB: [{s['ob_low']} - {s['ob_high']}] | TP: {s['tp_price']} | Soft SL: {s['soft_sl_price']} | Displacement: {s['displacement_pct']}% | Wick Ratio: {s['wick_ratio_pct']}% | Tap Time: {tap_dt} | Status: {s['status']}")

run_detector("MANAUSDT", "4h")
run_detector("AEROUSDT", "4h")
run_detector("ICPUSDT", "1h")
