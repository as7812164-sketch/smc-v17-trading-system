import os
import sys
import json
import urllib.request
import math
from engine.quant_microstructure_math import compute_hurst_exponent, compute_taker_delta_metrics

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TOP_ASSETS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "ENAUSDT", "SUIUSDT", "NEARUSDT", "AVAXUSDT", "FETUSDT", "1000PEPEUSDT"]

def fetch_futures_klines(symbol: str, limit: int = 1500):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=15m&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = json.loads(urllib.request.urlopen(req).read())
    candles = []
    for k in raw:
        candles.append({
            "t": k[0],
            "o": float(k[1]),
            "h": float(k[2]),
            "l": float(k[3]),
            "c": float(k[4]),
            "vol": float(k[5]),
            "taker_buy_vol": float(k[9]),
            "trades": int(k[8])
        })
    return candles

def run_battle():
    print("================================================================================")
    print("🔬 RUNNING LIVE INSTITUTIONAL QUANT ENGINE BATTLE ON BINANCE FUTURES DATA")
    print(f"Testing across {len(TOP_ASSETS)} Top Crypto Assets with exact Taker Volume Delta")
    print("================================================================================")

    models = {
        "RETAIL_TEXTBOOK_SMC": {
            "name": "Retail Textbook SMC (Normal OB + FVG, Blind Entry)",
            "trades": 0, "wins": 0, "losses": 0, "be_cuts": 0, "win_rate": 0.0,
            "gross_profit": 0.0, "gross_loss": 0.0, "profit_factor": 0.0, "pnl_roe": 0.0
        },
        "HERMES_3.5_BASELINE": {
            "name": "Hermes 3.5 Baseline (18% Wick + 50% MT Harvest)",
            "trades": 0, "wins": 0, "losses": 0, "be_cuts": 0, "win_rate": 0.0,
            "gross_profit": 0.0, "gross_loss": 0.0, "profit_factor": 0.0, "pnl_roe": 0.0
        },
        "PROPRIETARY_QUANT_MICROSTRUCTURE": {
            "name": "Proprietary Quant Engine (Hurst Noise Gate + Taker Delta Absorption + Discount + Asymmetric Squeeze)",
            "trades": 0, "wins": 0, "losses": 0, "be_cuts": 0, "win_rate": 0.0,
            "gross_profit": 0.0, "gross_loss": 0.0, "profit_factor": 0.0, "pnl_roe": 0.0,
            "random_walk_vetoes": 0, "falling_knives_vetoed": 0
        }
    }

    for sym in TOP_ASSETS:
        try:
            print(f"Fetching {sym} live 15m futures klines...")
            candles = fetch_futures_klines(sym, limit=1500)
        except Exception as e:
            print(f"Error fetching {sym}: {e}")
            continue

        n = len(candles)
        if n < 100: continue

        closes = [c["c"] for c in candles]

        # Scan for structural points
        for i in range(50, n - 40):
            c3 = candles[i]
            c2 = candles[i+1]
            c1 = candles[i+2]

            imp_h = max(c1["h"], c2["h"])
            is_red = c3["c"] < c3["o"]
            fvg = c1["l"] > c3["h"]
            disp = (imp_h - c3["l"]) / c3["l"] if c3["l"] > 0 else 0.0

            if not (is_red and fvg and disp >= 0.025):
                continue

            ob_high = c3["h"]
            ob_low = c3["l"]
            ob_range = ob_high - ob_low
            boundary_5pct = ob_high - (0.05 * ob_range)
            mt_50 = (ob_high + ob_low) / 2.0

            # Find tap forward
            tap_idx = -1
            for k in range(i + 3, min(i + 120, n)):
                if candles[k]["c"] < ob_low: break
                if candles[k]["l"] <= boundary_5pct:
                    tap_idx = k
                    break

            if tap_idx == -1: continue

            tap_c = candles[tap_idx]

            # -------------------------------------------------------------
            # MODEL 1: RETAIL TEXTBOOK SMC (Blind limit order at OB high/50%)
            # -------------------------------------------------------------
            m1_entry = mt_50
            m1_sl = ob_low * 0.995 # Tight stop below OB
            m1_tp = m1_entry * 1.020 # 1:1.5 RR target
            m1_won = False; m1_lost = False
            for s in range(tap_idx + 1, min(tap_idx + 100, n)):
                sc = candles[s]
                if sc["h"] >= m1_tp: m1_won = True; break
                if sc["l"] <= m1_sl: m1_lost = True; break
            
            res1 = models["RETAIL_TEXTBOOK_SMC"]
            res1["trades"] += 1
            if m1_won:
                res1["wins"] += 1
                gain = 0.020 * 5.0
                res1["gross_profit"] += gain
                res1["pnl_roe"] += gain
            elif m1_lost:
                res1["losses"] += 1
                loss = ((m1_entry - m1_sl) / m1_entry) * 5.0
                res1["gross_loss"] += loss
                res1["pnl_roe"] -= loss

            # -------------------------------------------------------------
            # MODEL 2: HERMES 3.5 BASELINE (18% Wick + 50% MT Harvest)
            # -------------------------------------------------------------
            c_rng = tap_c["h"] - tap_c["l"]
            l_wick = min(tap_c["o"], tap_c["c"]) - tap_c["l"]
            wick_ratio = (l_wick / c_rng) if c_rng > 0 else 0.0
            is_green = tap_c["c"] >= tap_c["o"]
            h35_pass = (wick_ratio >= 0.15 or is_green) and (tap_c["c"] >= mt_50)

            if h35_pass:
                m2_entry = boundary_5pct
                m2_tp = m2_entry * 1.020
                m2_sl = m2_entry * 0.975
                m2_be = m2_entry * 1.012
                be_act = False; m2_won = False; m2_lost = False
                for s in range(tap_idx + 1, min(tap_idx + 100, n)):
                    sc = candles[s]
                    if sc["h"] >= m2_be: be_act = True
                    if sc["h"] >= m2_tp: m2_won = True; break
                    if be_act and sc["l"] <= m2_entry * 1.001: break
                    if sc["l"] <= m2_sl: m2_lost = True; break
                
                res2 = models["HERMES_3.5_BASELINE"]
                res2["trades"] += 1
                if m2_won:
                    res2["wins"] += 1
                    gain = 0.020 * 5.0
                    res2["gross_profit"] += gain
                    res2["pnl_roe"] += gain
                elif m2_lost:
                    res2["losses"] += 1
                    loss = 0.025 * 5.0
                    res2["gross_loss"] += loss
                    res2["pnl_roe"] -= loss
                else:
                    res2["be_cuts"] += 1

            # -------------------------------------------------------------
            # MODEL 3: PROPRIETARY QUANT ENGINE
            # -------------------------------------------------------------
            # 1. Hurst Exponent Regime Gate (Check past 60 candles)
            hist_prices = closes[max(0, tap_idx - 60):tap_idx]
            hurst_val = compute_hurst_exponent(hist_prices)
            
            # Noise Veto: If Hurst in [0.47, 0.53], market is pure random noise Brownian walk!
            is_random_noise = (0.47 <= hurst_val <= 0.53)
            if is_random_noise:
                models["PROPRIETARY_QUANT_MICROSTRUCTURE"]["random_walk_vetoes"] += 1
                continue # HARD VETO - ZERO CHOP TRADING!

            # 2. 50% Equilibrium Discount Filter (Prior 40 bars)
            p_high = max(c["h"] for c in candles[max(0, tap_idx - 40):tap_idx])
            p_low = min(c["l"] for c in candles[max(0, tap_idx - 40):tap_idx])
            eq_50 = (p_high + p_low) / 2.0
            if tap_c["l"] > eq_50:
                continue # DO NOT BUY IN PREMIUM!

            # 3. Taker Volume Delta Absorption Gate
            delta_info = compute_taker_delta_metrics(tap_c["taker_buy_vol"], tap_c["vol"])
            # Require Absorption: Either positive delta ratio OR wick >= 18% with seller exhaustion
            has_absorption = (delta_info["delta_ratio"] >= 0.50) or (wick_ratio >= 0.18 and delta_info["delta_ratio"] >= 0.44)
            if not has_absorption:
                models["PROPRIETARY_QUANT_MICROSTRUCTURE"]["falling_knives_vetoed"] += 1
                continue # VETO - Aggressive selling without limit absorption!

            # 4. Asymmetric Squeeze Execution:
            # Micro-SL under reaction wick + 1:2.5 Asymmetric Target
            m3_entry = boundary_5pct
            m3_sl = min(ob_low, tap_c["l"]) * 0.997
            risk_dist = m3_entry - m3_sl
            if risk_dist <= 0 or (risk_dist / m3_entry) > 0.030:
                risk_dist = m3_entry * 0.018
                m3_sl = m3_entry * 0.982
            
            m3_tp = m3_entry + (2.5 * risk_dist) # 1:2.5 Asymmetric Squeeze Target
            m3_be = m3_entry + (1.2 * risk_dist)
            
            be_act = False; m3_won = False; m3_lost = False
            for s in range(tap_idx + 1, min(tap_idx + 120, n)):
                sc = candles[s]
                if sc["h"] >= m3_be: be_act = True
                if sc["h"] >= m3_tp: m3_won = True; break
                if be_act and sc["l"] <= m3_entry * 1.001: break
                if sc["l"] <= m3_sl: m3_lost = True; break
                
            res3 = models["PROPRIETARY_QUANT_MICROSTRUCTURE"]
            res3["trades"] += 1
            if m3_won:
                res3["wins"] += 1
                gain = ((m3_tp - m3_entry) / m3_entry) * 5.0
                res3["gross_profit"] += gain
                res3["pnl_roe"] += gain
            elif m3_lost:
                res3["losses"] += 1
                loss = (risk_dist / m3_entry) * 5.0
                res3["gross_loss"] += loss
                res3["pnl_roe"] -= loss
            else:
                res3["be_cuts"] += 1

    # Summarize
    for k in models:
        m = models[k]
        decided = m["wins"] + m["losses"]
        m["win_rate"] = round((m["wins"] / decided * 100.0), 2) if decided > 0 else 0.0
        m["profit_factor"] = round((m["gross_profit"] / m["gross_loss"]), 2) if m["gross_loss"] > 0 else 99.0
        m["pnl_roe"] = round(m["pnl_roe"] * 100.0, 2)
        m["gross_profit"] = round(m["gross_profit"] * 100.0, 2)
        m["gross_loss"] = round(m["gross_loss"] * 100.0, 2)

    print("\n========================= QUANT BATTLE AUDIT RESULTS =========================")
    print(json.dumps(models, indent=2))

if __name__ == "__main__":
    run_battle()
