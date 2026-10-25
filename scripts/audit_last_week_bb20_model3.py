"""
AUDIT BB 2.0 (MODEL 3 SNIPER) — REAL MARKET LAST WEEK TRIAL (OCT 7 - OCT 14, 2026)
===================================================================================
Fetches real 15m and 1D klines directly from Binance Public Futures API for Top-20 Champions.
Simulates exact BB 2.0 Model 3 Stepped Trailing SL + Single-Shot + Deca Compounding ($500 start).
"""

import os
import sys
import json
import ssl
import time
import urllib.request
from datetime import datetime, timezone
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

CHAMPIONS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT",
    "DOGEUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "NEARUSDT",
    "OPUSDT", "RENDERUSDT", "SUIUSDT", "TIAUSDT", "UNIUSDT",
    "XRPUSDT", "1000PEPEUSDT", "APTUSDT", "ARBUSDT", "FETUSDT"
]

PAIR_MAPPING = {
    "BTCUSDT": 1, "ETHUSDT": 1,
    "SOLUSDT": 2, "BNBUSDT": 2,
    "AVAXUSDT": 3, "DOGEUSDT": 3,
    "DOTUSDT": 4, "LINKUSDT": 4,
    "LTCUSDT": 5, "NEARUSDT": 5,
    "OPUSDT": 6, "RENDERUSDT": 6,
    "SUIUSDT": 7, "TIAUSDT": 7,
    "UNIUSDT": 8, "XRPUSDT": 8,
    "1000PEPEUSDT": 9, "APTUSDT": 9,
    "ARBUSDT": 10, "FETUSDT": 10
}

def fetch_klines(symbol: str, interval: str, limit: int = 1000):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candles = []
            for row in data:
                candles.append({
                    "time": int(row[0]),
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5])
                })
            return candles
    except Exception as e:
        print(f"Error fetching {symbol} {interval}: {e}")
        return []

def get_day_key(ts_ms):
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")

def run_last_week_audit():
    print("=" * 80)
    print("🎯 FETCHING REAL LIVE DATA FROM BINANCE FOR LAST 7 DAYS (OCT 7 - OCT 14, 2026)")
    print("=" * 80)

    # We want last 7 days: Oct 7, 8, 9, 10, 11, 12, 13, 14
    TARGET_DAYS = ["2026-10-07", "2026-10-08", "2026-10-09", "2026-10-10", "2026-10-11", "2026-10-12", "2026-10-13", "2026-10-14"]
    
    all_trades = []

    for sym in CHAMPIONS:
        # Fetch 15m candles (1000 candles = ~10.4 days)
        candles_15m = fetch_klines(sym, "15m", 1000)
        time.sleep(0.08) # rate limit courtesy
        if len(candles_15m) < 400:
            print(f"Warning: {sym} has only {len(candles_15m)} candles")
            continue

        # Bucket 15m candles by day
        day_buckets = defaultdict(list)
        for idx, c in enumerate(candles_15m):
            d_key = get_day_key(c["time"])
            day_buckets[d_key].append((idx, c))

        sorted_days = sorted(day_buckets.keys())

        for d_i in range(1, len(sorted_days)):
            curr_day = sorted_days[d_i]
            prev_day = sorted_days[d_i - 1]

            if curr_day not in TARGET_DAYS:
                continue

            prev_candles = [c for _, c in day_buckets[prev_day]]
            curr_entries = day_buckets[curr_day]

            if len(prev_candles) < 20 or len(curr_entries) < 10:
                continue

            pdh = max(c["high"] for c in prev_candles)
            pdl = min(c["low"] for c in prev_candles)

            long_taken_today = False
            short_taken_today = False

            for pos_in_day, (g_idx, c) in enumerate(curr_entries):
                if g_idx + 2 >= len(candles_15m):
                    continue

                c_o, c_h, c_l, c_c = c["open"], c["high"], c["low"], c["close"]
                next_c = candles_15m[g_idx + 1]
                next_c2 = candles_15m[g_idx + 2]

                # 1. BOTTOM OB (PDL) -> LONG
                if not long_taken_today:
                    dist_to_pdl = abs(c_l - pdl) / pdl if pdl > 0 else 1.0
                    if dist_to_pdl <= 0.015 or c_l <= pdl:
                        is_bearish = c_c < c_o
                        gain_1bar = (next_c["high"] - c_l) / c_l
                        gain_2bar = (next_c2["high"] - c_l) / c_l
                        has_fvg = next_c2["low"] > c_h

                        if (is_bearish or (c_h - c_l) > 0) and (gain_1bar >= 0.012 or gain_2bar >= 0.018) and has_fvg:
                            ob_high = c_h
                            ob_low = c_l
                            mt = (ob_high + ob_low) / 2.0
                            sl = ob_low * (1.0 - 0.0015)
                            risk = mt - sl

                            if risk > 0:
                                # Look for fill within 32 bars (8 hours)
                                fill_idx = -1
                                for w_idx in range(g_idx + 2, min(g_idx + 34, len(candles_15m))):
                                    b = candles_15m[w_idx]
                                    if b["low"] <= sl:
                                        break
                                    if b["low"] <= mt:
                                        fill_idx = w_idx
                                        break

                                if fill_idx != -1:
                                    long_taken_today = True
                                    trade = evaluate_trade(candles_15m, fill_idx, "LONG", mt, sl, risk, sym, curr_day)
                                    all_trades.append(trade)

                # 2. TOP OB (PDH) -> SHORT
                if not short_taken_today:
                    dist_to_pdh = abs(c_h - pdh) / pdh if pdh > 0 else 1.0
                    if dist_to_pdh <= 0.015 or c_h >= pdh:
                        is_bullish = c_c > c_o
                        drop_1bar = (c_h - next_c["low"]) / c_h
                        drop_2bar = (c_h - next_c2["low"]) / c_h
                        has_fvg = next_c2["high"] < c_l

                        if (is_bullish or (c_h - c_l) > 0) and (drop_1bar >= 0.012 or drop_2bar >= 0.018) and has_fvg:
                            ob_high = c_h
                            ob_low = c_l
                            mt = (ob_high + ob_low) / 2.0
                            sl = ob_high * (1.0 + 0.0015)
                            risk = sl - mt

                            if risk > 0:
                                fill_idx = -1
                                for w_idx in range(g_idx + 2, min(g_idx + 34, len(candles_15m))):
                                    b = candles_15m[w_idx]
                                    if b["high"] >= sl:
                                        break
                                    if b["high"] >= mt:
                                        fill_idx = w_idx
                                        break

                                if fill_idx != -1:
                                    short_taken_today = True
                                    trade = evaluate_trade(candles_15m, fill_idx, "SHORT", mt, sl, risk, sym, curr_day)
                                    all_trades.append(trade)

                if long_taken_today and short_taken_today:
                    break

    all_trades.sort(key=lambda t: t["fill_time"])
    print(f"\n✅ Total Qualified Trades in Past Week: {len(all_trades)}")

    # -------------------------------------------------------------------------
    # SIMULATION: DECA COMPOUNDING ($500 START, 10 SECTIONS @ $50 EACH)
    # -------------------------------------------------------------------------
    def run_sim(risk_pct: float, label: str):
        sections = {
            i: {
                "id": i,
                "balance": 50.0,
                "busy_until": 0,
                "trades": 0,
                "wins": 0,
                "saves": 0,
                "losses": 0,
                "pnl": 0.0
            }
            for i in range(1, 11)
        }

        executed_trades = []
        skipped_trades = []

        for t in all_trades:
            sec_id = PAIR_MAPPING.get(t["symbol"], 1)
            sec = sections[sec_id]

            if sec["busy_until"] > t["fill_time"]:
                # Section busy
                skipped_trades.append(t)
                continue

            sec["busy_until"] = t["exit_time"]
            sec["trades"] += 1

            r_pnl = t["pnl_r"]
            risk_usd = sec["balance"] * risk_pct
            dollar_pnl = risk_usd * r_pnl
            sec["balance"] = max(1.0, round(sec["balance"] + dollar_pnl, 2))
            sec["pnl"] = round(sec["pnl"] + dollar_pnl, 2)

            if "WIN" in t["outcome"]:
                sec["wins"] += 1
            elif "SAVE" in t["outcome"]:
                sec["saves"] += 1
            else:
                sec["losses"] += 1

            rec = dict(t)
            rec["sec_id"] = sec_id
            rec["risk_usd"] = risk_usd
            rec["dollar_pnl"] = dollar_pnl
            rec["sec_new_bal"] = sec["balance"]
            rec["total_equity"] = sum(s["balance"] for s in sections.values())
            executed_trades.append(rec)

        tot_eq = sum(s["balance"] for s in sections.values())
        tot_wins = sum(s["wins"] for s in sections.values())
        tot_saves = sum(s["saves"] for s in sections.values())
        tot_losses = sum(s["losses"] for s in sections.values())
        tot_exec = len(executed_trades)

        win_rate = (tot_wins / tot_exec * 100) if tot_exec else 0.0
        green_rate = ((tot_wins + tot_saves) / tot_exec * 100) if tot_exec else 0.0
        loss_rate = (tot_losses / tot_exec * 100) if tot_exec else 0.0
        net_profit = tot_eq - 500.0
        roi_pct = (net_profit / 500.0) * 100.0

        # Calculate Max Drawdown from total equity curve
        peak = 500.0
        max_dd = 0.0
        for rec in executed_trades:
            eq = rec["total_equity"]
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100.0
            if dd > max_dd:
                max_dd = dd

        return {
            "label": label,
            "risk_pct": risk_pct,
            "sections": sections,
            "executed_trades": executed_trades,
            "total_trades": tot_exec,
            "wins": tot_wins,
            "saves": tot_saves,
            "losses": tot_losses,
            "win_rate": win_rate,
            "green_rate": green_rate,
            "loss_rate": loss_rate,
            "initial_balance": 500.0,
            "final_balance": tot_eq,
            "net_profit": net_profit,
            "roi_pct": roi_pct,
            "max_dd": max_dd
        }

    res_5pct = run_sim(0.05, "Aggressive Deca (5% Section Risk)")
    res_2pct = run_sim(0.02, "Conservative Deca (2% Section Risk)")

    print("\n" + "=" * 80)
    print("🏆 PAST 7 DAYS (OCT 7 - OCT 14, 2026) BACKTEST RESULTS")
    print("=" * 80)

    for res in [res_2pct, res_5pct]:
        print(f"\n--- {res['label']} ---")
        print(f"• Total Trades Executed: {res['total_trades']}")
        print(f"• Wins: {res['wins']} | Fee Saves (BE): {res['saves']} | Losses (SL): {res['losses']}")
        print(f"• Pure Win Rate: {res['win_rate']:.1f}%")
        print(f"• Total Green / Protected Rate: {res['green_rate']:.1f}%")
        print(f"• Loss Rate: {res['loss_rate']:.1f}%")
        print(f"• Starting Balance: ${res['initial_balance']:.2f} USDT")
        print(f"• Final Balance: ${res['final_balance']:.2f} USDT")
        print(f"• Net Profit: {res['net_profit']:+.2f} USDT ({res['roi_pct']:+.2f}%)")
        print(f"• Max Account Drawdown: {res['max_dd']:.2f}%")

    # Section-by-section breakdown for 5% risk
    print("\n" + "-" * 80)
    print("🧩 SECTION-BY-SECTION BREAKDOWN (5% Compounding Risk):")
    print("-" * 80)
    print(f"{'SEC':<5} | {'ASSIGNED COINS':<22} | {'TRADES':<6} | {'W/S/L':<8} | {'START':<8} | {'FINAL':<10} | {'NET PNL':<10} | {'GAIN %':<8}")
    print("-" * 80)
    for s_id in range(1, 11):
        s = res_5pct["sections"][s_id]
        assigned = [c for c, sid in PAIR_MAPPING.items() if sid == s_id]
        assigned_str = ", ".join([c.replace("USDT","") for c in assigned])
        wsl = f"{s['wins']}/{s['saves']}/{s['losses']}"
        gain_pct = ((s['balance'] - 50.0) / 50.0) * 100.0
        print(f"Sec {s['id']:<2} | {assigned_str:<22} | {s['trades']:<6} | {wsl:<8} | $50.00   | ${s['balance']:<9.2f} | {s['pnl']:+9.2f} | {gain_pct:+7.1f}%")
    print("-" * 80)

    # Detailed trade sample
    print("\n" + "-" * 80)
    print("📜 RECENT EXECUTED TRADES LOG (SAMPLE):")
    print("-" * 80)
    for tr in res_5pct["executed_trades"][:12]:
        dt_str = datetime.fromtimestamp(tr["fill_time"]/1000, tz=timezone.utc).strftime("%d-%b %H:%M")
        print(f"[{dt_str}] #{tr['symbol']:<12} {tr['side']:<5} @ ${tr['entry']:<9.4f} | {tr['outcome']:<16} ({tr['pnl_r']:+5.2f}R) | PnL: {tr['dollar_pnl']:+6.2f}$ | Sec #{tr['sec_id']} (${tr['sec_new_bal']:.2f})")

    # Save results to json
    out_file = "last_week_bb20_audit_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target_period": "2026-10-07 to 2026-10-14",
            "summary_5pct": {
                "initial_balance": res_5pct["initial_balance"],
                "final_balance": res_5pct["final_balance"],
                "net_profit": res_5pct["net_profit"],
                "roi_pct": res_5pct["roi_pct"],
                "win_rate": res_5pct["win_rate"],
                "green_rate": res_5pct["green_rate"],
                "max_dd": res_5pct["max_dd"],
                "total_trades": res_5pct["total_trades"]
            },
            "summary_2pct": {
                "initial_balance": res_2pct["initial_balance"],
                "final_balance": res_2pct["final_balance"],
                "net_profit": res_2pct["net_profit"],
                "roi_pct": res_2pct["roi_pct"],
                "win_rate": res_2pct["win_rate"],
                "green_rate": res_2pct["green_rate"],
                "max_dd": res_2pct["max_dd"],
                "total_trades": res_2pct["total_trades"]
            },
            "trades": res_5pct["executed_trades"]
        }, f, indent=2)
    print(f"\nFull audit saved to: {out_file}")

def evaluate_trade(candles, fill_idx, side, entry_price, sl_price, risk, symbol, day_str, max_hold_bars=96, friction_r=0.06):
    active_sl = sl_price
    current_tier = 0
    n = len(candles)
    fill_candle = candles[fill_idx]
    fill_time = fill_candle["time"]

    for idx in range(fill_idx + 1, min(fill_idx + 1 + max_hold_bars, n)):
        b = candles[idx]
        b_h, b_l = b["high"], b["low"]
        exit_time = b["time"]

        if side == "LONG":
            if b_l <= active_sl:
                if current_tier == 0:
                    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": exit_time, "outcome": "LOSS (SL HIT)", "pnl_r": -1.0 - friction_r}
                elif current_tier == 1:
                    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": exit_time, "outcome": "FEE SHIELD SAVE", "pnl_r": 0.2 - friction_r}
                else:
                    locked_r = (current_tier - 1) * 0.5
                    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": exit_time, "outcome": f"WIN (+{locked_r:.1f}R)", "pnl_r": locked_r - friction_r}

            max_fav_r = (b_h - entry_price) / risk
            if max_fav_r >= 1.0:
                tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
                if tier_candidate > current_tier:
                    current_tier = tier_candidate
                    locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                    active_sl = entry_price + (locked_r * risk)

        else: # SHORT
            if b_h >= active_sl:
                if current_tier == 0:
                    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": exit_time, "outcome": "LOSS (SL HIT)", "pnl_r": -1.0 - friction_r}
                elif current_tier == 1:
                    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": exit_time, "outcome": "FEE SHIELD SAVE", "pnl_r": 0.2 - friction_r}
                else:
                    locked_r = (current_tier - 1) * 0.5
                    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": exit_time, "outcome": f"WIN (+{locked_r:.1f}R)", "pnl_r": locked_r - friction_r}

            max_fav_r = (entry_price - b_l) / risk
            if max_fav_r >= 1.0:
                tier_candidate = int((max_fav_r - 1.0) / 0.5) + 1
                if tier_candidate > current_tier:
                    current_tier = tier_candidate
                    locked_r = 0.2 if current_tier == 1 else (current_tier - 1) * 0.5
                    active_sl = entry_price - (locked_r * risk)

    last_c = candles[min(fill_idx + max_hold_bars, n - 1)]
    pnl_r = ((last_c["close"] - entry_price) / risk) if side == "LONG" else ((entry_price - last_c["close"]) / risk)
    return {"symbol": symbol, "day": day_str, "side": side, "entry": entry_price, "fill_time": fill_time, "exit_time": last_c["time"], "outcome": "TIMEOUT", "pnl_r": pnl_r - friction_r}

if __name__ == "__main__":
    run_last_week_audit()
