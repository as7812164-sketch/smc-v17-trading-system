"""
Hermes 2.5 Apex: Quantitative Altcoin Discovery Engine.
Scans liquid Binance Futures coins outside the Top-22 Champions to identify
the highest-performing assets with exceptional SMC / Order Block respect.
"""

import asyncio
import time
from typing import List, Dict, Any
from feed.binance_feed import binance_feed

CURRENT_22 = {
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SOLUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
}

NEW_CANDIDATE_COINS = [
    "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT", "LINKUSDT", "DOTUSDT", "ARBUSDT", "TIAUSDT",
    "INJUSDT", "PEPEUSDT", "WIFUSDT", "SEIUSDT", "STXUSDT", "JUPUSDT", "ORDIUSDT",
    "CRVUSDT", "AXSUSDT", "DYDXUSDT", "MANAUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT"
]

def simulate_hermes25_trades(candles: List[Dict[str, Any]], interval: str) -> Dict[str, Any]:
    n = len(candles)
    if n < 50:
        return {"total": 0, "wins": 0, "losses": 0, "wr": 0.0, "net_pnl": 0.0}

    tp_pct = 0.022 if interval == "1h" else 0.028
    soft_sl_pct = 0.025 if interval == "1h" else 0.028
    hard_sl_pct = 0.036 if interval == "1h" else 0.038
    min_displacement = 0.050
    max_tap_window = 28
    leverage = 5.0

    trades = []
    i = 20
    while i < n - 30:
        # Check Long setup
        is_swing_low = candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1])
        if is_swing_low:
            sub_w = candles[i:min(i+16, n)]
            highs = [c["high"] for c in sub_w]
            max_high = max(highs)
            high_idx = i + highs.index(max_high)
            if high_idx > i + 2:
                gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                if gain >= min_displacement:
                    idm_low = candles[high_idx - 1]["low"]
                    best_mid = -1
                    max_bg = 0.0
                    for mid in range(i+1, high_idx):
                        bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                        fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                        if 0.30 <= fib <= 0.70 and bg > max_bg:
                            max_bg = bg
                            best_mid = mid

                    if best_mid != -1:
                        dec_c = candles[best_mid - 1]
                        dec_top = max(dec_c["open"], dec_c["close"])
                        dec_bot = dec_c["low"]
                        has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False

                        if has_fvg:
                            # Search for tap
                            for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                tap_c = candles[t]
                                if tap_c["low"] <= dec_top * 1.0005:
                                    c_range = tap_c["high"] - tap_c["low"]
                                    swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                    l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                    w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                    mt = (dec_top + dec_bot) / 2.0

                                    if swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                        # Trade entered at dec_top! Simulate forward
                                        entry_p = dec_top
                                        tp_p = entry_p * (1.0 + tp_pct)
                                        sl_p = entry_p * (1.0 - soft_sl_pct)
                                        highest = entry_p
                                        outcome = "SL_HIT"
                                        pnl_usdt = -250.0 * soft_sl_pct * leverage

                                        for f in range(t + 1, min(t + 40, n)):
                                            bar = candles[f]
                                            highest = max(highest, bar["high"])
                                            cur_roe = (highest - entry_p) / entry_p * leverage

                                            # Dynamic Armor (+5% BE shift)
                                            if cur_roe >= 0.05:
                                                sl_p = entry_p

                                            if bar["high"] >= tp_p:
                                                outcome = "TP_HIT"
                                                pnl_usdt = 250.0 * tp_pct * leverage
                                                break
                                            elif bar["low"] <= sl_p:
                                                if sl_p == entry_p:
                                                    outcome = "BE_EXIT"
                                                    pnl_usdt = 0.0
                                                else:
                                                    outcome = "SL_HIT"
                                                    pnl_usdt = -250.0 * soft_sl_pct * leverage
                                                break

                                        trades.append({
                                            "side": "BUY",
                                            "entry": entry_p,
                                            "outcome": outcome,
                                            "pnl": pnl_usdt,
                                            "mfe": round((highest - entry_p) / entry_p * 100 * leverage, 1)
                                        })
                                        i = t + 5 # skip forward
                                        break
        i += 1

    wins = sum(1 for t in trades if t["outcome"] == "TP_HIT")
    losses = sum(1 for t in trades if t["outcome"] == "SL_HIT")
    bes = sum(1 for t in trades if t["outcome"] == "BE_EXIT")
    tot = wins + losses
    wr = round((wins / tot * 100), 1) if tot > 0 else 0.0
    net_pnl = sum(t["pnl"] for t in trades)
    avg_mfe = round(sum(t["mfe"] for t in trades) / len(trades), 1) if trades else 0.0

    return {
        "trades_count": len(trades),
        "wins": wins,
        "losses": losses,
        "be_count": bes,
        "win_rate": wr,
        "net_pnl": round(net_pnl, 2),
        "avg_mfe": avg_mfe
    }

async def scan_all():
    print("🚀 Initiating Multi-Coin Quantitative Scan Beyond Top 22...")
    results = []

    for sym in NEW_CANDIDATE_COINS:
        try:
            # Fetch 500 candles of 1H and 4H
            candles_1h = await binance_feed.fetch_klines(sym, "1h", 400)
            candles_4h = await binance_feed.fetch_klines(sym, "4h", 300)

            res_1h = simulate_hermes25_trades(candles_1h, "1h")
            res_4h = simulate_hermes25_trades(candles_4h, "4h")

            total_trades = res_1h["trades_count"] + res_4h["trades_count"]
            total_wins = res_1h["wins"] + res_4h["wins"]
            total_losses = res_1h["losses"] + res_4h["losses"]
            comb_tot = total_wins + total_losses
            comb_wr = round((total_wins / comb_tot * 100), 1) if comb_tot > 0 else 0.0
            comb_pnl = round(res_1h["net_pnl"] + res_4h["net_pnl"], 2)

            results.append({
                "symbol": sym,
                "total_trades": total_trades,
                "wins": total_wins,
                "losses": total_losses,
                "be_exits": res_1h["be_count"] + res_4h["be_count"],
                "win_rate": comb_wr,
                "net_pnl": comb_pnl,
                "avg_mfe_1h": res_1h["avg_mfe"],
                "avg_mfe_4h": res_4h["avg_mfe"]
            })
            print(f"✓ Scanned {sym:10s} -> WR: {comb_wr:5.1f}% | Trades: {comb_tot:2d} (W:{total_wins} L:{total_losses}) | PnL: ${comb_pnl:+.1f}")
        except Exception as e:
            print(f"❌ Error scanning {sym}: {e}")

    await binance_feed.close()

    # Sort by Win Rate and Net PnL
    results.sort(key=lambda x: (x["win_rate"], x["net_pnl"]), reverse=True)

    print("\n🏆 ================= TOP DISCOVERED COINS (RANKED) =================")
    for idx, r in enumerate(results[:10], 1):
        print(f"#{idx:2d} {r['symbol']:10s} | Win Rate: {r['win_rate']:5.1f}% | Net PnL: ${r['net_pnl']:+6.1f} | Trades: {r['total_trades']:2d} (W:{r['wins']} L:{r['losses']} BE:{r['be_exits']}) | MFE: {r['avg_mfe_4h']}%")

if __name__ == "__main__":
    asyncio.run(scan_all())
