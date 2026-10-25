import urllib.request
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Fetch live tickers
req = urllib.request.Request('https://fapi.binance.com/fapi/v1/ticker/price', headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req)
raw_tickers = json.loads(resp.read().decode())
live_prices = {t['symbol']: float(t['price']) for t in raw_tickers}

# Fetch setups from Render
req_setups = urllib.request.Request('https://smc-ai-agent.onrender.com/api/hermes/apex/setups', headers={'User-Agent': 'Mozilla/5.0'})
resp_setups = urllib.request.urlopen(req_setups)
setups_data = json.loads(resp_setups.read().decode())

print("=== LIVE UPCOMING SIGNALS & ARMED ORDER BLOCKS ===")
print(f"BTC Macro Sentry Bias: {setups_data.get('btc_macro_sentry', {}).get('bias')} | BTC Bull: {setups_data.get('btc_macro_sentry', {}).get('btc_is_bull')}")

for s in setups_data.get('setups', []):
    sym = s['symbol']
    tf = s['interval'].upper()
    side = s['side']
    entry = s['entry_price']
    radar = s['radar_price']
    ob_h = s['ob_high']
    ob_l = s['ob_low']
    mt = s['mean_threshold']
    tp = s['tp_price']
    sl = s['soft_sl_price']
    hard_sl = s['hard_sl_price']
    status = s['status']
    disp = s['displacement_pct']
    airspace = s['runway_void_pct']
    
    cur_p = live_prices.get(sym, 0.0)
    if side == "LONG":
        dist_pct = ((cur_p - entry) / entry * 100.0) if entry > 0 else 0.0
    else:
        dist_pct = ((entry - cur_p) / cur_p * 100.0) if cur_p > 0 else 0.0

    print(f"\n[*] {sym} ({tf} {side})")
    print(f"  - Status: {status}")
    print(f"  - Current Live Price: ${cur_p:.6f}")
    print(f"  - 5% Boundary Entry: ${entry:.6f} (Distance: {dist_pct:+.2f}%)")
    print(f"  - 0.20% Radar Pre-Arm: ${radar:.6f}")
    print(f"  - Order Block: [${ob_l:.6f} - ${ob_h:.6f}] (MT 50%: ${mt:.6f})")
    print(f"  - Target TP (+14.0% ROE): ${tp:.6f}")
    print(f"  - Stepped Armor: +8% BE Lock at ${s.get('armor_stage1_price'):.6f} | +9% Trail at ${s.get('armor_stage2_price'):.6f}")
    print(f"  - Soft Stop Loss (-14.0% ROE): ${sl:.6f} | Hard Stop: ${hard_sl:.6f}")
    print(f"  - Quality: Displacement: +{disp:.1f}% | Airspace Runway: +{airspace:.1f}% | [ORIGIN BEDROCK]")
