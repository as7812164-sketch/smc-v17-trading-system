import os
import json
import glob
from datetime import datetime, timezone, timedelta
import csv

IST = timezone(timedelta(hours=5, minutes=30))
CACHE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\market_data_cache"

class EliteSniperCompounding:
    def __init__(self, initial_capital=50.0, leverage=5.0):
        self.initial_capital = initial_capital
        self.leverage = leverage
        self.fee_rate = 0.0005 # 0.05% fee

    def load_candles(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        candles = []
        for row in data:
            if isinstance(row, list):
                candles.append({
                    "time": int(row[0]),
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5])
                })
            elif isinstance(row, dict):
                candles.append(row)
        return candles

    def run_backtest_symbol(self, symbol, timeframe, candles, btc_candles=None):
        n = len(candles)
        if n < 40:
            return []

        is_4h = (timeframe == "4h")
        airspace_min = 2.8 if is_4h else 1.8
        qual_pct = 0.025 if is_4h else 0.018
        tp_pct = 0.0240 if is_4h else 0.0160   # +12% ROE 4H / +8% ROE 1H
        ssl_pct = 0.0225 if is_4h else 0.0200  # Soft SL
        hsl_pct = 0.0320                       # Hard SL
        be_trig_pct = 0.0105 if is_4h else 0.0075
        fee_buf_pct = 0.0010

        trades = []
        active_obs = []

        for idx in range(20, n):
            c = candles[idx]
            c_prev = candles[idx - 1]
            bodies = [abs(candles[k]["close"] - candles[k]["open"]) for k in range(idx - 10, idx)]
            avg_body = sum(bodies) / len(bodies) if bodies else 0.0
            c_body = abs(c["close"] - c["open"])
            
            # True Displacement
            is_disp = avg_body > 0 and (c_body >= 1.35 * avg_body) and (c["close"] > c["open"]) and (c["close"] > c_prev["high"])

            if is_disp:
                origin_idx = -1
                for k in range(1, 10):
                    if idx - k >= 0 and candles[idx - k]["close"] < candles[idx - k]["open"]:
                        origin_idx = idx - k
                        break
                if origin_idx == -1:
                    lowest_p = 1e10
                    for k in range(1, 10):
                        if idx - k >= 0 and candles[idx - k]["low"] < lowest_p:
                            lowest_p = candles[idx - k]["low"]
                            origin_idx = idx - k

                if origin_idx != -1:
                    o_c = candles[origin_idx]
                    o_high = o_c["high"]
                    o_low = o_c["low"]
                    
                    if not any(ob["origin_idx"] == origin_idx for ob in active_obs):
                        # 1. Inducement (IDM) Check
                        idm_swept = False
                        if origin_idx >= 4:
                            prev_lows = [candles[p]["low"] for p in range(max(0, origin_idx - 6), origin_idx)]
                            if prev_lows and o_low < min(prev_lows):
                                idm_swept = True

                        # 2. Bullish FVG
                        has_fvg = (c["low"] > candles[idx - 2]["high"]) if idx >= 2 else False

                        # 3. Macro Range Discount Check: dealing range from origin to displacement high
                        dealing_high = max(c["high"], candles[idx-1]["high"])
                        equilibrium = (dealing_high + o_low) / 2.0
                        is_in_discount = (o_high <= equilibrium) # Entry point sits below 50%

                        # 4. Instant Bar-0 Qualification
                        is_qual = dealing_high >= o_high * (1.0 + qual_pct)

                        active_obs.append({
                            "origin_idx": origin_idx,
                            "disp_idx": idx,
                            "top": o_high,
                            "bottom": o_low,
                            "entry_p": o_high * 1.0005,
                            "tp_p": o_high * 1.0005 * (1.0 + tp_pct),
                            "ssl_p": o_high * 1.0005 * (1.0 - ssl_pct),
                            "hsl_p": o_high * 1.0005 * (1.0 - hsl_pct),
                            "bet_p": o_high * 1.0005 * (1.0 + be_trig_pct),
                            "fee_be_p": o_high * 1.0005 * (1.0 + fee_buf_pct),
                            "target_qual": o_high * (1.0 + qual_pct),
                            "is_qualified": is_qual,
                            "idm_swept": idm_swept,
                            "has_fvg": has_fvg,
                            "is_in_discount": is_in_discount,
                            "status": "QUALIFIED" if is_qual else "PENDING",
                            "be_active": False
                        })

            # Update lifecycle
            valid_obs = []
            for ob in active_obs:
                if ob["status"] == "PENDING":
                    if c["low"] <= ob["bottom"]:
                        continue
                    elif c["high"] >= ob["target_qual"]:
                        ob["is_qualified"] = True
                        ob["status"] = "QUALIFIED"
                        valid_obs.append(ob)
                    else:
                        valid_obs.append(ob)
                else:
                    valid_obs.append(ob)
            active_obs = valid_obs

            # Sort active qualified OBs descending by price
            qual_obs = [ob for ob in active_obs if ob["status"] == "QUALIFIED"]
            qual_obs.sort(key=lambda x: x["top"], reverse=True)

            trade_candidate = None
            if len(qual_obs) >= 3:
                top_ob = qual_obs[0]
                mid_ob = qual_obs[1]
                bot_ob = qual_obs[2]
                if top_ob["top"] > mid_ob["top"] and mid_ob["top"] > bot_ob["top"]:
                    airspace = (top_ob["bottom"] - mid_ob["entry_p"]) / mid_ob["entry_p"] * 100.0
                    # Strict Filter: Airspace >= min AND (IDM swept OR FVG launchpad)
                    if airspace >= airspace_min and (mid_ob["idm_swept"] or mid_ob["has_fvg"]):
                        mid_ob["mode"] = "MODE_A_3OB"
                        mid_ob["airspace"] = airspace
                        trade_candidate = mid_ob
            elif len(qual_obs) == 2:
                top_ob = qual_obs[0]
                mid_ob = qual_obs[1]
                if top_ob["top"] > mid_ob["top"]:
                    airspace = (top_ob["bottom"] - mid_ob["entry_p"]) / mid_ob["entry_p"] * 100.0
                    # Strict Mode B: Requires BOTH Airspace AND IDM swept
                    if airspace >= airspace_min and mid_ob["idm_swept"] and mid_ob["is_in_discount"]:
                        mid_ob["mode"] = "MODE_B_2OB_EXP"
                        mid_ob["airspace"] = airspace
                        trade_candidate = mid_ob

            # First tap entry check
            if trade_candidate and trade_candidate["status"] == "QUALIFIED":
                if c_prev["close"] > trade_candidate["top"] and c["low"] <= trade_candidate["entry_p"]:
                    # Rejection Wick Filter: Candle must not be a pure falling knife
                    candle_range = c["high"] - c["low"]
                    lower_wick = min(c["open"], c["close"]) - c["low"]
                    wick_ratio = (lower_wick / candle_range) if candle_range > 0 else 0.0

                    # King Bitcoin Shield
                    btc_dump = False
                    if btc_candles and symbol != "BTCUSDT":
                        c_time = c["time"]
                        btc_match = next((bc for bc in btc_candles if abs(bc["time"] - c_time) <= 3600000), None)
                        if btc_match:
                            btc_ret = (btc_match["close"] - btc_match["open"]) / btc_match["open"]
                            if btc_ret <= -0.015:
                                btc_dump = True

                    # Only enter if not BTC dump and has rejection absorption
                    if not btc_dump and wick_ratio >= 0.18:
                        entry_price = trade_candidate["entry_p"]
                        trade_candidate["status"] = "ACTIVE"
                        
                        exit_price = None
                        exit_time = None
                        exit_reason = None
                        be_active = False

                        for fwd_idx in range(idx, min(n, idx + 48)):
                            fc = candles[fwd_idx]
                            
                            if fc["low"] <= trade_candidate["hsl_p"]:
                                exit_price = trade_candidate["hsl_p"]
                                exit_time = fc["time"]
                                exit_reason = "HARD_SL"
                                break
                            
                            if not be_active and fc["high"] >= trade_candidate["bet_p"]:
                                be_active = True
                                
                            if fc["high"] >= trade_candidate["tp_p"]:
                                exit_price = trade_candidate["tp_p"]
                                exit_time = fc["time"]
                                exit_reason = "TP_HIT"
                                break
                                
                            if be_active and fc["low"] <= trade_candidate["fee_be_p"]:
                                exit_price = trade_candidate["fee_be_p"]
                                exit_time = fc["time"]
                                exit_reason = "FEE_SHIELD_BE"
                                break
                                
                            if not be_active and fc["close"] <= trade_candidate["ssl_p"]:
                                exit_price = fc["close"]
                                exit_time = fc["time"]
                                exit_reason = "SOFT_SL"
                                break

                        if not exit_reason:
                            last_c = candles[min(n - 1, idx + 47)]
                            exit_price = last_c["close"]
                            exit_time = last_c["time"]
                            exit_reason = "TIME_CLOSE"

                        price_return = (exit_price - entry_price) / entry_price
                        gross_pnl = price_return * self.leverage
                        fee_drag = 2 * (self.fee_rate * self.leverage)
                        net_roe = gross_pnl - fee_drag

                        is_win = (exit_reason == "TP_HIT")
                        is_be = (exit_reason == "FEE_SHIELD_BE") or (abs(net_roe) < 0.005)
                        is_loss = (exit_reason in ["HARD_SL", "SOFT_SL"]) and not is_be

                        trades.append({
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "mode": trade_candidate["mode"],
                            "airspace": round(trade_candidate["airspace"], 2),
                            "entry_time": datetime.fromtimestamp(c["time"] / 1000, tz=IST).strftime("%Y-%m-%d %H:%M"),
                            "exit_time": datetime.fromtimestamp(exit_time / 1000, tz=IST).strftime("%Y-%m-%d %H:%M"),
                            "entry_price": round(entry_price, 5),
                            "exit_price": round(exit_price, 5),
                            "exit_reason": exit_reason,
                            "net_roe_pct": round(net_roe * 100, 2),
                            "is_win": is_win,
                            "is_be": is_be,
                            "is_loss": is_loss
                        })
                        active_obs.remove(trade_candidate)

        return trades

    def run_portfolio(self, pairs):
        btc_file_1h = os.path.join(CACHE_DIR, "BTCUSDT_1h.json")
        btc_candles = self.load_candles(btc_file_1h) if os.path.exists(btc_file_1h) else None

        all_trades = []
        for sym in pairs:
            for tf in ["1h", "4h"]:
                fpath = os.path.join(CACHE_DIR, f"{sym}_{tf}.json")
                if os.path.exists(fpath):
                    c = self.load_candles(fpath)
                    all_trades.extend(self.run_backtest_symbol(sym, tf, c, btc_candles))

        all_trades.sort(key=lambda x: x["entry_time"])

        balance = self.initial_capital
        peak = balance
        max_dd = 0.0
        ledger = []
        wins, losses, bes = 0, 0, 0
        gross_profit, gross_loss = 0.0, 0.0

        for idx, t in enumerate(all_trades):
            start_bal = balance
            pnl_usd = start_bal * (t["net_roe_pct"] / 100.0)
            balance += pnl_usd
            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak * 100.0
            if dd > max_dd:
                max_dd = dd

            if t["is_win"]:
                wins += 1
                gross_profit += pnl_usd
            elif t["is_be"]:
                bes += 1
            else:
                losses += 1
                gross_loss += abs(pnl_usd)

            rec = dict(t)
            rec["trade_num"] = idx + 1
            rec["start_balance"] = round(start_bal, 2)
            rec["pnl_usd"] = round(pnl_usd, 2)
            rec["end_balance"] = round(balance, 2)
            rec["drawdown_pct"] = round(dd, 2)
            ledger.append(rec)

        tot = len(all_trades)
        wr = (wins / tot * 100.0) if tot > 0 else 0.0
        lr = (losses / tot * 100.0) if tot > 0 else 0.0
        br = (bes / tot * 100.0) if tot > 0 else 0.0
        pf = (gross_profit / gross_loss) if gross_loss > 0 else 999.0

        return {
            "initial_capital": self.initial_capital,
            "final_balance": round(balance, 2),
            "total_trades": tot,
            "wins": wins,
            "losses": losses,
            "breakevens": bes,
            "win_rate_pct": round(wr, 2),
            "loss_rate_pct": round(lr, 2),
            "be_rate_pct": round(br, 2),
            "capital_safety_pct": round(100.0 - lr, 2),
            "profit_factor": round(pf, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "total_pnl_pct": round((balance - self.initial_capital) / self.initial_capital * 100.0, 2),
            "ledger": ledger
        }

if __name__ == "__main__":
    sniper = EliteSniperCompounding(initial_capital=50.0, leverage=5.0)
    cache_files = glob.glob(os.path.join(CACHE_DIR, "*_1h.json"))
    pairs = [os.path.basename(f).replace("_1h.json", "") for f in cache_files]
    res = sniper.run_portfolio(pairs)

    print("\n=======================================================")
    print("ELITE SNIPER (SMC + ICT + LIQUIDITY + WICK ABSORPTION)")
    print("=======================================================")
    print(f"Starting Capital:     ${res['initial_capital']:.2f}")
    print(f"Final Balance:        ${res['final_balance']:.2f}")
    print(f"Total Trades:         {res['total_trades']}")
    print(f"Wins / Losses / BEs:  {res['wins']} Wins | {res['losses']} Losses | {res['breakevens']} Breakevens")
    print(f"Win Rate:             {res['win_rate_pct']}%")
    print(f"Loss Rate:            {res['loss_rate_pct']}%")
    print(f"Breakeven Rate:       {res['be_rate_pct']}%")
    print(f"Capital Safety:       {res['capital_safety_pct']}%")
    print(f"Profit Factor:        {res['profit_factor']}")
    print(f"Max Drawdown:         {res['max_drawdown_pct']}%")
    print(f"Total Net Growth:     +{res['total_pnl_pct']}%")
    print("=======================================================\n")

    # 100 trade milestone
    l100 = res["ledger"][:100]
    if l100:
        w100 = sum(1 for x in l100 if x["is_win"])
        loss100 = sum(1 for x in l100 if x["is_loss"])
        be100 = sum(1 for x in l100 if x["is_be"])
        bal100 = l100[-1]["end_balance"]
        dd100 = max(x["drawdown_pct"] for x in l100)
        print(f"--- FIRST 100 TRADES STATS ---")
        print(f"Balance after 100 Trades: ${bal100:.2f}")
        print(f"Wins: {w100} | Losses: {loss100} | BEs: {be100}")
        print(f"Win Rate: {(w100/len(l100))*100:.1f}%")
        print(f"Loss Rate: {(loss100/len(l100))*100:.1f}%")
        print(f"Capital Safety: {(1 - loss100/len(l100))*100:.1f}%")
        print(f"Max Drawdown: {dd100:.2f}%\n")

    # Export to json & csv
    with open("elite_sniper_compounding_result.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    if res["ledger"]:
        keys = list(res["ledger"][0].keys())
        with open("elite_sniper_compounding_ledger.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(res["ledger"])
    print("Exported elite_sniper_compounding_ledger.csv and elite_sniper_compounding_result.json successfully!")
