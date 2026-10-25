import asyncio
import json
import urllib.request
import sys
from config import TIER1_COINS, DEFAULT_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def get_data():
    coins = list(dict.fromkeys(TIER1_COINS + DEFAULT_COINS))
    
    for tf in ['1h', '4h']:
        print(f"\n========================== [ TIMEFRAME: {tf.upper()} ] ==========================")
        tp_mult = 1.0150 if tf == '1h' else 1.0204
        sl_mult = 0.9800 if tf == '1h' else 0.9750
        
        matches = []
        for sym in coins:
            try:
                url = f"http://127.0.0.1:8000/api/klines?symbol={sym}&interval={tf}&limit=500"
                with urllib.request.urlopen(url, timeout=5) as r:
                    data = json.loads(r.read().decode())
                    cur_p = data.get('current_price', 0.0)
                    zones = [z for z in data.get('zones', []) if z.get('side') == 'BUY' and z.get('status') in ('QUALIFIED', 'ACTIVE')]
                    if len(zones) >= 2:
                        mid = zones[1] # Exact 2nd OB
                        ep = mid['ob_high']
                        ob_l = mid['ob_low']
                        tp = ep * tp_mult
                        sl = ep * sl_mult
                        dist = ((cur_p - ep) / cur_p) * 100 if cur_p > 0 else 0
                        matches.append({
                            "symbol": sym,
                            "cur_p": cur_p,
                            "ob_range": f"{ob_l:.4f} - {ep:.4f}",
                            "entry": ep,
                            "tp": tp,
                            "sl": sl,
                            "dist": dist
                        })
            except Exception:
                pass
                
        matches.sort(key=lambda x: abs(x["dist"]))
        print(f"{'Symbol':<12} | {'Current Price':<14} | {'⭐ OB Entry (Middle)':<22} | {'Take Profit (TP)':<18} | {'Stop Loss (SL)':<16} | {'Distance %'}")
        print("-" * 110)
        for m in matches[:10]:
            print(f"{m['symbol']:<12} | {m['cur_p']:<14.4f} | {m['entry']:<22.4f} | {m['tp']:<18.4f} | {m['sl']:<16.4f} | {m['dist']:+6.2f}%")

if __name__ == "__main__":
    get_data()
