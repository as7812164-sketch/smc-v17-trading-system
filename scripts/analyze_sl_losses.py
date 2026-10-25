import os
import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta

def run_sl_forensics():
    results_path = os.path.join(os.path.dirname(__file__), "..", "hermes35_deep_oos_results.json")
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    trades = data["trades"]
    sl_trades = [t for t in trades if t["outcome"] == "SL_HIT"]
    
    print(f"Total Trades: {len(trades)}")
    print(f"Total Stop Loss (SL) Hits: {len(sl_trades)}")
    print("=" * 70)
    
    # 1. Distribution by Side
    side_dist = defaultdict(int)
    tf_dist = defaultdict(int)
    coin_dist = defaultdict(int)
    coin_pnl = defaultdict(float)
    total_loss_usdt = sum(t["net_pnl_usdt"] for t in sl_trades)
    
    durations_mins = []
    
    print("\n--- ALL 19 STOP LOSS TRADES FORENSIC AUDIT TABLE ---")
    print(f"{'#':<3} | {'Symbol':<9} | {'Side':<5} | {'TF':<3} | {'Entry Time':<20} | {'Exit Time':<20} | {'Dur':<6} | {'Entry':<9} | {'Exit/SL':<9} | {'Loss USDT':<10} | {'Bal After':<10}")
    print("-" * 125)
    
    for idx, t in enumerate(sl_trades, 1):
        side_dist[t["side"]] += 1
        tf_dist[t["timeframe"]] += 1
        coin_dist[t["symbol"]] += 1
        coin_pnl[t["symbol"]] += t["net_pnl_usdt"]
        
        # parse duration
        dur_str = t["duration"]
        
        print(f"{idx:<3} | {t['symbol']:<9} | {t['side']:<5} | {t['timeframe']:<3} | {t['entry_time_str']:<20} | {t['exit_time_str']:<20} | {dur_str:<6} | {t['entry_price']:<9.4f} | {t['exit_price']:<9.4f} | ${t['net_pnl_usdt']:<9.2f} | ${t['balance_after']:<10.2f}")
        
    print("\n" + "=" * 70)
    print("FORENSIC PATTERN 1: SIDE BREAKDOWN")
    print(f"SHORT SLs: {side_dist['SHORT']} ({side_dist['SHORT']/len(sl_trades)*100:.1f}%)")
    print(f"LONG SLs:  {side_dist['LONG']} ({side_dist['LONG']/len(sl_trades)*100:.1f}%)")
    
    print("\nFORENSIC PATTERN 2: TIMEFRAME BREAKDOWN")
    print(f"1H Timeframe SLs: {tf_dist['1H']} ({tf_dist['1H']/len(sl_trades)*100:.1f}%)")
    print(f"4H Timeframe SLs: {tf_dist['4H']} ({tf_dist['4H']/len(sl_trades)*100:.1f}%)")
    
    print("\nFORENSIC PATTERN 3: COIN RANKING BY LOSS COUNT & DRAIN")
    sorted_coins = sorted(coin_dist.items(), key=lambda x: x[1], reverse=True)
    for c, cnt in sorted_coins:
        print(f"{c:<10}: {cnt} Losses | Total Drained: ${coin_pnl[c]:.2f}")
        
    print("\nFORENSIC PATTERN 4: CLUSTER ANALYSIS (DATE REGIMES)")
    date_clusters = defaultdict(list)
    for t in sl_trades:
        d_str = t["entry_time_str"][:6] # e.g. "17 Sep"
        date_clusters[d_str].append(t)
    for d, tr_list in sorted(date_clusters.items()):
        print(f"{d}: {len(tr_list)} SL hits -> {[x['symbol'] + ' ' + x['side'] for x in tr_list]}")

if __name__ == "__main__":
    run_sl_forensics()
