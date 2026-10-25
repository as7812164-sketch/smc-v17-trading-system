import urllib.request
import json
import time
import sys
import numpy as np
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT",
    "SUIUSDT", "AVAXUSDT", "UNIUSDT", "NEARUSDT", "ARBUSDT",
    "APTUSDT", "LTCUSDT", "LINKUSDT", "ADAUSDT", "XRPUSDT"
]

def fetch_4h_candles_and_oi(symbol):
    """Fetches 1000 4H candles (~5.5 months) and aligned 4H Open Interest data."""
    # 1. Klines
    url_k = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval=4h&limit=1000"
    candles = []
    running_cvd = 0.0
    try:
        req = urllib.request.Request(url_k, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
            for k in data:
                vol = float(k[5])
                taker_buy = float(k[9]) if len(k) > 9 else vol * 0.5
                taker_sell = max(0.0, vol - taker_buy)
                delta = taker_buy - taker_sell
                running_cvd += delta
                candles.append({
                    "time": int(k[0]),
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": vol,
                    "taker_buy": taker_buy,
                    "taker_sell": taker_sell,
                    "delta": delta,
                    "cvd": running_cvd
                })
    except Exception as e:
        print(f"Error klines {symbol}: {e}", flush=True)

    # 2. Historical Open Interest (4H)
    url_oi = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={symbol}&period=4h&limit=500"
    oi_map = {}
    try:
        req_oi = urllib.request.Request(url_oi, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_oi, timeout=12) as resp:
            oi_data = json.loads(resp.read().decode())
            for item in oi_data:
                ts = int(item["timestamp"])
                oi_val = float(item["sumOpenInterest"])
                oi_map[ts] = oi_val
    except Exception:
        pass

    return symbol, candles, oi_map

def run_true_4h_backtest():
    print("=" * 95)
    print("   TRUE 4H AUDIT: STRICT 3-OB MIDDLE SETUP + FULL SUPER SNIPER (DELTA + CVD + OI)")
    print("=" * 95)
    print("   Target TP:  +11.00% ROE (+2.20% price move @ 5x leverage)")
    print("   Breakeven:  +5.50% ROE  (+1.10% price move lock)")
    print("   Soft SL:    -12.50% ROE (-2.50% price move on Candle Close)")
    print("   Capital:    $50.00 USDT Initial Compounding")
    print("=" * 95)

    all_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fetch_4h_candles_and_oi, s) for s in SYMBOLS]
        for f in concurrent.futures.as_completed(futures):
            sym, c, oi_map = f.result()
            all_data[sym] = (c, oi_map)
            days = (c[-1]["time"] - c[0]["time"]) / (86400 * 1000) if c else 0
            print(f"  ✓ {sym:<10}: {len(c)} candles ({days:.1f} days / {days/30:.1f} months) | OI: {len(oi_map)} pts", flush=True)

    # True 4H Parameters (5x Leverage)
    tp_pct = 0.022     # +2.20% price move = +11.00% ROE
    be_pct = 0.011     # +1.10% price move = +5.50% ROE
    sl_pct = 0.025     # -2.50% price move = -12.50% ROE

    trades = []

    # Detect exact 3-OB Middle setups on 4H
    for sym, (candles, oi_map) in all_data.items():
        if len(candles) < 80:
            continue

        # Maintain list of qualified unmitigated OBs
        # An OB is formed on a bearish candle before >= 4.0% expansion
        detected_obs = []
        for i in range(10, len(candles) - 15):
            c = candles[i]
            if c["close"] >= c["open"]:
                continue
            ob_high = c["high"]
            ob_low = c["low"]

            # Must expand >= 4.0%
            max_exp = 0.0
            for k in range(1, min(8, len(candles) - i)):
                exp = (candles[i+k]["high"] - ob_high) / ob_high
                if exp > max_exp:
                    max_exp = exp
            if max_exp < 0.040:
                continue

            detected_obs.append({
                "bar_idx": i,
                "time": c["time"],
                "ob_high": ob_high,
                "ob_low": ob_low,
                "mitigated": False
            })

        # Now simulate price moving forward and finding First Tap on the MIDDLE 2nd OB
        for bar_idx in range(40, len(candles) - 15):
            curr_bar = candles[bar_idx]
            
            # Find active unmitigated OBs formed before this bar
            active_obs = [ob for ob in detected_obs if ob["bar_idx"] < bar_idx - 2 and not ob["mitigated"]]
            if len(active_obs) < 3:
                continue

            # Sort active OBs by price: Top #1 -> Middle #2 -> Bottom #3
            active_obs.sort(key=lambda x: x["ob_high"], reverse=True)
            middle_ob = active_obs[1] # Index 1 is strictly the MIDDLE / SANDWICH 2nd OB

            entry_p = middle_ob["ob_high"]

            # Check if this bar makes the FIRST TAP into the middle OB
            if curr_bar["low"] <= entry_p and curr_bar["open"] > entry_p:
                # First Tap Occurred! Mark middle OB as mitigated so it doesn't trigger again
                middle_ob["mitigated"] = True

                # --- SUPER SNIPER ORDER FLOW GATE (DELTA + CVD + OI) ---
                # 1. Delta Absorption
                d_ratio = curr_bar["taker_buy"] / curr_bar["volume"] if curr_bar["volume"] > 0 else 0.50
                # 2. CVD Momentum
                cvd_prev = candles[bar_idx - 2]["cvd"] if bar_idx >= 2 else candles[0]["cvd"]
                cvd_reversal = (curr_bar["cvd"] - cvd_prev) > 0
                # 3. Open Interest change (4H lookback)
                t_now = curr_bar["time"]
                oi_curr = oi_map.get(t_now, 0.0)
                oi_prev = oi_map.get(t_now - 14400000, 0.0)
                oi_chg = ((oi_curr - oi_prev) / oi_prev * 100) if (oi_prev > 0 and oi_curr > 0) else 0.0

                # Super Sniper Verification:
                # Taker Buy >= 51%, CVD turning up, and OI not in collapse (oi_chg >= -0.5%)
                is_sniper = (d_ratio >= 0.51) and cvd_reversal and (oi_chg >= -0.5)

                # Simulate Forward Trade Outcome (Starting STRICTLY from NEXT candle bar_idx + 1 to eliminate lookahead bias!)
                tp_target = entry_p * (1.0 + tp_pct)
                be_target = entry_p * (1.0 + be_pct)
                sl_target = entry_p * (1.0 - sl_pct)

                trade_res = None
                be_active = False
                bars_held = 0

                for m in range(bar_idx + 1, min(bar_idx + 40, len(candles))):
                    f_bar = candles[m]
                    bars_held += 1

                    # Check BE Trigger (+1.10% move)
                    if not be_active and f_bar["high"] >= be_target:
                        be_active = True

                    # Check TP Hit (+2.20% move = +11.0% ROE)
                    if f_bar["high"] >= tp_target:
                        trade_res = "WIN"
                        break

                    # Check Breakeven Stop Hit ($0 loss)
                    if be_active and f_bar["low"] <= entry_p:
                        trade_res = "BREAKEVEN"
                        break

                    # Check Soft Candle Close SL (-2.50% move = -12.5% ROE)
                    if f_bar["close"] <= sl_target:
                        trade_res = "LOSS"
                        break

                if not trade_res:
                    trade_res = "BREAKEVEN" if be_active else "LOSS"

                trades.append({
                    "symbol": sym,
                    "entry_time": t_now,
                    "entry_price": entry_p,
                    "result": trade_res,
                    "is_sniper": is_sniper,
                    "bars_held": bars_held,
                    "hours_held": bars_held * 4,
                    "delta_ratio": d_ratio,
                    "cvd_reversal": cvd_reversal,
                    "oi_chg": oi_chg
                })

    trades.sort(key=lambda x: x["entry_time"])

    # Separate Baseline vs Super Sniper
    baseline_trades = trades
    sniper_trades = [t for t in trades if t["is_sniper"]]

    def print_summary(t_list, label):
        if not t_list:
            print(f"\n{label}: No trades captured.")
            return
        total = len(t_list)
        wins = sum(1 for t in t_list if t["result"] == "WIN")
        bes = sum(1 for t in t_list if t["result"] == "BREAKEVEN")
        losses = sum(1 for t in t_list if t["result"] == "LOSS")

        wr = wins / total * 100
        be_rate = bes / total * 100
        loss_rate = losses / total * 100
        safety = (wins + bes) / total * 100
        avg_h = np.mean([t["hours_held"] for t in t_list if t["result"] == "WIN"]) if wins > 0 else 0

        # Compounding $50 with 4H params: Win = +11.0% ROE, Loss = -12.5% ROE
        cap = 50.0
        peak = 50.0
        max_dd = 0.0
        for t in t_list:
            if t["result"] == "WIN":
                cap += cap * 0.11 # +11.0% ROE
            elif t["result"] == "LOSS":
                cap -= cap * 0.125 # -12.5% ROE
            if cap > peak:
                peak = cap
            dd = (peak - cap) / peak * 100
            if dd > max_dd:
                max_dd = dd

        print(f"\n--- {label} (Total Setups: {total}) ---")
        print(f"  🏆 Direct Win Rate (TP +11% ROE): {wr:.2f}%  ({wins}/{total})")
        print(f"  🛡️ Breakeven Rate ($0 Loss):     {be_rate:.2f}%  ({bes}/{total})")
        print(f"  ❌ Loss Rate (SL -12.5% ROE):     {loss_rate:.2f}%  ({losses}/{total})")
        print(f"  💎 Total Capital Safety:          {safety:.2f}%  (Win + Breakeven)")
        print(f"  ⚡ Average Duration to TP:        {avg_h:.1f} Hours ({avg_h/4:.1f} Candles)")
        print(f"  💰 $50 Compounded Final Balance:   ${cap:,.2f} USDT")
        print(f"  📈 Net Profit Return:             +{((cap-50)/50)*100:,.1f}%")
        print(f"  🛡️ Maximum Drawdown:              {max_dd:.2f}%")

    print("\n" + "=" * 95)
    print("                     4H SCIENTIFIC AUDIT RESULTS (STRICT RULES)")
    print("=" * 95)
    print_summary(baseline_trades, "1. ALL 3-OB MIDDLE SETUPS (Bina Order Flow Filter)")
    print_summary(sniper_trades, "2. SUPER SNIPER 3-OB MIDDLE SETUPS (Delta + CVD + OI Confirmed)")

if __name__ == "__main__":
    run_true_4h_backtest()
