"""
HERMES 2.5 APEX HYBRID: Quantitative Candidate Discovery Engine
Scans 22 liquid Binance coins outside the current Top-22 Champions.
Evaluates both Long & Short setups under full 4-Sentries + Dynamic Armor rules.
"""

import sys
import json
import time
import urllib.request
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CANDIDATE_COINS = [
    "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT", "LINKUSDT", "DOTUSDT",
    "ARBUSDT", "TIAUSDT", "INJUSDT", "PEPEUSDT", "WIFUSDT", "SEIUSDT",
    "STXUSDT", "JUPUSDT", "ORDIUSDT", "CRVUSDT", "AXSUSDT", "DYDXUSDT",
    "MANAUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT"
]

BINANCE_BASE = "https://data-api.binance.vision/api/v3/klines"

def fetch_klines(symbol: str, interval: str, limit: int = 1000) -> List[Dict[str, Any]]:
    url = f"{BINANCE_BASE}?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candles = []
            for c in data:
                candles.append({
                    "time": int(c[0]),
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": float(c[5])
                })
            return candles
    except Exception as e:
        return []

def evaluate_hermes25(candles: List[Dict[str, Any]], interval: str, btc_map_4h: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
    n = len(candles)
    if n < 50:
        return []

    std_tp_pct = 0.022 if interval == "1h" else 0.028
    soft_sl_pct = 0.025 if interval == "1h" else 0.028
    max_tap_window = 28
    max_hold = 40 if interval == "1h" else 30
    leverage = 5.0
    margin = 50.0 # $50 per trade

    trades = []
    i = 20
    while i < n - max_hold:
        # =====================================================================
        # 1. LONG SETUP CHECK
        # =====================================================================
        is_swing_low = candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1])
        if is_swing_low:
            sub_w = candles[i:min(i+16, n)]
            highs = [c["high"] for c in sub_w]
            max_high = max(highs)
            high_idx = i + highs.index(max_high)
            if high_idx > i + 2:
                gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                if gain >= 0.050: # Sentry 2: Displacement >= 5.0%
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
                            for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                tap_c = candles[t]
                                if tap_c["low"] <= dec_top * 1.0005:
                                    # Sentry 1 BTC Brake (dump < 2%)
                                    curr_4h_ts = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                    btc_c = btc_map_4h.get(curr_4h_ts)
                                    btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                    sentry1_ok = btc_dump < 0.020

                                    c_range = tap_c["high"] - tap_c["low"]
                                    swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                    l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                    w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                    mt = (dec_top + dec_bot) / 2.0

                                    if swept and w_ratio >= 0.18 and tap_c["close"] >= mt and sentry1_ok:
                                        entry = dec_top
                                        tp_p = entry * (1.0 + std_tp_pct)
                                        cur_sl = entry * (1.0 - soft_sl_pct)
                                        highest = entry
                                        outcome = "SL_HIT"
                                        pnl = -margin * soft_sl_pct * leverage

                                        for m in range(t + 1, min(t + max_hold, n)):
                                            bar = candles[m]
                                            highest = max(highest, bar["high"])
                                            
                                            # Dynamic Armor: +1.6% move -> Lock BE +0.2%
                                            if bar["high"] >= entry * 1.016:
                                                cur_sl = max(cur_sl, entry * 1.002)
                                            # Stage 2: +2.2% move -> Lock +1.2%
                                            if bar["high"] >= entry * 1.022:
                                                cur_sl = max(cur_sl, entry * 1.012)

                                            if bar["high"] >= tp_p:
                                                outcome = "TP_HIT"
                                                pnl = margin * std_tp_pct * leverage
                                                break
                                            elif bar["low"] <= cur_sl:
                                                if cur_sl > entry:
                                                    outcome = "BE_EXIT"
                                                    pnl = margin * (cur_sl - entry) / entry * leverage
                                                else:
                                                    outcome = "SL_HIT"
                                                    pnl = -margin * soft_sl_pct * leverage
                                                break

                                        trades.append({
                                            "side": "BUY",
                                            "entry": entry,
                                            "outcome": outcome,
                                            "pnl": pnl,
                                            "mfe": (highest - entry) / entry * 100 * leverage,
                                            "tf": interval
                                        })
                                        i = t + 3
                                        break

        # =====================================================================
        # 2. SHORT SETUP CHECK
        # =====================================================================
        is_swing_high = candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1])
        if is_swing_high:
            sub_w = candles[i:min(i+16, n)]
            lows = [c["low"] for c in sub_w]
            min_low = min(lows)
            low_idx = i + lows.index(min_low)
            if low_idx > i + 2:
                drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                if drop >= 0.050: # Sentry 2: Institutional Ceiling >= 5.0%
                    idm_high = candles[low_idx - 1]["high"]
                    best_mid = -1
                    max_bg = 0.0
                    for mid in range(i+1, low_idx):
                        bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                        fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                        if 0.30 <= fib <= 0.70 and bg > max_bg:
                            max_bg = bg
                            best_mid = mid

                    if best_mid != -1:
                        dec_c = candles[best_mid - 1]
                        dec_top = dec_c["high"]
                        dec_bot = min(dec_c["open"], dec_c["close"])
                        has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False

                        if has_bear_fvg:
                            for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                tap_c = candles[t]
                                if tap_c["high"] >= dec_bot * 1.0005:
                                    # Sentry 1 BTC Brake (pump < 2%)
                                    curr_4h_ts = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                    btc_c = btc_map_4h.get(curr_4h_ts)
                                    btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                    sentry1_ok = btc_pump < 0.020

                                    c_range = tap_c["high"] - tap_c["low"]
                                    swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                    u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                    w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                    mt = (dec_top + dec_bot) / 2.0

                                    if swept and w_ratio >= 0.18 and tap_c["close"] <= mt and sentry1_ok:
                                        entry = dec_bot
                                        tp_p = entry * (1.0 - std_tp_pct)
                                        cur_sl = entry * (1.0 + soft_sl_pct)
                                        lowest = entry
                                        outcome = "SL_HIT"
                                        pnl = -margin * soft_sl_pct * leverage

                                        for m in range(t + 1, min(t + max_hold, n)):
                                            bar = candles[m]
                                            lowest = min(lowest, bar["low"])

                                            # Dynamic Armor Short: price drops -> Lock BE +0.2%
                                            if bar["low"] <= entry * (1.0 - 0.016):
                                                cur_sl = min(cur_sl, entry * 0.998)
                                            # Stage 2: price drops 2.2% -> Lock +1.2%
                                            if bar["low"] <= entry * (1.0 - 0.022):
                                                cur_sl = min(cur_sl, entry * 0.988)

                                            if bar["low"] <= tp_p:
                                                outcome = "TP_HIT"
                                                pnl = margin * std_tp_pct * leverage
                                                break
                                            elif bar["high"] >= cur_sl:
                                                if cur_sl < entry:
                                                    outcome = "BE_EXIT"
                                                    pnl = margin * (entry - cur_sl) / entry * leverage
                                                else:
                                                    outcome = "SL_HIT"
                                                    pnl = -margin * soft_sl_pct * leverage
                                                break

                                        trades.append({
                                            "side": "SELL",
                                            "entry": entry,
                                            "outcome": outcome,
                                            "pnl": pnl,
                                            "mfe": (entry - lowest) / entry * 100 * leverage,
                                            "tf": interval
                                        })
                                        i = t + 3
                                        break
        i += 1

    return trades

def main():
    print("[*] Fetching BTC 4H benchmark for Sentry 1 Macro Brake...")
    btc_candles = fetch_klines("BTCUSDT", "4h", limit=1000)
    btc_map_4h = {c["time"]: c for c in btc_candles}
    print(f"[*] Loaded {len(btc_candles)} BTC 4H candles.")

    summary = []

    print(f"\n[*] Scanning {len(CANDIDATE_COINS)} Alternative Coins against HERMES 2.5 APEX HYBRID...")
    print("-" * 85)

    for idx, sym in enumerate(CANDIDATE_COINS, 1):
        c_1h = fetch_klines(sym, "1h", limit=1000)
        c_4h = fetch_klines(sym, "4h", limit=1000)

        trades_1h = evaluate_hermes25(c_1h, "1h", btc_map_4h)
        trades_4h = evaluate_hermes25(c_4h, "4h", btc_map_4h)
        all_t = trades_1h + trades_4h

        wins = sum(1 for t in all_t if t["outcome"] in ("TP_HIT", "BE_EXIT") and t["pnl"] > 0)
        losses = sum(1 for t in all_t if t["outcome"] == "SL_HIT")
        tot = wins + losses
        wr = (wins / tot * 100) if tot > 0 else 0.0
        net_pnl = sum(t["pnl"] for t in all_t)

        long_trades = [t for t in all_t if t["side"] == "BUY"]
        short_trades = [t for t in all_t if t["side"] == "SELL"]
        long_wins = sum(1 for t in long_trades if t["pnl"] > 0)
        short_wins = sum(1 for t in short_trades if t["pnl"] > 0)

        avg_mfe = sum(t["mfe"] for t in all_t) / len(all_t) if all_t else 0.0

        summary.append({
            "symbol": sym,
            "total_trades": len(all_t),
            "wins": wins,
            "losses": losses,
            "win_rate": round(wr, 1),
            "net_pnl": round(net_pnl, 2),
            "long_count": len(long_trades),
            "long_wins": long_wins,
            "short_count": len(short_trades),
            "short_wins": short_wins,
            "avg_mfe": round(avg_mfe, 1)
        })

        print(f"[{idx:02d}/{len(CANDIDATE_COINS)}] {sym:<10s} -> WR: {wr:5.1f}% | Net PnL: ${net_pnl:+7.2f} | Trades: {len(all_t):2d} (W:{wins} L:{losses}) | MFE: {avg_mfe:4.1f}%")
        time.sleep(0.1)

    # Sort candidates
    summary.sort(key=lambda x: (x["win_rate"], x["net_pnl"]), reverse=True)

    print("\n" + "=" * 90)
    print("🏆 HERMES 2.5 APEX HYBRID: CANDIDATE COINS QUANTITATIVE LEADERBOARD")
    print("=" * 90)
    print(f"{'Rank':<5}{'Symbol':<12}{'Win Rate':<10}{'Net PnL ($)':<14}{'Trades':<9}{'W / L':<10}{'Short WR':<12}{'Long WR':<12}{'Avg MFE':<8}")
    print("-" * 90)

    for rank, s in enumerate(summary, 1):
        sh_wr = round(s['short_wins'] / s['short_count'] * 100, 1) if s['short_count'] > 0 else 0.0
        lg_wr = round(s['long_wins'] / s['long_count'] * 100, 1) if s['long_count'] > 0 else 0.0
        print(f"#{rank:<4}{s['symbol']:<12}{s['win_rate']:>6.1f}%    ${s['net_pnl']:>+8.2f}     {s['total_trades']:<9}{s['wins']}/{s['losses']:<7}{sh_wr:>5.1f}% ({s['short_count']})  {lg_wr:>5.1f}% ({s['long_count']})  {s['avg_mfe']:>5.1f}%")

    # Output JSON for reporting
    with open("candidate_coins_discovery_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("\n[+] Full results saved to candidate_coins_discovery_results.json")

if __name__ == "__main__":
    main()
