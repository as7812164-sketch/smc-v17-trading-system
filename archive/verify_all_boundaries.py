import urllib.request
import json
import sys
from config import DEFAULT_COINS, TIER1_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def scan_all_from_api():
    print("================================================================================")
    print("      VERIFIED LIVE WEBSITE API CHART DATA: 2ND OB EXACT BOUNDARY PRICES")
    print("================================================================================")
    
    coins = list(dict.fromkeys(TIER1_COINS + DEFAULT_COINS))
    
    for tf in ["1h", "4h"]:
        print(f"\n========================== [ TIMEFRAME: {tf.upper()} ] ==========================")
        print(f"{'Symbol':<12} | {'Cur Price':<10} | {'⭐ 2nd OB Range':<22} | {'Exact Entry':<12} | {'TP (+ROE)':<14} | {'SL (-ROE)':<14} | {'Dist %'}")
        print("-" * 110)
        
        tp_mult = 1.0150 if tf == "1h" else 1.0204
        sl_mult = 0.9800 if tf == "1h" else 0.9750
        
        matches = []
        for sym in coins:
            try:
                url = f"http://127.0.0.1:8000/api/klines?symbol={sym}&interval={tf}&limit=500"
                with urllib.request.urlopen(url, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                    cur_p = data.get("current_price", 0.0)
                    zones = data.get("zones", [])
                    
                    buy_zones = [z for z in zones if z.get("side") == "BUY" and z.get("status") in ("QUALIFIED", "ACTIVE")]
                    
                    # 2nd OB is Zone 2 (index 1) in unmitigated time sequence
                    if len(buy_zones) >= 2:
                        target_ob = buy_zones[1]
                        entry_p = target_ob["ob_high"]
                        ob_low = target_ob["ob_low"]
                        tp_p = entry_p * tp_mult
                        sl_p = entry_p * sl_mult
                        dist_pct = ((cur_p - entry_p) / cur_p) * 100 if cur_p > 0 else 0.0
                        
                        matches.append({
                            "symbol": sym,
                            "cur_p": cur_p,
                            "ob_range": f"{ob_low:.4f} - {entry_p:.4f}",
                            "entry_p": entry_p,
                            "tp_p": tp_p,
                            "sl_p": sl_p,
                            "dist_pct": dist_pct,
                            "tags": target_ob.get("tags", [])
                        })
            except Exception:
                pass
                
        matches.sort(key=lambda x: abs(x["dist_pct"]))
        for m in matches[:10]:
            tp_str = f"{m['tp_p']:.4f}"
            sl_str = f"{m['sl_p']:.4f}"
            print(f"{m['symbol']:<12} | {m['cur_p']:<10.4f} | {m['ob_range']:<22} | {m['entry_p']:<12.4f} | {tp_str:<14} | {sl_str:<14} | {m['dist_pct']:+6.2f}%")

if __name__ == "__main__":
    scan_all_from_api()
