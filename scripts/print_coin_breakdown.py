import json
import sys
sys.path.insert(0, 'scripts')
import test_pure_pdh_pdl_touch_1to3 as eng

for sl_val in [0.012, 0.015]:
    mode_a, mode_b = eng.run_pure_touch_audit(sl_pct=sl_val)
    
    print("=" * 88)
    print(f"COIN-BY-COIN BREAKDOWN: SL={sl_val*100:.1f}% | TP={sl_val*300:.1f}% (1:3 R:R)")
    print("=" * 88)
    print(f"{'#':<3} | {'Coin':<14} | {'1st Short (PDH)':<22} | {'Result':<8} | {'1st Long (PDL)':<22} | {'Result':<8}")
    print("-" * 88)
    
    s_wins = 0
    l_wins = 0
    idx = 1
    
    for sym, rec in mode_a.items():
        st = rec.get("short_trade")
        lt = rec.get("long_trade")
        
        if st:
            s_str = f"{st['date']} @ ${st['entry_price']:.4f}"
            s_res = "TP WIN" if st["outcome"] == "TP_HIT" else "SL HIT"
            if st["outcome"] == "TP_HIT": s_wins += 1
        else:
            s_str = "No PDH touch"
            s_res = "N/A"
            
        if lt:
            l_str = f"{lt['date']} @ ${lt['entry_price']:.4f}"
            l_res = "TP WIN" if lt["outcome"] == "TP_HIT" else "SL HIT"
            if lt["outcome"] == "TP_HIT": l_wins += 1
        else:
            l_str = "No PDL touch"
            l_res = "N/A"
            
        print(f"{idx:<3} | {sym:<14} | {s_str:<22} | {s_res:<8} | {l_str:<22} | {l_res:<8}")
        idx += 1
        
    print("=" * 88)
    print(f"Total Coins: 20 | Total Trades: 40")
    print(f"Short Trades: {s_wins} TP Wins / {20 - s_wins} SL Hits ({s_wins/20*100:.1f}%)")
    print(f"Long Trades:  {l_wins} TP Wins / {20 - l_wins} SL Hits ({l_wins/20*100:.1f}%)")
    print(f"Overall Mode A: {s_wins + l_wins} TP Wins / {40 - (s_wins + l_wins)} SL Hits ({(s_wins+l_wins)/40*100:.1f}%)")
    print("=" * 88)
    print("\n")
