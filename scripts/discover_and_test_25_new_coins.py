"""
DISCOVER AND TEST 25 NEW CRYPTO CANDIDATES
================================================================================
Discovers 25 brand-new, high-volume liquid Binance Futures pairs (excluding all 28 existing coins).
Fetches historical 4H market candles and tests the EXACT HERMES 3.5 Single Tier strategy:
- Displacement >= 5.0%
- Inducement Wick >= 18%
- Fair Value Gap (FVG)
- 5% Boundary Penetration inside Order Block
- BTC 4H EMA50 Macro Sentry
- +1.6% Break-Even Armor & +2.8% Take Profit (5x leverage)

CRITICAL: Pure Sandbox Backtest. DOES NOT TOUCH live engine or config.py!
================================================================================
"""

import os
import sys
import json
import time
import urllib.request
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXISTING_COINS = {
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT", "ORDIUSDT", "ETCUSDT",
    "MANAUSDT", "ADAUSDT", "TIAUSDT", "AXSUSDT", "ATOMUSDT", "ETHUSDT", "SOLUSDT", "ARBUSDT",
    "XRPUSDT", "INJUSDT", "PEPEUSDT", "LINKUSDT", "BNBUSDT"
}

def calculate_ema(values: List[float], period: int = 50) -> List[float]:
    if not values: return []
    ema = [values[0]] * len(values)
    k = 2.0 / (period + 1.0)
    for i in range(1, len(values)):
        ema[i] = values[i] * k + ema[i-1] * (1.0 - k)
    return ema

def fetch_klines(symbol: str, interval: str = "4h", limit: int = 500) -> List[Dict[str, Any]]:
    # Try public Binance API
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = json.loads(r.read().decode())
            candles = []
            for d in raw:
                candles.append({
                    "time": int(d[0]),
                    "open": float(d[1]),
                    "high": float(d[2]),
                    "low": float(d[3]),
                    "close": float(d[4]),
                    "volume": float(d[5]),
                    "close_time": int(d[6])
                })
            return candles
    except Exception as e:
        print(f"Warning: Failed to fetch {symbol} directly: {e}")
        return []

def evaluate_hermes35(candles: List[Dict[str, Any]], sym: str, btc_map: Dict[int, Any], btc_ema_map: Dict[int, bool]) -> Dict[str, Any]:
    n = len(candles)
    if n < 40:
        return {"sym": sym, "trades": 0, "wins": 0, "losses": 0, "win_rate": 0.0, "pf": 0.0, "status": "INSUFFICIENT_DATA"}

    max_tap_window = 28
    tp_target = 0.028
    sl_target = 0.028
    armor_be_trigger = 0.016

    executed = []

    for i in range(20, n - 2):
        # 1. LONG SETUP
        if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
            sub_w = candles[i:min(i+16, n)]
            highs = [c["high"] for c in sub_w]
            max_high = max(highs)
            high_idx = i + highs.index(max_high)
            if high_idx > i + 2:
                gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                if gain >= 0.050:
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
                                    c_range = tap_c["high"] - tap_c["low"]
                                    l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                    w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                    mt = (dec_top + dec_bot) / 2.0

                                    swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                    curr_4h = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                    prev_4h = curr_4h - (4 * 3600 * 1000)
                                    btc_c = btc_map.get(prev_4h)
                                    btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                    btc_clean = btc_dump < 0.020
                                    btc_is_bull = btc_ema_map.get(prev_4h, True)

                                    if btc_clean and btc_is_bull and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                        # Execute Long Trade
                                        entry_p = dec_top
                                        tp_p = entry_p * (1.0 + tp_target)
                                        sl_p = entry_p * (1.0 - sl_target)
                                        be_p = entry_p * (1.0 + 0.0010)

                                        outcome = "HOLD"
                                        be_active = False
                                        for f_idx in range(t + 1, min(t + 40, n)):
                                            fc = candles[f_idx]
                                            if fc["high"] >= entry_p * (1.0 + armor_be_trigger):
                                                be_active = True
                                            if fc["high"] >= tp_p:
                                                outcome = "TP"; break
                                            if be_active and fc["low"] <= be_p:
                                                outcome = "ARMOR_BE"; break
                                            elif not be_active and fc["low"] <= sl_p:
                                                outcome = "SL"; break

                                        if outcome in ("TP", "ARMOR_BE", "SL"):
                                            executed.append(outcome)
                                        break

        # 2. SHORT SETUP
        if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
            sub_w = candles[i:min(i+16, n)]
            lows = [c["low"] for c in sub_w]
            min_low = min(lows)
            low_idx = i + lows.index(min_low)
            if low_idx > i + 2:
                drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                if drop >= 0.050:
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
                        has_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                        if has_fvg:
                            for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                tap_c = candles[t]
                                if tap_c["high"] >= dec_bot * 0.9995:
                                    c_range = tap_c["high"] - tap_c["low"]
                                    u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                    w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                    mt = (dec_top + dec_bot) / 2.0

                                    swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                    curr_4h = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                    prev_4h = curr_4h - (4 * 3600 * 1000)
                                    btc_c = btc_map.get(prev_4h)
                                    btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                    btc_clean = btc_pump < 0.020
                                    btc_is_bear = not btc_ema_map.get(prev_4h, True)

                                    if btc_clean and btc_is_bear and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                        entry_p = dec_bot
                                        tp_p = entry_p * (1.0 - tp_target)
                                        sl_p = entry_p * (1.0 + sl_target)
                                        be_p = entry_p * (1.0 - 0.0010)

                                        outcome = "HOLD"
                                        be_active = False
                                        for f_idx in range(t + 1, min(t + 40, n)):
                                            fc = candles[f_idx]
                                            if fc["low"] <= entry_p * (1.0 - armor_be_trigger):
                                                be_active = True
                                            if fc["low"] <= tp_p:
                                                outcome = "TP"; break
                                            if be_active and fc["high"] >= be_p:
                                                outcome = "ARMOR_BE"; break
                                            elif not be_active and fc["high"] >= sl_p:
                                                outcome = "SL"; break

                                        if outcome in ("TP", "ARMOR_BE", "SL"):
                                            executed.append(outcome)
                                        break

    tp_wins = executed.count("TP")
    be_wins = executed.count("ARMOR_BE")
    losses = executed.count("SL")
    tot = len(executed)
    wins = tp_wins + be_wins
    wr = (wins / tot * 100.0) if tot > 0 else 0.0
    pf = (tp_wins * 1.0 + be_wins * 0.05) / (losses * 1.0) if losses > 0 else (99.0 if wins > 0 else 0.0)

    return {
        "sym": sym,
        "trades": tot,
        "wins": wins,
        "tp_wins": tp_wins,
        "be_wins": be_wins,
        "losses": losses,
        "win_rate": round(wr, 2),
        "profit_factor": round(pf, 2)
    }

def main():
    print("=" * 85)
    print("      DISCOVERING TOP 25 NEW CANDIDATE CRYPTO ASSETS (STRICT EXCLUSION)")
    print("=" * 85)

    # 1. Fetch 24hr Ticker from Binance Futures
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            tickers = json.loads(r.read().decode())
    except Exception as e:
        print(f"Error fetching tickers: {e}")
        return

    # Filter purely for liquid crypto pairs NOT in our list
    candidates = []
    for d in tickers:
        s = d["symbol"]
        if not s.endswith("USDT"): continue
        if s in EXISTING_COINS: continue
        # Exclude equities, indices, commodities
        if any(s.startswith(x) for x in ["XAU", "XAG", "SPCX", "SNDK", "SOXL", "CL", "SKH", "MU", "NVDA", "TSLA", "AAPL", "AMZN", "GOOG", "META", "COIN"]): continue
        vol = float(d.get("quoteVolume", 0))
        if vol >= 8_000_000: # Over $8 Million daily volume
            candidates.append({
                "symbol": s,
                "vol_m": round(vol / 1_000_000, 1),
                "price": float(d.get("lastPrice", 0))
            })

    candidates.sort(key=lambda x: x["vol_m"], reverse=True)
    top_25_new = candidates[:25]

    print(f"Discovered {len(top_25_new)} Highly-Liquid Brand-New Candidates:")
    for idx, c in enumerate(top_25_new, 1):
        print(f"  {idx:>2}. {c['symbol']:<12} | 24h Vol: ${c['vol_m']:>7.1f}M | Price: ${c['price']}")
    print("-" * 85)

    # 2. Load BTC benchmark
    h_dir = "historical_data"
    btc_path = os.path.join(h_dir, "BTCUSDT_4h.json")
    btc_candles = []
    if os.path.exists(btc_path):
        with open(btc_path, "r", encoding="utf-8") as f:
            btc_candles = json.load(f)
    if not btc_candles:
        btc_candles = fetch_klines("BTCUSDT", "4h", 500)
    
    btc_map = {c["time"]: c for c in btc_candles}
    btc_closes = [c["close"] for c in btc_candles]
    btc_ema50 = calculate_ema(btc_closes, 50)
    btc_ema_map = {btc_candles[i]["time"]: (btc_closes[i] >= btc_ema50[i]) for i in range(len(btc_candles))}

    print("\n" + "=" * 85)
    print("    RUNNING STRICT HERMES 3.5 SINGLE TIER BACKTEST ON ALL 25 NEW COINS")
    print("=" * 85)
    print("Rules: 5% Boundary Penetration, Inducement Wick >=18%, FVG, BTC Sentry, +1.6% BE Armor")
    print("-" * 85)

    test_results = []
    total_trades = 0
    total_wins = 0
    total_losses = 0

    for idx, c in enumerate(top_25_new, 1):
        sym = c["symbol"]
        print(f"[{idx:>2}/25] Fetching & Testing {sym:<12}...", end=" ", flush=True)
        candles = fetch_klines(sym, "4h", 600)
        if len(candles) < 60:
            print(f"SKIPPED (Only {len(candles)} candles available)")
            continue

        res = evaluate_hermes35(candles, sym, btc_map, btc_ema_map)
        res["vol_m"] = c["vol_m"]
        test_results.append(res)
        total_trades += res["trades"]
        total_wins += res["wins"]
        total_losses += res["losses"]
        print(f"DONE | Setups: {res['trades']:>2} | Win Rate: {res['win_rate']:>6.2f}% | PF: {res['profit_factor']:>5.2f}")

    print("\n" + "=" * 85)
    print("                     TOP 25 NEW COINS LEADERBOARD")
    print("=" * 85)
    header = f"{'Rank':<5} | {'Symbol':<12} | {'Setups':<8} | {'Wins':<6} | {'Losses':<7} | {'Win Rate':<10} | {'PF':<6} | {'24h Volume':<12}"
    print(header)
    print("-" * 85)

    # Rank by Win Rate and Trade Count
    test_results.sort(key=lambda x: (x["win_rate"], x["trades"]), reverse=True)

    for rank, r in enumerate(test_results, 1):
        status_icon = "👑" if r["win_rate"] >= 85.0 else ("✅" if r["win_rate"] >= 75.0 else "⚠️")
        print(f"{status_icon} #{rank:<2} | {r['sym']:<12} | {r['trades']:<8} | {r['wins']:<6} | {r['losses']:<7} | {r['win_rate']:>7.2f}%   | {r['profit_factor']:>5.2f} | ${r['vol_m']:>7.1f}M")

    print("=" * 85)
    agg_wr = (total_wins / total_trades * 100.0) if total_trades > 0 else 0.0
    print(f"\nAGGREGATE 25 NEW COINS PERFORMANCE:")
    print(f"  • Total Extra Trades Harvested : {total_trades} Trades")
    print(f"  • Total Wins (TP + Armor BE)  : {total_wins} Wins")
    print(f"  • Total Losses                : {total_losses} Losses")
    print(f"  • Aggregate Win Rate          : {agg_wr:.2f}%")
    print(f"  • Trade Frequency Boost       : +{total_trades / 3.0:.1f} Additional Trades Per Month!")
    print("=" * 85)

    # Export report to JSON artifact
    out_file = "new_25_coins_discovery_audit.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.time(),
            "total_new_coins_tested": len(test_results),
            "aggregate_trades": total_trades,
            "aggregate_wins": total_wins,
            "aggregate_losses": total_losses,
            "aggregate_win_rate": round(agg_wr, 2),
            "leaderboard": test_results
        }, f, indent=2)
    print(f"\nAudit Report saved to: {out_file} (ENGINE UNTOUCHED & FROZEN)")

if __name__ == "__main__":
    main()
