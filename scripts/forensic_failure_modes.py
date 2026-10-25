import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json

def forensic_deep_dive():
    results_path = os.path.join(os.path.dirname(__file__), "..", "hermes35_deep_oos_results.json")
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    trades = data["trades"]
    sl_trades = [t for t in trades if t["outcome"] == "SL_HIT"]
    
    print("====================================================================")
    print("DETAILED QUANT AUTOPSY OF THE 4 MAIN FAILURE MODES")
    print("====================================================================")
    
    # Failure Mode 1: Counter-Trend Shock (Shorting during BTC Rally)
    short_sls = [t for t in sl_trades if t["side"] == "SHORT"]
    print(f"\n1. COUNTER-TREND SHORTS: {len(short_sls)} / 19 SLs ({len(short_sls)/len(sl_trades)*100:.1f}%)")
    print("Pairs caught shorting:", [t["symbol"] for t in short_sls])
    
    # Failure Mode 2: Falling Knife / Immediate Slicing (<2h duration)
    fast_sls = [t for t in sl_trades if "1h" in t["duration"] or "2h" in t["duration"]]
    print(f"\n2. IMMEDIATE MOMENTUM SLICE (<2 Hours): {len(fast_sls)} / 19 SLs ({len(fast_sls)/len(sl_trades)*100:.1f}%)")
    print("Pairs sliced immediately:", [t["symbol"] + ' (' + t['duration'] + ')' for t in fast_sls])
    
    # Failure Mode 3: Specific Toxic Asset (LDO + TIA)
    toxic_sls = [t for t in sl_trades if t["symbol"] in ["LDOUSDT", "TIAUSDT"]]
    print(f"\n3. TOXIC VOLATILITY ASSETS (LDO + TIA): {len(toxic_sls)} / 19 SLs ({len(toxic_sls)/len(sl_trades)*100:.1f}%)")
    print(f"Total Drain from LDO + TIA: ${sum(t['net_pnl_usdt'] for t in toxic_sls):.2f} USDT")
    
    # Failure Mode 4: 1H Noise vs 4H Conviction
    h1_sls = [t for t in sl_trades if t["timeframe"] == "1H"]
    print(f"\n4. 1H INTRADAY NOISE: {len(h1_sls)} / 19 SLs ({len(h1_sls)/len(sl_trades)*100:.1f}%)")

if __name__ == "__main__":
    forensic_deep_dive()
