import os
import json
import glob
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

CACHE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\market_data_cache"

class GodTierSMCBacktester:
    def __init__(self, initial_capital: float = 50.0, leverage: float = 5.0):
        self.initial_capital = initial_capital
        self.leverage = leverage
        self.fee_rate = 0.0005  # 0.05% taker/maker fee
        
    def load_candles(self, filepath: str) -> List[Dict[str, Any]]:
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

    def find_pivots(self, candles: List[Dict[str, Any]], window: int = 4) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
        highs = []
        lows = []
        n = len(candles)
        for i in range(window, n - window):
            curr_h = candles[i]["high"]
            curr_l = candles[i]["low"]
            if all(curr_h >= candles[i - k]["high"] for k in range(1, window + 1)) and \
               all(curr_h >= candles[i + k]["high"] for k in range(1, window + 1)):
                highs.append((i, curr_h))
            if all(curr_l <= candles[i - k]["low"] for k in range(1, window + 1)) and \
               all(curr_l <= candles[i + k]["low"] for k in range(1, window + 1)):
                lows.append((i, curr_l))
        return highs, lows

    def run_backtest_symbol(self, symbol: str, timeframe: str, candles: List[Dict[str, Any]], btc_candles: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        n = len(candles)
        if n < 40:
            return []

        # Timeframe parameters
        is_4h = (timeframe == "4h")
        airspace_min = 2.8 if is_4h else 1.8   # Timeframe-Adaptive Airspace
        qual_pct = 0.025 if is_4h else 0.018   # Min Expansion
        tp_pct = 0.0240 if is_4h else 0.0160   # Target (+12% ROE on 4H, +8% ROE on 1H @ 5x)
        ssl_pct = 0.0225 if is_4h else 0.0200  # Soft SL (-11.25% on 4H, -10% on 1H)
        hsl_pct = 0.0320                       # Hard SL
        be_trig_pct = 0.0105 if is_4h else 0.0075 # Breakeven trigger
        fee_buf_pct = 0.0010                   # Fee-Shield Buffer (+0.10% for $0.00 net loss)

        trades = []
        active_obs = [] # list of unmitigated Order Blocks

        # Average candle body lookback
        for idx in range(15, n):
            c = candles[idx]
            c_prev = candles[idx - 1]
            bodies = [abs(candles[k]["close"] - candles[k]["open"]) for k in range(idx - 10, idx)]
            avg_body = sum(bodies) / len(bodies) if bodies else 0.0
            c_body = abs(c["close"] - c["open"])
            
            # Displacement check
            is_disp = avg_body > 0 and (c_body >= 1.3 * avg_body) and (c["close"] > c["open"]) and (c["close"] > c_prev["high"])

            # 1. New Order Block formation
            if is_disp:
                # Find origin red candle or accumulation base
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
                    
                    # Avoid duplicate origin
                    if not any(ob["origin_idx"] == origin_idx for ob in active_obs):
                        # Inducement (IDM) Check: was there a minor pullback low prior to origin that got swept?
                        idm_swept = False
                        if origin_idx >= 4:
                            prev_lows = [candles[p]["low"] for p in range(max(0, origin_idx - 6), origin_idx)]
                            if prev_lows and o_low < min(prev_lows):
                                idm_swept = True

                        # FVG Confluence Check: Low of current > High of 2 candles ago
                        has_fvg = (c["low"] > candles[idx - 2]["high"]) if idx >= 2 else False

                        # Instant Bar-0 Qualification
                        max_impulse = max(c["high"], candles[idx]["high"])
                        is_qual = max_impulse >= o_high * (1.0 + qual_pct)

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
                            "status": "QUALIFIED" if is_qual else "PENDING",
                            "be_active": False
                        })

            # 2. Update Lifecycle of Existing OBs
            # Filter out invalidated
            valid_obs = []
            for ob in active_obs:
                if ob["status"] == "PENDING":
                    if c["low"] <= ob["bottom"]:
                        continue # Invalidated
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

            # Check for Setup Formation (Mode A: 3-OB or Mode B: 2-OB)
            trade_candidate = None
            if len(qual_obs) >= 3:
                top_ob = qual_obs[0]
                mid_ob = qual_obs[1]
                bot_ob = qual_obs[2]
                if top_ob["top"] > mid_ob["top"] and mid_ob["top"] > bot_ob["top"]:
                    airspace = (top_ob["bottom"] - mid_ob["entry_p"]) / mid_ob["entry_p"] * 100.0
                    if airspace >= airspace_min:
                        mid_ob["mode"] = "MODE_A_3OB"
                        mid_ob["airspace"] = airspace
                        trade_candidate = mid_ob
            elif len(qual_obs) == 2:
                top_ob = qual_obs[0]
                mid_ob = qual_obs[1]
                if top_ob["top"] > mid_ob["top"]:
                    airspace = (top_ob["bottom"] - mid_ob["entry_p"]) / mid_ob["entry_p"] * 100.0
                    if airspace >= airspace_min and (mid_ob["idm_swept"] or mid_ob["has_fvg"]):
                        mid_ob["mode"] = "MODE_B_2OB_EXP"
                        mid_ob["airspace"] = airspace
                        trade_candidate = mid_ob

            # Check First Tap Execution on Trade Candidate
            if trade_candidate and trade_candidate["status"] == "QUALIFIED":
                # Price must come from above and tap entry
                if c_prev["close"] > trade_candidate["top"] and c["low"] <= trade_candidate["entry_p"]:
                    # King Bitcoin Shield: check if BTC is in macro dump
                    btc_dump = False
                    if btc_candles and symbol != "BTCUSDT":
                        c_time = c["time"]
                        btc_match = next((bc for bc in btc_candles if abs(bc["time"] - c_time) <= 3600000), None)
                        if btc_match:
                            btc_ret = (btc_match["close"] - btc_match["open"]) / btc_match["open"]
                            if btc_ret <= -0.018:
                                btc_dump = True

                    if not btc_dump:
                        # Enter Trade!
                        entry_idx = idx
                        entry_time = c["time"]
                        entry_price = trade_candidate["entry_p"]
                        trade_candidate["status"] = "ACTIVE"
                        
                        # Simulate forward to outcome
                        exit_price = None
                        exit_time = None
                        exit_reason = None
                        be_active = False

                        for fwd_idx in range(idx, min(n, idx + 48)): # Max 48 candles hold
                            fc = candles[fwd_idx]
                            
                            # 1. Hard SL
                            if fc["low"] <= trade_candidate["hsl_p"]:
                                exit_price = trade_candidate["hsl_p"]
                                exit_time = fc["time"]
                                exit_reason = "HARD_SL"
                                break
                            
                            # 2. Breakeven Trigger
                            if not be_active and fc["high"] >= trade_candidate["bet_p"]:
                                be_active = True
                                
                            # 3. Take Profit
                            if fc["high"] >= trade_candidate["tp_p"]:
                                exit_price = trade_candidate["tp_p"]
                                exit_time = fc["time"]
                                exit_reason = "TP_HIT"
                                break
                                
                            # 4. Breakeven Exit at Fee Shield
                            if be_active and fc["low"] <= trade_candidate["fee_be_p"]:
                                exit_price = trade_candidate["fee_be_p"]
                                exit_time = fc["time"]
                                exit_reason = "FEE_SHIELD_BE"
                                break
                                
                            # 5. Soft SL on Candle Close
                            if not be_active and fc["close"] <= trade_candidate["ssl_p"]:
                                exit_price = fc["close"]
                                exit_time = fc["time"]
                                exit_reason = "SOFT_SL"
                                break

                        if not exit_reason:
                            # End of data or time exit
                            last_c = candles[min(n - 1, idx + 47)]
                            exit_price = last_c["close"]
                            exit_time = last_c["time"]
                            exit_reason = "TIME_CLOSE"

                        # Calculate PnL & ROE
                        price_return = (exit_price - entry_price) / entry_price
                        gross_pnl_pct = price_return * self.leverage
                        # Total fees: entry fee + exit fee (each 0.05% * 5x leverage = 0.25% * 2 = 0.50% fee drag)
                        fee_drag = 2 * (self.fee_rate * self.leverage)
                        net_roe_pct = gross_pnl_pct - fee_drag

                        is_win = (exit_reason == "TP_HIT")
                        is_be = (exit_reason == "FEE_SHIELD_BE") or (abs(net_roe_pct) < 0.005)
                        is_loss = (exit_reason in ["HARD_SL", "SOFT_SL"]) and not is_be

                        trades.append({
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "mode": trade_candidate["mode"],
                            "airspace": round(trade_candidate["airspace"], 2),
                            "entry_time": datetime.fromtimestamp(entry_time / 1000, tz=IST).strftime("%Y-%m-%d %H:%M"),
                            "exit_time": datetime.fromtimestamp(exit_time / 1000, tz=IST).strftime("%Y-%m-%d %H:%M"),
                            "entry_price": round(entry_price, 5),
                            "exit_price": round(exit_price, 5),
                            "exit_reason": exit_reason,
                            "price_return_pct": round(price_return * 100, 2),
                            "net_roe_pct": round(net_roe_pct * 100, 2),
                            "is_win": is_win,
                            "is_be": is_be,
                            "is_loss": is_loss
                        })
                        # Remove mitigated trade candidate
                        active_obs.remove(trade_candidate)

        return trades

    def run_master_portfolio_compounding(self, pairs: List[str], timeframes: List[str] = ["1h", "4h"]) -> Dict[str, Any]:
        # Load BTC for shield
        btc_file_1h = os.path.join(CACHE_DIR, "BTCUSDT_1h.json")
        btc_candles = self.load_candles(btc_file_1h) if os.path.exists(btc_file_1h) else None

        all_trades = []
        for sym in pairs:
            for tf in timeframes:
                fpath = os.path.join(CACHE_DIR, f"{sym}_{tf}.json")
                if os.path.exists(fpath):
                    c = self.load_candles(fpath)
                    t_list = self.run_backtest_symbol(sym, tf, c, btc_candles)
                    all_trades.extend(t_list)

        # Sort all trades chronologically
        all_trades.sort(key=lambda x: x["entry_time"])

        # Run Compounding Simulation starting at $50
        balance = self.initial_capital
        peak_balance = balance
        max_drawdown = 0.0
        compounding_ledger = []

        wins = 0
        losses = 0
        breakevens = 0
        gross_profit = 0.0
        gross_loss = 0.0

        for idx, t in enumerate(all_trades):
            start_bal = balance
            # Dynamic position sizing: 100% compounding allocation
            pnl_usd = start_bal * (t["net_roe_pct"] / 100.0)
            balance += pnl_usd
            if balance > peak_balance:
                peak_balance = balance
            dd = (peak_balance - balance) / peak_balance * 100.0
            if dd > max_drawdown:
                max_drawdown = dd

            if t["is_win"]:
                wins += 1
                gross_profit += pnl_usd
            elif t["is_be"]:
                breakevens += 1
            else:
                losses += 1
                gross_loss += abs(pnl_usd)

            t_record = dict(t)
            t_record["trade_num"] = idx + 1
            t_record["start_balance"] = round(start_bal, 2)
            t_record["pnl_usd"] = round(pnl_usd, 2)
            t_record["end_balance"] = round(balance, 2)
            t_record["drawdown_pct"] = round(dd, 2)
            compounding_ledger.append(t_record)

        total_trades = len(all_trades)
        win_rate = (wins / total_trades * 100.0) if total_trades > 0 else 0.0
        loss_rate = (losses / total_trades * 100.0) if total_trades > 0 else 0.0
        be_rate = (breakevens / total_trades * 100.0) if total_trades > 0 else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 999.0
        capital_safety = 100.0 - loss_rate

        return {
            "initial_capital": self.initial_capital,
            "final_balance": round(balance, 2),
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "breakevens": breakevens,
            "win_rate_pct": round(win_rate, 2),
            "loss_rate_pct": round(loss_rate, 2),
            "be_rate_pct": round(be_rate, 2),
            "capital_safety_pct": round(capital_safety, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
            "total_pnl_pct": round((balance - self.initial_capital) / self.initial_capital * 100.0, 2),
            "ledger": compounding_ledger
        }

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    backtester = GodTierSMCBacktester(initial_capital=50.0, leverage=5.0)
    # Scan all pairs available in cache
    cache_files = glob.glob(os.path.join(CACHE_DIR, "*_1h.json"))
    pairs = [os.path.basename(f).replace("_1h.json", "") for f in cache_files]
    print(f"Running Institutional God-Tier SMC Compounding Engine across {len(pairs)} pairs...")
    
    result = backtester.run_master_portfolio_compounding(pairs, timeframes=["1h", "4h"])
    
    print("\n=======================================================")
    print("INSTITUTIONAL GOD-TIER SMC COMPOUNDING RESULT")
    print("=======================================================")
    print(f"Starting Capital:     ${result['initial_capital']:.2f}")
    print(f"Final Balance:        ${result['final_balance']:.2f}")
    print(f"Total Trades:         {result['total_trades']}")
    print(f"Wins / Losses / BEs:  {result['wins']} Wins | {result['losses']} Losses | {result['breakevens']} Breakevens")
    print(f"Win Rate:             {result['win_rate_pct']}%")
    print(f"Loss Rate:            {result['loss_rate_pct']}%")
    print(f"Breakeven Rate:       {result['be_rate_pct']}%")
    print(f"Capital Safety:       {result['capital_safety_pct']}%")
    print(f"Profit Factor:        {result['profit_factor']}")
    print(f"Max Drawdown:         {result['max_drawdown_pct']}%")
    print(f"Total Net Growth:     +{result['total_pnl_pct']}%")
    print("=======================================================\n")

    # Save results to json and csv
    with open("godtier_smc_compounding_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    import pandas as pd
    df = pd.DataFrame(result["ledger"])
    df.to_csv("godtier_smc_compounding_ledger.csv", index=False)
    print("Ledger exported to godtier_smc_compounding_ledger.csv and godtier_smc_compounding_result.json")
