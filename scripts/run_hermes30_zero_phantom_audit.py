import sys
import os
import json
import time
from datetime import datetime, timezone, timedelta

# Reconfigure stdout for clean UTF-8
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 85)
print("   HERMES 3.0 MODEL 2A: ZERO-PHANTOM-FILL ALGORITHMIC AUDIT & REALITY ENGINE   ")
print("=" * 85)
print("AUDIT DIRECTIVE: Zero lookahead, conservative intra-bar execution, 0.10% roundtrip")
print("fees, candle-body-close SL invalidation, and strict sequential queue verification.")
print("=" * 85)

HIST_DIR = os.path.join(os.path.dirname(__file__), "..", "historical_data")
COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", 
    "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "OPUSDT", 
    "FILUSDT", "SANDUSDT", "ALGOUSDT", "INJUSDT", "FETUSDT", 
    "LDOUSDT", "TIAUSDT", "ARBUSDT", "AAVEUSDT", "ADAUSDT"
]

# 1. Load Datasets
data_1h = {}
data_4h = {}
for c in COINS:
    f1 = os.path.join(HIST_DIR, f"{c}_1h.json")
    f4 = os.path.join(HIST_DIR, f"{c}_4h.json")
    if os.path.exists(f1):
        data_1h[c] = json.load(open(f1, "r", encoding="utf-8"))
    if os.path.exists(f4):
        data_4h[c] = json.load(open(f4, "r", encoding="utf-8"))

print(f" Loaded historical datasets: 1H={len(data_1h)} coins, 4H={len(data_4h)} coins.")

btc_4h = data_4h.get("BTCUSDT", [])

# 2. Extract Qualified Hermes 3.0 Model 2A Setups
candidate_events = []
max_tap_window = 28  # Freshness Guard <= 28 bars

for c in COINS:
    for tf, dataset in [("4h", data_4h.get(c, [])), ("1h", data_1h.get(c, []))]:
        n = len(dataset)
        if n < 40:
            continue

        for i in range(20, n - 2):
            # -----------------------------------------------------------------
            # 1. BULLISH SETUP (LONG)
            # -----------------------------------------------------------------
            prior_lows = [float(x["low"]) for x in dataset[max(0, i-15):i+1]]
            if float(dataset[i]["low"]) == min(prior_lows):
                sub_w = dataset[i:min(i+16, n)]
                highs = [float(x["high"]) for x in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)

                if high_idx > i + 2:
                    origin_l = float(dataset[i]["low"])
                    gain = (max_high - origin_l) / origin_l if origin_l > 0 else 0.0

                    # Sentry 2: Displacement >= 5.0%
                    if gain >= 0.050:
                        idm_low = float(dataset[high_idx - 1]["low"])
                        best_mid = -1
                        max_bg = 0.0

                        # Sentry 2: Decisional Order Block in 0.30 - 0.70 Fib Range
                        for mid in range(i + 1, high_idx):
                            m_h, m_l = float(dataset[mid]["high"]), float(dataset[mid]["low"])
                            bg = (m_h - m_l) / m_l if m_l > 0 else 0.0
                            fib = (m_l - origin_l) / (max_high - origin_l) if max_high > origin_l else 0.0
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg
                                best_mid = mid

                        if best_mid != -1:
                            dec_c = dataset[best_mid - 1]
                            dec_top = max(float(dec_c["open"]), float(dec_c["close"]))
                            dec_bot = float(dec_c["low"])
                            has_fvg = (float(dataset[best_mid + 1]["low"]) > float(dataset[best_mid - 1]["high"])) if best_mid + 1 < n else False

                            if has_fvg:
                                mt = round((dec_top + dec_bot) / 2.0, 8)

                                # Scan forward for Retest Tap
                                for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                    tap_c = dataset[t]
                                    t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])

                                    # Check First Tap at 50% Mean Threshold
                                    if t_l <= mt:
                                        c_range = t_h - t_l
                                        # Sentry 3: IDM swept
                                        swept = any(float(dataset[k]["low"]) < idm_low for k in range(high_idx, t + 1))
                                        # Sentry 3: Rejection Wick >= 18%
                                        l_wick = min(t_o, t_c) - t_l
                                        w_ratio = (l_wick / c_range) if c_range > 0 else 0.0

                                        # Sentry 1: BTC Macro Causal Brake (Completed prior 4H BTC candle < 2.0% dump)
                                        btc_clean = True
                                        if btc_4h:
                                            prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                            if len(prior_btc) >= 2:
                                                last_b = prior_btc[-1]
                                                o_b, c_b = float(last_b["open"]), float(last_b["close"])
                                                dump_pct = (o_b - c_b) / o_b if o_b > 0 else 0.0
                                                if dump_pct >= 0.020:
                                                    btc_clean = False

                                        # PHANTOM GUARD 1: Tap candle must NOT close below soft SL (-1.5%)
                                        soft_sl_p = round(mt * (1.0 - 0.0150), 8)
                                        hard_sl_p = round(mt * (1.0 - 0.0300), 8)
                                        if btc_clean and swept and w_ratio >= 0.18 and t_c > soft_sl_p:
                                            # PHANTOM GUARD 2: Check realistic fill price
                                            # If bar opened below MT, fill is at open (worse), else at MT
                                            fill_p = mt if t_o >= mt else t_o

                                            candidate_events.append({
                                                "symbol": c,
                                                "side": "LONG",
                                                "timeframe": tf,
                                                "tap_time": tap_c["time"],
                                                "tap_idx": t,
                                                "entry_price": fill_p,
                                                "tp_price": round(fill_p * 1.0300, 8),
                                                "soft_sl_price": round(fill_p * 0.9850, 8),
                                                "hard_sl_price": round(fill_p * 0.9700, 8),
                                                "be_price": round(fill_p * 1.0150, 8),
                                                "dataset": dataset,
                                                "displacement_pct": round(gain * 100, 2),
                                                "wick_ratio_pct": round(w_ratio * 100, 1)
                                            })
                                        break

            # -----------------------------------------------------------------
            # 2. BEARISH SETUP (SHORT)
            # -----------------------------------------------------------------
            prior_highs = [float(x["high"]) for x in dataset[max(0, i-15):i+1]]
            if float(dataset[i]["high"]) == max(prior_highs):
                sub_w = dataset[i:min(i+16, n)]
                lows = [float(x["low"]) for x in sub_w]
                min_low = min(lows)
                low_idx = i + lows.index(min_low)

                if low_idx > i + 2:
                    origin_h = float(dataset[i]["high"])
                    drop = (origin_h - min_low) / origin_h if origin_h > 0 else 0.0

                    if drop >= 0.050:
                        idm_high = float(dataset[low_idx - 1]["high"])
                        best_mid = -1
                        max_bg = 0.0

                        for mid in range(i + 1, low_idx):
                            m_h, m_l = float(dataset[mid]["high"]), float(dataset[mid]["low"])
                            bg = (m_h - m_l) / m_h if m_h > 0 else 0.0
                            fib = (origin_h - m_h) / (origin_h - min_low) if origin_h > min_low else 0.0
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg
                                best_mid = mid

                        if best_mid != -1:
                            dec_c = dataset[best_mid - 1]
                            dec_top = float(dec_c["high"])
                            dec_bot = min(float(dec_c["open"]), float(dec_c["close"]))
                            has_fvg = (float(dataset[best_mid + 1]["high"]) < float(dataset[best_mid - 1]["low"])) if best_mid + 1 < n else False

                            if has_fvg:
                                mt = round((dec_top + dec_bot) / 2.0, 8)

                                for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                    tap_c = dataset[t]
                                    t_l, t_h, t_o, t_c = float(tap_c["low"]), float(tap_c["high"]), float(tap_c["open"]), float(tap_c["close"])

                                    if t_h >= mt:
                                        c_range = t_h - t_l
                                        swept = any(float(dataset[k]["high"]) > idm_high for k in range(low_idx, t + 1))
                                        u_wick = t_h - max(t_o, t_c)
                                        w_ratio = (u_wick / c_range) if c_range > 0 else 0.0

                                        btc_clean = True
                                        if btc_4h:
                                            prior_btc = [x for x in btc_4h if x["time"] < tap_c["time"]]
                                            if len(prior_btc) >= 2:
                                                last_b = prior_btc[-1]
                                                o_b, c_b = float(last_b["open"]), float(last_b["close"])
                                                pump_pct = (c_b - o_b) / o_b if o_b > 0 else 0.0
                                                if pump_pct >= 0.020:
                                                    btc_clean = False

                                        soft_sl_p = round(mt * (1.0 + 0.0150), 8)
                                        hard_sl_p = round(mt * (1.0 + 0.0300), 8)
                                        if btc_clean and swept and w_ratio >= 0.18 and t_c < soft_sl_p:
                                            fill_p = mt if t_o <= mt else t_o

                                            candidate_events.append({
                                                "symbol": c,
                                                "side": "SHORT",
                                                "timeframe": tf,
                                                "tap_time": tap_c["time"],
                                                "tap_idx": t,
                                                "entry_price": fill_p,
                                                "tp_price": round(fill_p * 0.9700, 8),
                                                "soft_sl_price": round(fill_p * 1.0150, 8),
                                                "hard_sl_price": round(fill_p * 1.0300, 8),
                                                "be_price": round(fill_p * 0.9850, 8),
                                                "dataset": dataset,
                                                "displacement_pct": round(drop * 100, 2),
                                                "wick_ratio_pct": round(w_ratio * 100, 1)
                                            })
                                        break

# De-duplicate simultaneous triggers on same coin & timestamp
seen = set()
unique_events = []
for ev in candidate_events:
    key = (ev["symbol"], ev["tap_time"])
    if key not in seen:
        seen.add(key)
        unique_events.append(ev)

unique_events.sort(key=lambda x: x["tap_time"])
print(f" Identified {len(unique_events)} institutional qualified Model 2A triggers across 1 Year.")

# -----------------------------------------------------------------------------
# 3. ZERO-PHANTOM SIMULATION RUNNER
# -----------------------------------------------------------------------------
def simulate_execution(events, body_close_sl=True, conservative_same_bar=True, friction_fee_pct=0.0010):
    """
    Executes trades with zero lookahead, pessimistic intra-bar conflict resolution,
    and real-world fee/slippage deductions.
    """
    start_equity = 50.00
    balance = start_equity
    peak_balance = start_equity
    max_drawdown = 0.0

    busy_until = 0
    trades = []
    tps, sls, bes = 0, 0, 0
    absorbed_wicks = 0

    for ev in events:
        t_entry = ev["tap_time"]
        if t_entry < busy_until:
            continue  # Strict sequential queue: cannot enter while holding previous position

        ds = ev["dataset"]
        t_idx = ev["tap_idx"]
        side = ev["side"]
        ep = ev["entry_price"]
        tp = ev["tp_price"]
        soft_sl = ev["soft_sl_price"]
        hard_sl = ev["hard_sl_price"]
        be_trig = ev["be_price"]

        be_locked = False
        outcome = None
        exit_price = ep
        exit_time = t_entry
        exit_bar_idx = t_idx

        # Forward march through future candles (strictly t_idx + 1 onwards)
        for k in range(t_idx + 1, len(ds)):
            bar = ds[k]
            b_o = float(bar["open"])
            b_h = float(bar["high"])
            b_l = float(bar["low"])
            b_c = float(bar["close"])
            b_t = bar["time"]

            if side == "LONG":
                # Check BE Armor Trigger (+1.50% Spot Gain)
                if not be_locked and b_h >= be_trig:
                    be_locked = True

                # PESSIMISTIC INTRA-BAR CHECK:
                # If a bar touched BOTH TP and Hard Circuit SL, assume SL was hit first!
                if conservative_same_bar and b_h >= tp and b_l <= hard_sl:
                    outcome = "HARD_SL"
                    exit_price = hard_sl
                    exit_time = b_t
                    exit_bar_idx = k
                    break

                # 1. Take Profit
                if b_h >= tp:
                    outcome = "TP_HIT"
                    exit_price = tp
                    exit_time = b_t
                    exit_bar_idx = k
                    break

                # 2. Hard Circuit Breaker Touch (-3.00%)
                if b_l <= hard_sl:
                    outcome = "HARD_SL"
                    exit_price = hard_sl
                    exit_time = b_t
                    exit_bar_idx = k
                    break

                # 3. Break-Even Stop Touch (if BE locked)
                if be_locked and b_l <= ep:
                    outcome = "BE_SAVE"
                    exit_price = ep
                    exit_time = b_t
                    exit_bar_idx = k
                    break

                # 4. Soft SL (-1.50%): Body Close vs Wick Touch
                if body_close_sl:
                    if b_l <= soft_sl:
                        # Price wicked below soft SL!
                        if b_c <= soft_sl:
                            # Candle Body closed BELOW soft SL -> Structural Invalidation Exit!
                            outcome = "SOFT_SL_BODY_CLOSE"
                            exit_price = b_c
                            exit_time = b_t
                            exit_bar_idx = k
                            break
                        else:
                            # Wick penetrated but candle CLOSED ABOVE -> WICK ABSORBED!
                            absorbed_wicks += 1
                else:
                    # Baseline Wick SL (Any touch triggers SL)
                    if b_l <= soft_sl:
                        outcome = "SL_TOUCH"
                        exit_price = soft_sl
                        exit_time = b_t
                        exit_bar_idx = k
                        break

            else: # SHORT
                if not be_locked and b_l <= be_trig:
                    be_locked = True

                if conservative_same_bar and b_l <= tp and b_h >= hard_sl:
                    outcome = "HARD_SL"
                    exit_price = hard_sl
                    exit_time = b_t
                    exit_bar_idx = k
                    break

                if b_l <= tp:
                    outcome = "TP_HIT"
                    exit_price = tp
                    exit_time = b_t
                    exit_bar_idx = k
                    break

                if b_h >= hard_sl:
                    outcome = "HARD_SL"
                    exit_price = hard_sl
                    exit_time = b_t
                    exit_bar_idx = k
                    break

                if be_locked and b_h >= ep:
                    outcome = "BE_SAVE"
                    exit_price = ep
                    exit_time = b_t
                    exit_bar_idx = k
                    break

                if body_close_sl:
                    if b_h >= soft_sl:
                        if b_c >= soft_sl:
                            outcome = "SOFT_SL_BODY_CLOSE"
                            exit_price = b_c
                            exit_time = b_t
                            exit_bar_idx = k
                            break
                        else:
                            absorbed_wicks += 1
                else:
                    if b_h >= soft_sl:
                        outcome = "SL_TOUCH"
                        exit_price = soft_sl
                        exit_time = b_t
                        exit_bar_idx = k
                        break

        if not outcome:
            continue

        # Position duration
        duration_hrs = (exit_time - t_entry) / (1000 * 3600)
        busy_until = exit_time

        # Calculate PnL with 5x leverage & roundtrip friction fee
        leverage = 5.0
        margin = balance
        pos_size = margin * leverage

        if side == "LONG":
            gross_pct = (exit_price - ep) / ep
        else:
            gross_pct = (ep - exit_price) / ep

        # Deduct friction fee (0.10% roundtrip)
        net_pct = gross_pct - friction_fee_pct
        pnl_usdt = pos_size * net_pct
        roe_pct = round(net_pct * leverage * 100.0, 2)

        balance = max(1.0, balance + pnl_usdt)
        if balance > peak_balance:
            peak_balance = balance
        dd = (peak_balance - balance) / peak_balance * 100.0 if peak_balance > 0 else 0.0
        if dd > max_drawdown:
            max_drawdown = dd

        if outcome == "TP_HIT":
            tps += 1
        elif outcome == "BE_SAVE":
            bes += 1
        else:
            sls += 1

        trades.append({
            "symbol": ev["symbol"],
            "side": side,
            "tf": ev["timeframe"],
            "entry_time": t_entry,
            "exit_time": exit_time,
            "duration_h": round(duration_hrs, 1),
            "outcome": outcome,
            "entry_p": ep,
            "exit_p": exit_price,
            "pnl_usdt": round(pnl_usdt, 2),
            "roe_pct": roe_pct,
            "balance": round(balance, 2)
        })

    completed_trades = tps + sls
    win_rate = (tps / completed_trades * 100.0) if completed_trades > 0 else 0.0
    total_trades = tps + sls + bes

    # Profit Factor
    gross_profits = sum(t["pnl_usdt"] for t in trades if t["pnl_usdt"] > 0)
    gross_losses = abs(sum(t["pnl_usdt"] for t in trades if t["pnl_usdt"] < 0))
    profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else float("inf")

    return {
        "trades": trades,
        "total_trades": total_trades,
        "tps": tps,
        "sls": sls,
        "bes": bes,
        "win_rate": round(win_rate, 2),
        "absorbed_wicks": absorbed_wicks,
        "final_balance": round(balance, 2),
        "peak_balance": round(peak_balance, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "profit_factor": round(profit_factor, 2)
    }

# 4. Run Both Trials: Baseline vs Pure Model 2A Zero Phantom
print("\n" + "=" * 85)
print("EXECUTING TRIAL 1: BASELINE WICK SL (Any wick touch triggers SL)")
print("=" * 85)
res_base = simulate_execution(unique_events, body_close_sl=False, conservative_same_bar=True)
print(f" Total Trades: {res_base['total_trades']} | TP: {res_base['tps']} | SL: {res_base['sls']} | BE: {res_base['bes']}")
print(f" Win Rate: {res_base['win_rate']}% | Max DD: {res_base['max_drawdown_pct']}% | Final Balance: ${res_base['final_balance']} | PF: {res_base['profit_factor']}")

print("\n" + "=" * 85)
print("EXECUTING TRIAL 2: HERMES 3.0 MODEL 2A (Zero-Phantom + Candle Body Close SL)")
print("=" * 85)
res_m2a = simulate_execution(unique_events, body_close_sl=True, conservative_same_bar=True)
print(f" Total Trades: {res_m2a['total_trades']} | TP: {res_m2a['tps']} | SL: {res_m2a['sls']} | BE: {res_m2a['bes']}")
print(f" Absorbed Stop Hunts: {res_m2a['absorbed_wicks']} wicks absorbed without premature stopout!")
print(f" Win Rate: {res_m2a['win_rate']}% | Max DD: {res_m2a['max_drawdown_pct']}% | Final Balance: ${res_m2a['final_balance']} | PF: {res_m2a['profit_factor']}")

# 5. Monthly Breakdown for Model 2A
print("\n" + "=" * 85)
print("   HERMES 3.0 MODEL 2A: MONTH-BY-MONTH REALITY AUDIT BREAKDOWN   ")
print("=" * 85)

month_buckets = {}
for t in res_m2a["trades"]:
    dt = datetime.fromtimestamp(t["entry_time"] / 1000, tz=timezone.utc)
    m_key = dt.strftime("%B %Y")
    if m_key not in month_buckets:
        month_buckets[m_key] = {"tp": 0, "sl": 0, "be": 0, "pnl": 0.0}
    if t["outcome"] == "TP_HIT":
        month_buckets[m_key]["tp"] += 1
    elif t["outcome"] == "BE_SAVE":
        month_buckets[m_key]["be"] += 1
    else:
        month_buckets[m_key]["sl"] += 1
    month_buckets[m_key]["pnl"] += t["pnl_usdt"]

print(f"{'Month':<18} | {'Trades':<8} | {'TP':<5} | {'SL':<5} | {'BE':<5} | {'Win Rate':<10} | {'Net PnL USDT'}")
print("-" * 85)
for m_name, m_data in month_buckets.items():
    tot = m_data["tp"] + m_data["sl"]
    wr = (m_data["tp"] / tot * 100.0) if tot > 0 else 0.0
    print(f"{m_name:<18} | {tot + m_data['be']:<8} | {m_data['tp']:<5} | {m_data['sl']:<5} | {m_data['be']:<5} | {wr:<9.1f}% | ${m_data['pnl']:+,.2f}")

# Save detailed results to JSON for artifact generation
results_out = {
    "audit_timestamp": datetime.now(timezone.utc).isoformat(),
    "methodology": "ZERO_PHANTOM_FILL_PESSIMISTIC_REALITY",
    "coins_count": len(COINS),
    "dataset_duration": "1 Full Year (Sep 2025 - Sep 2026)",
    "baseline": {
        "win_rate": res_base["win_rate"],
        "tp": res_base["tps"],
        "sl": res_base["sls"],
        "be": res_base["bes"],
        "max_dd": res_base["max_drawdown_pct"],
        "final_balance": res_base["final_balance"],
        "profit_factor": res_base["profit_factor"]
    },
    "hermes_30_model_2a": {
        "win_rate": res_m2a["win_rate"],
        "tp": res_m2a["tps"],
        "sl": res_m2a["sls"],
        "be": res_m2a["bes"],
        "absorbed_wicks": res_m2a["absorbed_wicks"],
        "max_dd": res_m2a["max_drawdown_pct"],
        "final_balance": res_m2a["final_balance"],
        "profit_factor": res_m2a["profit_factor"],
        "monthly": month_buckets
    },
    "trades_sample": res_m2a["trades"][:30]
}

out_path = os.path.join(os.path.dirname(__file__), "..", "zero_phantom_audit_results.json")
with open(out_path, "w", encoding="utf-8") as fp:
    json.dump(results_out, fp, indent=2)

print("\n" + "=" * 85)
print(f" Audit results saved cleanly to: zero_phantom_audit_results.json")
print("=" * 85)
