"""
HERMES 2.5 APEX HYBRID: 1-Year Comprehensive Audit Engine
Coins: ETCUSDT, ORDIUSDT, ADAUSDT
Period: 28 September 2025 to 28 September 2026 (1 Full Year - 365 Days)
Timeframes: 1H Fast Scalp & 4H Macro Swing
Metrics: Total Trades, Long Trades vs Short Trades, Long Win Rate vs Short Win Rate,
         PnL, Profit Factor, Max Drawdown, MFE, MAE, Win Streaks.
"""

import os
import sys
import json
import time
from datetime import datetime
import urllib.request
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TARGET_COINS = ["ETCUSDT", "ORDIUSDT", "ADAUSDT"]
BINANCE_BASE = "https://data-api.binance.vision/api/v3/klines"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")
os.makedirs(CACHE_DIR, exist_ok=True)

NOW_TS = int(time.time() * 1000)
ONE_YEAR_MS = 365 * 24 * 3600 * 1000
START_1Y_TS = NOW_TS - ONE_YEAR_MS

def download_full_year(symbol: str, interval: str) -> List[Dict[str, Any]]:
    cache_path = os.path.join(CACHE_DIR, f"{symbol}_{interval}_1y_audit.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if len(data) > 500:
                print(f"[CACHE] Loaded {symbol} {interval}: {len(data)} candles.")
                return data

    print(f"[DOWNLOAD] Fetching 1-year data for {symbol} ({interval})...")
    all_candles = []
    curr_start = START_1Y_TS

    while curr_start < NOW_TS:
        url = f"{BINANCE_BASE}?symbol={symbol}&interval={interval}&startTime={curr_start}&limit=1000"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                batch = json.loads(resp.read().decode("utf-8"))
                if not batch:
                    break
                for c in batch:
                    all_candles.append({
                        "time": int(c[0]),
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4]),
                        "volume": float(c[5])
                    })
                last_ts = int(batch[-1][0])
                if last_ts <= curr_start:
                    break
                curr_start = last_ts + (3600000 if interval == "1h" else 14400000)
                time.sleep(0.08)
        except Exception as e:
            print(f"Error fetching batch: {e}")
            break

    # Deduplicate by timestamp
    seen = set()
    clean_candles = []
    for c in all_candles:
        if c["time"] not in seen:
            seen.add(c["time"])
            clean_candles.append(c)

    clean_candles.sort(key=lambda x: x["time"])
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(clean_candles, f)

    print(f"[SAVED] {symbol} {interval}: {len(clean_candles)} candles (1-Year).")
    return clean_candles

def audit_symbol_hermes25(symbol: str, candles_1h: List[Dict[str, Any]], candles_4h: List[Dict[str, Any]], btc_map_4h: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    trades = []
    leverage = 5.0
    margin = 50.0 # $50 margin allocation per trade ($250 notional size)

    for tf, candles in [("1h", candles_1h), ("4h", candles_4h)]:
        n = len(candles)
        if n < 50:
            continue

        std_tp_pct = 0.022 if tf == "1h" else 0.028
        soft_sl_pct = 0.025 if tf == "1h" else 0.028
        hard_sl_pct = 0.036 if tf == "1h" else 0.038
        max_tap_window = 28
        max_hold = 40 if tf == "1h" else 30

        i = 20
        while i < n - max_hold:
            # -----------------------------------------------------------------
            # 1. LONG SETUP (Bullish Decisional OB + FVG + IDM Sweep)
            # -----------------------------------------------------------------
            if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                sub_w = candles[i:min(i+16, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx > i + 2:
                    gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                    if gain >= 0.050: # Sentry 2: Institutional Displacement >= 5.0%
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
                                        # Sentry 1: BTC Macro Brake (<2% dump)
                                        curr_4h_ts = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        btc_c = btc_map_4h.get(curr_4h_ts)
                                        btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                        sentry1_ok = btc_dump < 0.020

                                        c_range = tap_c["high"] - tap_c["low"]
                                        swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                        l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                        w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                        mt = (dec_top + dec_bot) / 2.0

                                        # Sentry 3: IDM Sweep + Wick >= 18% + MT Rejection
                                        if swept and w_ratio >= 0.18 and tap_c["close"] >= mt and sentry1_ok:
                                            entry = dec_top
                                            tp_p = entry * (1.0 + std_tp_pct)
                                            cur_sl = entry * (1.0 - soft_sl_pct)
                                            highest = entry
                                            lowest = entry
                                            outcome = "HOLD_EXPIRY"
                                            exit_price = entry
                                            pnl = 0.0

                                            for m in range(t + 1, min(t + max_hold, n)):
                                                bar = candles[m]
                                                highest = max(highest, bar["high"])
                                                lowest = min(lowest, bar["low"])

                                                # Dynamic Profit Armor: Stage 1 (+1.6% move -> Lock BE +0.2%)
                                                if bar["high"] >= entry * 1.016:
                                                    cur_sl = max(cur_sl, entry * 1.002)
                                                # Stage 2 (+2.2% move -> Lock +1.2%)
                                                if bar["high"] >= entry * 1.022:
                                                    cur_sl = max(cur_sl, entry * 1.012)

                                                if bar["high"] >= tp_p:
                                                    outcome = "TP_HIT"
                                                    exit_price = tp_p
                                                    pnl = margin * std_tp_pct * leverage
                                                    break
                                                elif bar["low"] <= cur_sl:
                                                    exit_price = cur_sl
                                                    if cur_sl > entry:
                                                        outcome = "BE_EXIT"
                                                        pnl = margin * (cur_sl - entry) / entry * leverage
                                                    else:
                                                        outcome = "SL_HIT"
                                                        pnl = -margin * soft_sl_pct * leverage
                                                    break

                                            mfe_pct = (highest - entry) / entry * 100 * leverage
                                            mae_pct = (entry - lowest) / entry * 100 * leverage

                                            trades.append({
                                                "symbol": symbol,
                                                "side": "LONG",
                                                "tf": tf,
                                                "entry_time": tap_c["time"],
                                                "entry": entry,
                                                "exit": exit_price,
                                                "outcome": outcome,
                                                "pnl": round(pnl, 2),
                                                "mfe": round(mfe_pct, 2),
                                                "mae": round(mae_pct, 2),
                                                "is_win": pnl > 0
                                            })
                                            i = t + 3
                                            break

            # -----------------------------------------------------------------
            # 2. SHORT SETUP (Bearish Decisional OB + FVG + IDM Sweep)
            # -----------------------------------------------------------------
            if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
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
                                        # Sentry 1: BTC Macro Pump (<2% pump)
                                        curr_4h_ts = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        btc_c = btc_map_4h.get(curr_4h_ts)
                                        btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                        sentry1_ok = btc_pump < 0.020

                                        c_range = tap_c["high"] - tap_c["low"]
                                        swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                        u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                        w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                        mt = (dec_top + dec_bot) / 2.0

                                        # Sentry 3: IDM Sweep + Wick >= 18% + MT Rejection
                                        if swept and w_ratio >= 0.18 and tap_c["close"] <= mt and sentry1_ok:
                                            entry = dec_bot
                                            tp_p = entry * (1.0 - std_tp_pct)
                                            cur_sl = entry * (1.0 + soft_sl_pct)
                                            lowest = entry
                                            highest = entry
                                            outcome = "HOLD_EXPIRY"
                                            exit_price = entry
                                            pnl = 0.0

                                            for m in range(t + 1, min(t + max_hold, n)):
                                                bar = candles[m]
                                                lowest = min(lowest, bar["low"])
                                                highest = max(highest, bar["high"])

                                                # Dynamic Profit Armor: Stage 1 (+1.6% drop -> Lock BE +0.2%)
                                                if bar["low"] <= entry * (1.0 - 0.016):
                                                    cur_sl = min(cur_sl, entry * 0.998)
                                                # Stage 2 (+2.2% drop -> Lock +1.2%)
                                                if bar["low"] <= entry * (1.0 - 0.022):
                                                    cur_sl = min(cur_sl, entry * 0.988)

                                                if bar["low"] <= tp_p:
                                                    outcome = "TP_HIT"
                                                    exit_price = tp_p
                                                    pnl = margin * std_tp_pct * leverage
                                                    break
                                                elif bar["high"] >= cur_sl:
                                                    exit_price = cur_sl
                                                    if cur_sl < entry:
                                                        outcome = "BE_EXIT"
                                                        pnl = margin * (entry - cur_sl) / entry * leverage
                                                    else:
                                                        outcome = "SL_HIT"
                                                        pnl = -margin * soft_sl_pct * leverage
                                                    break

                                            mfe_pct = (entry - lowest) / entry * 100 * leverage
                                            mae_pct = (highest - entry) / entry * 100 * leverage

                                            trades.append({
                                                "symbol": symbol,
                                                "side": "SHORT",
                                                "tf": tf,
                                                "entry_time": tap_c["time"],
                                                "entry": entry,
                                                "exit": exit_price,
                                                "outcome": outcome,
                                                "pnl": round(pnl, 2),
                                                "mfe": round(mfe_pct, 2),
                                                "mae": round(mae_pct, 2),
                                                "is_win": pnl > 0
                                            })
                                            i = t + 3
                                            break
            i += 1

    # Sort chronological
    trades.sort(key=lambda x: x["entry_time"])

    # Aggregate Statistics
    total_trades = len(trades)
    wins = [t for t in trades if t["is_win"]]
    losses = [t for t in trades if not t["is_win"] and t["outcome"] == "SL_HIT"]
    bes = [t for t in trades if t["outcome"] == "BE_EXIT"]

    win_count = len(wins)
    loss_count = len(losses)
    tot_evaluated = win_count + loss_count
    wr = round(win_count / tot_evaluated * 100, 1) if tot_evaluated > 0 else 0.0
    net_pnl = round(sum(t["pnl"] for t in trades), 2)

    gross_profit = sum(t["pnl"] for t in wins)
    gross_loss = abs(sum(t["pnl"] for t in losses))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 99.0

    # Long breakdown
    long_trades = [t for t in trades if t["side"] == "LONG"]
    l_wins = [t for t in long_trades if t["is_win"]]
    l_losses = [t for t in long_trades if not t["is_win"] and t["outcome"] == "SL_HIT"]
    l_tot = len(l_wins) + len(l_losses)
    long_wr = round(len(l_wins) / l_tot * 100, 1) if l_tot > 0 else 0.0
    long_pnl = round(sum(t["pnl"] for t in long_trades), 2)

    # Short breakdown
    short_trades = [t for t in trades if t["side"] == "SHORT"]
    s_wins = [t for t in short_trades if t["is_win"]]
    s_losses = [t for t in short_trades if not t["is_win"] and t["outcome"] == "SL_HIT"]
    s_tot = len(s_wins) + len(s_losses)
    short_wr = round(len(s_wins) / s_tot * 100, 1) if s_tot > 0 else 0.0
    short_pnl = round(sum(t["pnl"] for t in short_trades), 2)

    # Timeframe breakdown
    tf_1h = [t for t in trades if t["tf"] == "1h"]
    tf_4h = [t for t in trades if t["tf"] == "4h"]
    wr_1h = round(sum(1 for t in tf_1h if t["is_win"]) / (sum(1 for t in tf_1h if t["is_win"]) + sum(1 for t in tf_1h if t["outcome"] == "SL_HIT")) * 100, 1) if tf_1h else 0.0
    wr_4h = round(sum(1 for t in tf_4h if t["is_win"]) / (sum(1 for t in tf_4h if t["is_win"]) + sum(1 for t in tf_4h if t["outcome"] == "SL_HIT")) * 100, 1) if tf_4h else 0.0

    # Max Drawdown
    equity_curve = [50.0]
    peak = 50.0
    max_dd_dollars = 0.0
    for t in trades:
        curr = equity_curve[-1] + t["pnl"]
        equity_curve.append(curr)
        if curr > peak:
            peak = curr
        dd = peak - curr
        if dd > max_dd_dollars:
            max_dd_dollars = dd

    max_dd_pct = round(max_dd_dollars / peak * 100, 1) if peak > 0 else 0.0

    # Streaks
    max_win_streak = 0
    max_loss_streak = 0
    cur_w = 0
    cur_l = 0
    for t in trades:
        if t["is_win"]:
            cur_w += 1
            cur_l = 0
            if cur_w > max_win_streak:
                max_win_streak = cur_w
        elif t["outcome"] == "SL_HIT":
            cur_l += 1
            cur_w = 0
            if cur_l > max_loss_streak:
                max_loss_streak = cur_l

    avg_mfe = round(sum(t["mfe"] for t in trades) / len(trades), 1) if trades else 0.0
    avg_mae = round(sum(t["mae"] for t in trades) / len(trades), 1) if trades else 0.0

    return {
        "symbol": symbol,
        "total_trades": total_trades,
        "wins": win_count,
        "losses": loss_count,
        "be_exits": len(bes),
        "overall_win_rate": wr,
        "net_pnl": net_pnl,
        "profit_factor": profit_factor,
        "max_drawdown_pct": max_dd_pct,
        "max_drawdown_dollars": round(max_dd_dollars, 2),
        "avg_mfe": avg_mfe,
        "avg_mae": avg_mae,
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
        "longs": {
            "total": len(long_trades),
            "wins": len(l_wins),
            "losses": len(l_losses),
            "be_exits": sum(1 for t in long_trades if t["outcome"] == "BE_EXIT"),
            "win_rate": long_wr,
            "pnl": long_pnl
        },
        "shorts": {
            "total": len(short_trades),
            "wins": len(s_wins),
            "losses": len(s_losses),
            "be_exits": sum(1 for t in short_trades if t["outcome"] == "BE_EXIT"),
            "win_rate": short_wr,
            "pnl": short_pnl
        },
        "timeframes": {
            "1h": {"total": len(tf_1h), "win_rate": wr_1h, "pnl": round(sum(t["pnl"] for t in tf_1h), 2)},
            "4h": {"total": len(tf_4h), "win_rate": wr_4h, "pnl": round(sum(t["pnl"] for t in tf_4h), 2)}
        },
        "sample_trades": trades[-5:] # last 5 trades
    }

def main():
    print("=" * 80)
    print("   HERMES 2.5 APEX HYBRID: 1-YEAR (365-DAY) QUANT AUDIT")
    print("   Focus Assets: ETCUSDT, ORDIUSDT, ADAUSDT")
    print("   Window: 28-Sep-2025 to 28-Sep-2026")
    print("=" * 80)

    # 1. Fetch BTC 4H benchmark
    btc_4h = download_full_year("BTCUSDT", "4h")
    btc_map_4h = {c["time"]: c for c in btc_4h}

    results = {}
    for sym in TARGET_COINS:
        print(f"\n[*] Processing 1-Year Audit for {sym}...")
        c_1h = download_full_year(sym, "1h")
        c_4h = download_full_year(sym, "4h")
        res = audit_symbol_hermes25(sym, c_1h, c_4h, btc_map_4h)
        results[sym] = res

    # Save to JSON
    with open("audit_1year_etc_ordi_ada.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print("   FINAL 1-YEAR SUMMARY (ETC, ORDI, ADA)")
    print("=" * 80)
    for sym, r in results.items():
        print(f"\n>> {sym} <<")
        print(f"  Total Trades: {r['total_trades']} | Wins: {r['wins']} | Losses: {r['losses']} | BE: {r['be_exits']}")
        print(f"  Overall Win Rate: {r['overall_win_rate']}% | Net PnL: ${r['net_pnl']:+0.2f} | Profit Factor: {r['profit_factor']}")
        print(f"  Max Drawdown: -{r['max_drawdown_pct']}% (-${r['max_drawdown_dollars']}) | Max Win Streak: {r['max_win_streak']}W")
        print(f"  LONGS : {r['longs']['total']} trades | Wins: {r['longs']['wins']} | Losses: {r['longs']['losses']} | Win Rate: {r['longs']['win_rate']}% | PnL: ${r['longs']['pnl']:+0.2f}")
        print(f"  SHORTS: {r['shorts']['total']} trades | Wins: {r['shorts']['wins']} | Losses: {r['shorts']['losses']} | Win Rate: {r['shorts']['win_rate']}% | PnL: ${r['shorts']['pnl']:+0.2f}")
        print(f"  Timeframes: 1H WR: {r['timeframes']['1h']['win_rate']}% (${r['timeframes']['1h']['pnl']:+0.2f}) | 4H WR: {r['timeframes']['4h']['win_rate']}% (${r['timeframes']['4h']['pnl']:+0.2f})")
        print(f"  Avg MFE: +{r['avg_mfe']}% | Avg MAE: -{r['avg_mae']}%")

if __name__ == "__main__":
    main()
