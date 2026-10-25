import json
import os
import sys
import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_data")

# 4-month window (120 days): From May 28, 2026 to Sep 25, 2026
START_TS_MS = int(datetime.datetime(2026, 5, 28, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
END_TS_MS = int(datetime.datetime(2026, 9, 25, 12, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)

print(f"[*] Starting HERMES 2.5 APEX 4-Month Quad-Compounding Backtest...")
print(f"[*] Window: May 28, 2026 -> Sep 25, 2026 (120 Days / 4 Months)")
print(f"[*] Accounts: 4 Parallel Slots (Binance 4H, Binance 1H, Bitget 4H, Bitget 1H)")
print(f"[*] Starting Balance per Account: $50.00 | Milestone Target: $2,000.00")
print(f"[*] Total Capital: $200.00 | Leverage: 5x Isolated Perpetual")

def load_data(sym, interval):
    fpath = os.path.join(DATA_DIR, f"{sym}_{interval}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    for c in data:
        c["open"] = float(c["open"])
        c["high"] = float(c["high"])
        c["low"] = float(c["low"])
        c["close"] = float(c["close"])
        c["volume"] = float(c.get("volume", 0.0))
    return data

all_data = {"1h": {}, "4h": {}}
for s in TOP_22_CHAMPIONS:
    for tf in ["1h", "4h"]:
        k = load_data(s, tf)
        if len(k) >= 500:
            all_data[tf][s] = k

btc_4h = load_data("BTCUSDT", "4h")
btc_map_4h = {c["time"]: c for c in btc_4h}

# Generate Long & Short Signals adhering strictly to HERMES 2.5 APEX
signals = []

for tf in ["4h", "1h"]:
    std_tp_pct = 0.028 if tf == "4h" else 0.022
    soft_sl_pct = 0.028 if tf == "4h" else 0.025
    hard_sl_pct = 0.038 if tf == "4h" else 0.036
    max_hold = 30 if tf == "4h" else 40

    for sym, candles in all_data[tf].items():
        n = len(candles)
        # Scan across all candles, but entry must fall within the 4-month window
        for i in range(25, n - 35):
            # ---------------- BUY (LONG) SIGNAL GENERATION ----------------
            if candles[i]["low"] == min(c["low"] for c in candles[i-15:i+1]):
                sub_w = candles[i:min(i+16, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx > i + 3:
                    gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                    if gain >= 0.050:
                        idm_low = candles[high_idx - 1]["low"]
                        best_mid = -1; max_bg = 0.0
                        for mid in range(i+1, high_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                            fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg; best_mid = mid
                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = max(dec_c["open"], dec_c["close"])
                            dec_bot = dec_c["low"]
                            has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                            ob_fib = (dec_top - candles[i]["low"]) / (max_high - candles[i]["low"])

                            if has_fvg and ob_fib <= 0.65:
                                for t in range(high_idx + 1, min(high_idx + 28, n)):
                                    if candles[t]["low"] <= dec_top * 1.0005:
                                        tap_c = candles[t]
                                        # Filter by 4-month window
                                        if not (START_TS_MS <= tap_c["time"] <= END_TS_MS):
                                            break
                                        
                                        # Sentry 1: BTC Causal Brake
                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                        if btc_dump >= 0.020:
                                            break

                                        # Sentry 3: IDM Sweep + >=18% Wick Absorption + 50% MT
                                        c_range = tap_c["high"] - tap_c["low"]
                                        swept_idm = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                        l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                        w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                        mt = (dec_top + dec_bot) / 2.0

                                        if swept_idm and (w_ratio >= 0.18) and tap_c["close"] >= mt:
                                            entry = dec_top
                                            tp_p = entry * (1.0 + std_tp_pct)
                                            soft_sl_p = entry * (1.0 - soft_sl_pct)
                                            hard_sl_p = entry * (1.0 - hard_sl_pct)

                                            res = None; exit_p = entry; exit_t = tap_c["time"]
                                            curr_sl = soft_sl_p; be_locked = False
                                            lowest_m = entry; highest_m = entry

                                            for m in range(t, min(t + max_hold, n)):
                                                h_bar = candles[m]["high"]
                                                l_bar = candles[m]["low"]
                                                lowest_m = min(lowest_m, l_bar)
                                                highest_m = max(highest_m, h_bar)

                                                if h_bar >= entry * 1.016: # +1.6% BE Lock
                                                    curr_sl = max(curr_sl, entry * 1.002)
                                                    be_locked = True
                                                if h_bar >= tp_p:
                                                    res = "TP_HIT"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                if l_bar <= hard_sl_p:
                                                    res = "HARD_SL_HIT"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                if candles[m]["close"] <= curr_sl:
                                                    res = "BREAK_EVEN" if (be_locked and curr_sl > entry) else "SL_HIT"
                                                    exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break

                                            if not res:
                                                fc = candles[min(t + max_hold, n - 1)]["close"]
                                                res = "TP_HIT" if fc >= tp_p * 0.995 else ("BREAK_EVEN" if fc >= entry else "TIMEOUT_CLOSE")
                                                exit_p = fc; exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                            mae_pct = max(0.0, (entry - lowest_m) / entry * 100.0)
                                            mfe_pct = max(0.0, (highest_m - entry) / entry * 100.0)
                                            gross_pct = (exit_p - entry) / entry

                                            signals.append({
                                                "sym": sym, "tf": tf, "side": "LONG",
                                                "entry_time": tap_c["time"], "exit_time": exit_t,
                                                "entry": entry, "exit": exit_p, "gross_pct": gross_pct,
                                                "res": res, "mae_pct": round(mae_pct, 2), "mfe_pct": round(mfe_pct, 2),
                                                "bars_held": (exit_t - tap_c["time"]) // (3600 * 1000 if tf == "1h" else 4 * 3600 * 1000)
                                            })
                                            break

            # ---------------- SELL (SHORT) SIGNAL GENERATION ----------------
            if candles[i]["high"] == max(c["high"] for c in candles[i-15:i+1]):
                sub_w = candles[i:min(i+16, n)]
                lows = [c["low"] for c in sub_w]
                min_low = min(lows)
                low_idx = i + lows.index(min_low)
                if low_idx > i + 3:
                    drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                    if drop >= 0.050:
                        idm_high = candles[low_idx - 1]["high"]
                        best_mid = -1; max_bg = 0.0
                        for mid in range(i+1, low_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                            fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg; best_mid = mid
                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = dec_c["high"]
                            dec_bot = min(dec_c["open"], dec_c["close"])
                            has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False

                            if has_bear_fvg:
                                for t in range(low_idx + 1, min(low_idx + 28, n)):
                                    if candles[t]["high"] >= dec_bot * 0.9995:
                                        tap_c = candles[t]
                                        if not (START_TS_MS <= tap_c["time"] <= END_TS_MS):
                                            break

                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0
                                        if btc_pump >= 0.020:
                                            break

                                        c_range = tap_c["high"] - tap_c["low"]
                                        swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                        u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                        w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                        mt = (dec_top + dec_bot) / 2.0

                                        if swept and (w_ratio >= 0.18) and tap_c["close"] <= mt:
                                            entry = dec_bot
                                            tp_p = entry * (1.0 - std_tp_pct)
                                            soft_sl_p = entry * (1.0 + soft_sl_pct)
                                            hard_sl_p = entry * (1.0 + hard_sl_pct)

                                            res = None; exit_p = entry; exit_t = tap_c["time"]
                                            curr_sl = soft_sl_p; be_locked = False
                                            lowest_m = entry; highest_m = entry

                                            for m in range(t, min(t + max_hold, n)):
                                                h_bar = candles[m]["high"]
                                                l_bar = candles[m]["low"]
                                                lowest_m = min(lowest_m, l_bar)
                                                highest_m = max(highest_m, h_bar)

                                                if l_bar <= entry * 0.984: # +1.6% BE Lock
                                                    curr_sl = min(curr_sl, entry * 0.998)
                                                    be_locked = True
                                                if l_bar <= tp_p:
                                                    res = "TP_HIT"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                                                if h_bar >= hard_sl_p:
                                                    res = "HARD_SL_HIT"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                                                if candles[m]["close"] >= curr_sl:
                                                    res = "BREAK_EVEN" if (be_locked and curr_sl < entry) else "SL_HIT"
                                                    exit_p = candles[m]["close"]; exit_t = candles[m]["time"]; break

                                            if not res:
                                                fc = candles[min(t + max_hold, n - 1)]["close"]
                                                res = "TP_HIT" if fc <= tp_p * 1.005 else ("BREAK_EVEN" if fc <= entry else "TIMEOUT_CLOSE")
                                                exit_p = fc; exit_t = candles[min(t + max_hold, n - 1)]["time"]

                                            mae_pct = max(0.0, (highest_m - entry) / entry * 100.0)
                                            mfe_pct = max(0.0, (entry - lowest_m) / entry * 100.0)
                                            gross_pct = (entry - exit_p) / entry

                                            signals.append({
                                                "sym": sym, "tf": tf, "side": "SHORT",
                                                "entry_time": tap_c["time"], "exit_time": exit_t,
                                                "entry": entry, "exit": exit_p, "gross_pct": gross_pct,
                                                "res": res, "mae_pct": round(mae_pct, 2), "mfe_pct": round(mfe_pct, 2),
                                                "bars_held": (exit_t - tap_c["time"]) // (3600 * 1000 if tf == "1h" else 4 * 3600 * 1000)
                                            })
                                            break

# Sort all signals strictly chronologically
signals.sort(key=lambda x: x["entry_time"])
print(f"[+] Total Verified Signals Generated in 4 Months: {len(signals)}")
print(f"    - 4H Signals: {len([s for s in signals if s['tf'] == '4h'])}")
print(f"    - 1H Signals: {len([s for s in signals if s['tf'] == '1h'])}")

# ----------------- SIMULATE 4 PARALLEL SLOTS -----------------
# 1. Binance 4H Macro
# 2. Binance 1H Intraday
# 3. Bitget 4H Macro
# 4. Bitget 1H Intraday

class QuadAccount:
    def __init__(self, name, channel, tf, exchange, initial_balance=50.0, target=2000.0):
        self.name = name
        self.channel = channel
        self.tf = tf
        self.exchange = exchange
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.target = target
        self.trades = []
        self.free_at = 0
        self.active_trade = None
        self.milestones_hit = {} # {amount: {"trade_num": int, "date": str, "balance": float}}
        self.peak_balance = initial_balance
        self.max_drawdown = 0.0

    def check_milestones(self, trade_num, date_str):
        for m in [100, 250, 500, 1000, 2000]:
            if self.balance >= m and m not in self.milestones_hit:
                self.milestones_hit[m] = {
                    "trade_num": trade_num,
                    "date": date_str,
                    "balance": round(self.balance, 2)
                }

    def execute_trade(self, sig):
        # 100% Compounding: Margin = current balance
        margin = self.balance
        leverage = 5.0
        notional = margin * leverage

        # Taker fee: 0.04% entry + 0.04% exit = 0.08% on notional
        fee = notional * 0.0008

        # PnL with fee
        raw_pnl = notional * sig["gross_pct"]
        net_pnl = raw_pnl - fee

        # Update balance
        prev_bal = self.balance
        self.balance += net_pnl
        if self.balance < 1.0: # blown account protection
            self.balance = 0.0

        # Drawdown tracking
        if self.balance > self.peak_balance:
            self.peak_balance = self.balance
        dd = (self.peak_balance - self.balance) / self.peak_balance * 100.0 if self.peak_balance > 0 else 0
        if dd > self.max_drawdown:
            self.max_drawdown = dd

        self.free_at = sig["exit_time"]

        entry_dt = datetime.datetime.fromtimestamp(sig["entry_time"] / 1000, datetime.timezone.utc)
        date_str = entry_dt.strftime("%Y-%m-%d %H:%M UTC")

        trade_info = {
            "num": len(self.trades) + 1,
            "sym": sig["sym"],
            "tf": sig["tf"],
            "side": sig["side"],
            "entry_date": date_str,
            "entry": sig["entry"],
            "exit": sig["exit"],
            "res": sig["res"],
            "gross_pct": round(sig["gross_pct"] * 100, 2),
            "roe_pct": round((net_pnl / margin) * 100, 2),
            "net_pnl": round(net_pnl, 2),
            "balance_after": round(self.balance, 2),
            "mae_pct": sig["mae_pct"],
            "mfe_pct": sig["mfe_pct"],
            "bars_held": sig["bars_held"]
        }
        self.trades.append(trade_info)
        self.check_milestones(trade_info["num"], date_str)

accounts = {
    "binance_4h": QuadAccount("Binance 4H Macro", "binance_4h", "4h", "BINANCE", 50.0, 2000.0),
    "binance_1h": QuadAccount("Binance 1H Intraday", "binance_1h", "1h", "BINANCE", 50.0, 2000.0),
    "bitget_4h": QuadAccount("Bitget 4H Macro", "bitget_4h", "4h", "BITGET", 50.0, 2000.0),
    "bitget_1h": QuadAccount("Bitget 1H Intraday", "bitget_1h", "1h", "BITGET", 50.0, 2000.0)
}

# Strict multi-account dispatcher
# Active coin tracking to prevent collision (no duplicate coin open simultaneously)
active_coins_until = {}

for s in signals:
    sig_time = s["entry_time"]
    sig_tf = s["tf"]
    sym = s["sym"]

    # Purge expired coins
    active_coins_until = {c: exp for c, exp in active_coins_until.items() if exp > sig_time}

    # Anti-collision check
    if sym in active_coins_until:
        continue

    # Find candidate slots matching timeframe
    candidates = []
    if sig_tf == "4h":
        candidates = [accounts["binance_4h"], accounts["bitget_4h"]]
    elif sig_tf == "1h":
        candidates = [accounts["binance_1h"], accounts["bitget_1h"]]

    # Pick first available slot
    available_slot = None
    for slot in candidates:
        if slot.free_at <= sig_time and slot.balance > 0:
            available_slot = slot
            break

    if available_slot:
        available_slot.execute_trade(s)
        active_coins_until[sym] = s["exit_time"]

# ----------------- PRINT IN-DEPTH COMPREHENSIVE REPORT -----------------
print("\n" + "="*85)
print("             HERMES 2.5 APEX: 4-MONTH QUAD COMPOUNDING AUDIT RESULTS")
print("="*85)

total_trades_all = 0
total_wins_all = 0
combined_final = 0.0

for key, acc in accounts.items():
    wins = len([t for t in acc.trades if t["net_pnl"] > 0])
    losses = len([t for t in acc.trades if t["net_pnl"] < 0])
    bes = len([t for t in acc.trades if t["net_pnl"] == 0 or t["res"] == "BREAK_EVEN"])
    tot = len(acc.trades)
    wr = (wins / tot * 100.0) if tot > 0 else 0.0

    total_trades_all += tot
    total_wins_all += wins
    combined_final += acc.balance

    print(f"\n[{acc.name.upper()}] ({acc.exchange} • {acc.tf.upper()} • 5x Leverage)")
    print(f"  • Starting Balance:    ${acc.initial_balance:.2f}")
    print(f"  • Final Balance:       ${acc.balance:,.2f} ({((acc.balance - acc.initial_balance)/acc.initial_balance*100):+,.1f}%)")
    print(f"  • Total Trades Taken:  {tot} Trades")
    print(f"  • Win / Loss / BE:     {wins} Wins | {losses} Losses | {bes} Break-Evens")
    print(f"  • Win Rate:            {wr:.1f}%")
    print(f"  • Max Drawdown:        {acc.max_drawdown:.1f}%")

    print(f"  • MILESTONE LADDER:")
    for m in [100, 250, 500, 1000, 2000]:
        if m in acc.milestones_hit:
            hit = acc.milestones_hit[m]
            print(f"    - Target ${m:,}:  REACHED at Trade #{hit['trade_num']} ({hit['date']}) -> Balance: ${hit['balance']:,.2f}")
        else:
            print(f"    - Target ${m:,}:  Not reached within 4 months (Max Reached: ${acc.peak_balance:,.2f})")

    # Sample trades breakdown
    if acc.trades:
        print(f"  • Last 3 Trades Executed:")
        for t in acc.trades[-3:]:
            pnl_sign = "+" if t["net_pnl"] >= 0 else ""
            print(f"    Trade #{t['num']:<2} | {t['entry_date'][:10]} | {t['sym']:<10} {t['side']:<5} | ROE: {t['roe_pct']:+6.1f}% | PnL: {pnl_sign}${t['net_pnl']:<7.2f} | Bal: ${t['balance_after']:<8.2f} | MAE: -{t['mae_pct']:.1f}% | MFE: +{t['mfe_pct']:.1f}%")

print("\n" + "="*85)
print("                     COMBINED 4-ACCOUNT PORTFOLIO TOTALS")
print("="*85)
print(f"  • Initial Capital Invested:   $200.00 ($50.00 x 4 accounts)")
print(f"  • Total Portfolio Capital:    ${combined_final:,.2f} ({((combined_final - 200.0)/200.0*100):+,.1f}% ROI)")
print(f"  • Total Trades Executed:      {total_trades_all} Trades across 4 accounts")
print(f"  • Aggregate Win Rate:         {(total_wins_all / total_trades_all * 100.0) if total_trades_all > 0 else 0:.1f}%")
print("="*85)

# Save JSON results for artifacts & records
summary_report = {
    "window": "May 28, 2026 - Sep 25, 2026 (4 Months / 120 Days)",
    "initial_capital_total": 200.0,
    "final_capital_total": round(combined_final, 2),
    "total_trades": total_trades_all,
    "aggregate_win_rate": round((total_wins_all / total_trades_all * 100.0) if total_trades_all > 0 else 0, 1),
    "accounts": {k: {
        "name": acc.name,
        "final_balance": round(acc.balance, 2),
        "total_trades": len(acc.trades),
        "wins": len([t for t in acc.trades if t["net_pnl"] > 0]),
        "losses": len([t for t in acc.trades if t["net_pnl"] < 0]),
        "win_rate": round(len([t for t in acc.trades if t["net_pnl"] > 0]) / len(acc.trades) * 100.0, 1) if acc.trades else 0.0,
        "max_drawdown": round(acc.max_drawdown, 1),
        "milestones": acc.milestones_hit,
        "trades": acc.trades
    } for k, acc in accounts.items()}
}

with open("hermes_4month_quad_compounding_audit.json", "w", encoding="utf-8") as f:
    json.dump(summary_report, f, indent=2)

print("\n[✔] Full JSON Audit Saved to: hermes_4month_quad_compounding_audit.json")
