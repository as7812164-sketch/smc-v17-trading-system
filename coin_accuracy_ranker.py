import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

trades = []
for fn in ['hermes2_apex_trades_4h_1y.json', 'hermes2_apex_trades_1h_1y.json']:
    if os.path.exists(fn):
        with open(fn, "r", encoding="utf-8") as f:
            trades.extend(json.load(f))

print(f"Total 1-Year Trades in Database: {len(trades)}")

if trades:
    stats = {}
    for t in trades:
        sym = t.get("sym") or t.get("symbol")
        result = t.get("result", "") or t.get("outcome", "")
        if sym not in stats:
            stats[sym] = {"trades": 0, "wins": 0, "losses": 0, "pnl": 0.0}
        stats[sym]["trades"] += 1
        pnl = float(t.get("pnl_usdt", 0.0) or t.get("net_pnl", 0.0))
        stats[sym]["pnl"] += pnl
        if result in ("WIN", "TP_HIT") or pnl > 0:
            stats[sym]["wins"] += 1
        else:
            stats[sym]["losses"] += 1

    sorted_coins = sorted(
        stats.items(),
        key=lambda x: (x[1]["wins"] / x[1]["trades"] if x[1]["trades"] > 0 else 0, x[1]["trades"]),
        reverse=True
    )

    print("\n" + "=" * 80)
    print("🏆 1-YEAR COIN-BY-COIN ACCURACY RANKING (CURRENT CHAMPIONS)")
    print("=" * 80)
    print(f"{'Rank':<4} | {'Symbol':<12} | {'Trades':<8} | {'Wins':<6} | {'Loss':<6} | {'Win Rate':<10} | {'Net PnL':<10}")
    print("-" * 80)

    tot_t = 0
    tot_w = 0
    tot_l = 0
    tot_pnl = 0.0

    for idx, (sym, s) in enumerate(sorted_coins, 1):
        tr = s["trades"]
        w = s["wins"]
        l = s["losses"]
        wr = (w / tr * 100.0) if tr > 0 else 0.0
        p = s["pnl"]
        tot_t += tr
        tot_w += w
        tot_l += l
        tot_pnl += p
        sym_str = str(sym or "UNKNOWN")
        p_val = float(p if p is not None else 0.0)
        print(f"#{idx:<3} | {sym_str:<12} | {tr:<8} | {w:<6} | {l:<6} | {wr:<9.1f}% | ${p_val:<9.2f}")

    overall_wr = (tot_w / tot_t * 100.0) if tot_t > 0 else 0.0
    print("-" * 80)
    print(f"OVERALL: {len(sorted_coins)} Coins | Total Trades: {tot_t} | Wins: {tot_w} | Losses: {tot_l} | Win Rate: {overall_wr:.2f}% | Total Net PnL: ${tot_pnl:.2f}")
    print("=" * 80)
