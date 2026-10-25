import json
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple

def compute_atr(candles: List[Dict[str, Any]], period: int = 14) -> List[float]:
    atrs = [0.0] * len(candles)
    if len(candles) < period + 1:
        return atrs
    tr_list = [0.0]
    for i in range(1, len(candles)):
        h = candles[i]["high"]
        l = candles[i]["low"]
        pc = candles[i-1]["close"]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        tr_list.append(tr)
    
    first_atr = sum(tr_list[1:period+1]) / period
    atrs[period] = first_atr
    curr_atr = first_atr
    for i in range(period + 1, len(candles)):
        curr_atr = (curr_atr * (period - 1) + tr_list[i]) / period
        atrs[i] = curr_atr
    return atrs

def run_forex_backtest(candles: List[Dict[str, Any]], symbol: str, model_type: str = "VOLATILITY_ADAPTIVE"):
    """
    model_type:
      - 'RIGID_CRYPTO_5PCT': 5.0% Displacement, 1.6% BE, 1.8% lock 0.9%, 2.8% TP
      - 'FX_FIXED_PCT': 0.60% Displacement, 0.35% BE, 0.50% lock 0.25%, 0.85% TP, 0.40% SL
      - 'FX_ATR_ADAPTIVE': Disp >= 2.0*ATR, BE @ 1.5*ATR, Lock @ 2.0*ATR, TP @ 3.0*ATR, SL @ OB + 0.5*ATR
    """
    n = len(candles)
    if n < 200:
        return {"error": "Insufficient candles"}

    atrs = compute_atr(candles, 14)
    trades = []
    active_trade = None
    min_maturation = 18 # 18 bars (18 hours)
    
    # Track unmitigated OBs
    active_obs = [] # list of dicts

    for i in range(20, n):
        c = candles[i]
        curr_t = c["time"]
        o, h, l, cl = c["open"], c["high"], c["low"], c["close"]
        curr_atr = atrs[i] or (c["close"] * 0.005)

        # 1. Manage Active Trade
        if active_trade is not None:
            side = active_trade["side"]
            entry_p = active_trade["entry_price"]
            sl_p = active_trade["sl_price"]
            tp_p = active_trade["tp_price"]
            be_p = active_trade["be_price"]
            lock_p = active_trade["lock_price"]
            lock_trig_p = active_trade["lock_trigger_price"]
            stage = active_trade["stage"] # 0: normal, 1: BE, 2: Locked
            bars_held = i - active_trade["entry_bar"]

            exit_trade = False
            exit_price = 0.0
            exit_reason = ""

            if side == "BUY":
                # Check TP
                if h >= tp_p:
                    exit_trade = True
                    exit_price = tp_p
                    exit_reason = "TP"
                # Check SL
                elif l <= sl_p:
                    exit_trade = True
                    exit_price = sl_p
                    exit_reason = "SL"
                else:
                    # Stepped Armor Updates
                    if stage == 0 and h >= be_p:
                        active_trade["sl_price"] = entry_p # Move to Break-Even
                        active_trade["stage"] = 1
                    elif stage == 1 and h >= lock_trig_p:
                        active_trade["sl_price"] = lock_p # Move to Profit Lock
                        active_trade["stage"] = 2

            else: # SELL
                # Check TP
                if l <= tp_p:
                    exit_trade = True
                    exit_price = tp_p
                    exit_reason = "TP"
                elif h >= sl_p:
                    exit_trade = True
                    exit_price = sl_p
                    exit_reason = "SL"
                else:
                    if stage == 0 and l <= be_p:
                        active_trade["sl_price"] = entry_p # Move to Break-Even
                        active_trade["stage"] = 1
                    elif stage == 1 and l <= lock_trig_p:
                        active_trade["sl_price"] = lock_p # Move to Profit Lock
                        active_trade["stage"] = 2

            if exit_trade:
                pnl_pct = (exit_price - entry_p) / entry_p * 100.0 if side == "BUY" else (entry_p - exit_price) / entry_p * 100.0
                trades.append({
                    "symbol": symbol,
                    "side": side,
                    "entry_time": active_trade["entry_time"],
                    "exit_time": curr_t,
                    "entry_price": entry_p,
                    "exit_price": exit_price,
                    "pnl_pct": pnl_pct,
                    "result": exit_reason,
                    "bars_held": bars_held,
                    "stage_reached": active_trade["stage"]
                })
                active_trade = None

        # 2. Check Expirations & Invalidation on active OBs
        surviving_obs = []
        for ob in active_obs:
            # Check invalidation
            if ob["side"] == "BUY" and cl < ob["ob_low"]:
                continue
            if ob["side"] == "SELL" and cl > ob["ob_high"]:
                continue
            # Check maximum lifespan (150 bars)
            if (i - ob["bar_idx"]) > 150:
                continue
            surviving_obs.append(ob)
        active_obs = surviving_obs

        # 3. Check for New Order Block Detection at bar i-2
        # Candle c3 is at i-2, c2 at i-1, c1 at i
        c3 = candles[i-2]
        c2 = candles[i-1]
        c1 = candles[i]
        
        # Bullish OB Check
        if c3["close"] < c3["open"]: # Strict Red
            if c1["low"] > c3["high"]: # Bullish FVG
                disp_val = max(c1["high"], c2["high"]) - c3["low"]
                disp_pct = disp_val / c3["low"] * 100.0
                
                req_disp = 5.0 if model_type == "RIGID_CRYPTO_5PCT" else (0.60 if model_type == "FX_FIXED_PCT" else 2.0 * curr_atr / c3["low"] * 100.0)
                if disp_pct >= req_disp:
                    ob_high = max(c3["open"], c3["high"])
                    ob_low = c3["low"]
                    ob_range = ob_high - ob_low
                    entry_p = ob_high - (ob_range * 0.05)
                    
                    active_obs.append({
                        "side": "BUY",
                        "bar_idx": i-2,
                        "time": c3["time"],
                        "ob_high": ob_high,
                        "ob_low": ob_low,
                        "entry_price": entry_p,
                        "atr": curr_atr,
                        "tapped": False
                    })

        # Bearish OB Check
        if c3["close"] > c3["open"]: # Strict Green
            if c1["high"] < c3["low"]: # Bearish FVG
                disp_val = c3["high"] - min(c1["low"], c2["low"])
                disp_pct = disp_val / c3["high"] * 100.0
                
                req_disp = 5.0 if model_type == "RIGID_CRYPTO_5PCT" else (0.60 if model_type == "FX_FIXED_PCT" else 2.0 * curr_atr / c3["high"] * 100.0)
                if disp_pct >= req_disp:
                    ob_high = c3["high"]
                    ob_low = min(c3["open"], c3["low"])
                    ob_range = ob_high - ob_low
                    entry_p = ob_low + (ob_range * 0.05)
                    
                    active_obs.append({
                        "side": "SELL",
                        "bar_idx": i-2,
                        "time": c3["time"],
                        "ob_high": ob_high,
                        "ob_low": ob_low,
                        "entry_price": entry_p,
                        "atr": curr_atr,
                        "tapped": False
                    })

        # 4. Check Retest / Tap Trigger on Mature Virgin OBs
        if active_trade is None:
            for ob in active_obs:
                if ob["tapped"]:
                    continue
                bars_alive = i - ob["bar_idx"]
                if bars_alive < min_maturation:
                    # If price touches zone before maturation -> invalidate as premature
                    if ob["side"] == "BUY" and l <= ob["entry_price"]:
                        ob["tapped"] = True # Mitigated prematurely
                    elif ob["side"] == "SELL" and h >= ob["entry_price"]:
                        ob["tapped"] = True
                    continue

                # Check if current candle taps the 5% boundary
                can_enter = False
                if ob["side"] == "BUY" and l <= ob["entry_price"] and cl >= ob["ob_low"]:
                    can_enter = True
                elif ob["side"] == "SELL" and h >= ob["entry_price"] and cl <= ob["ob_high"]:
                    can_enter = True

                if can_enter:
                    ob["tapped"] = True # Virgin mark consumed
                    ent_p = ob["entry_price"]
                    side = ob["side"]
                    atr_v = ob["atr"]

                    if model_type == "RIGID_CRYPTO_5PCT":
                        if side == "BUY":
                            tp_price = ent_p * (1.0 + 0.0280)
                            sl_price = ent_p * (1.0 - 0.0240)
                            be_price = ent_p * (1.0 + 0.0160)
                            lock_trig = ent_p * (1.0 + 0.0180)
                            lock_price = ent_p * (1.0 + 0.0090)
                        else:
                            tp_price = ent_p * (1.0 - 0.0280)
                            sl_price = ent_p * (1.0 + 0.0240)
                            be_price = ent_p * (1.0 - 0.0160)
                            lock_trig = ent_p * (1.0 - 0.0180)
                            lock_price = ent_p * (1.0 - 0.0090)

                    elif model_type == "FX_FIXED_PCT":
                        if side == "BUY":
                            tp_price = ent_p * (1.0 + 0.0085)
                            sl_price = ent_p * (1.0 - 0.0040)
                            be_price = ent_p * (1.0 + 0.0035)
                            lock_trig = ent_p * (1.0 + 0.0050)
                            lock_price = ent_p * (1.0 + 0.0025)
                        else:
                            tp_price = ent_p * (1.0 - 0.0085)
                            sl_price = ent_p * (1.0 + 0.0040)
                            be_price = ent_p * (1.0 - 0.0035)
                            lock_trig = ent_p * (1.0 - 0.0050)
                            lock_price = ent_p * (1.0 - 0.0025)

                    else: # FX_ATR_ADAPTIVE
                        if side == "BUY":
                            tp_price = ent_p + 3.0 * atr_v
                            sl_price = ob["ob_low"] - 0.5 * atr_v
                            be_price = ent_p + 1.5 * atr_v
                            lock_trig = ent_p + 2.0 * atr_v
                            lock_price = ent_p + 1.0 * atr_v
                        else:
                            tp_price = ent_p - 3.0 * atr_v
                            sl_price = ob["ob_high"] + 0.5 * atr_v
                            be_price = ent_p - 1.5 * atr_v
                            lock_trig = ent_p - 2.0 * atr_v
                            lock_price = ent_p - 1.0 * atr_v

                    active_trade = {
                        "side": side,
                        "entry_bar": i,
                        "entry_time": curr_t,
                        "entry_price": ent_p,
                        "tp_price": tp_price,
                        "sl_price": sl_price,
                        "be_price": be_price,
                        "lock_price": lock_price,
                        "lock_trigger_price": lock_trig,
                        "stage": 0
                    }
                    break

    # Calculate Performance Stats
    total = len(trades)
    wins = [t for t in trades if t["pnl_pct"] > 0]
    be_trades = [t for t in trades if abs(t["pnl_pct"]) < 0.0001]
    losses = [t for t in trades if t["pnl_pct"] < -0.0001]
    
    win_count = len(wins)
    loss_count = len(losses)
    be_count = len(be_trades)

    # Win rate considering BE as non-loss (Standard Institutional Quant)
    effective_wins = win_count + be_count
    win_rate = (win_count / total * 100.0) if total > 0 else 0.0
    safe_win_rate = (effective_wins / total * 100.0) if total > 0 else 0.0

    gross_profit = sum(t["pnl_pct"] for t in wins)
    gross_loss = abs(sum(t["pnl_pct"] for t in losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)
    net_pnl = gross_profit - gross_loss

    # Max Drawdown
    equity = 100.0
    peak = 100.0
    max_dd = 0.0
    for t in trades:
        equity += t["pnl_pct"]
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100.0
        if dd > max_dd:
            max_dd = dd

    return {
        "symbol": symbol,
        "model": model_type,
        "total_trades": total,
        "wins": win_count,
        "losses": loss_count,
        "break_even": be_count,
        "pure_win_rate": round(win_rate, 2),
        "safe_win_rate": round(safe_win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "net_pnl_pct": round(net_pnl, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "avg_trade_pnl": round(net_pnl / total, 3) if total > 0 else 0.0
    }

def main():
    forex_files = [
        "EURUSD_1h.json", "GBPUSD_1h.json", "USDJPY_1h.json",
        "AUDUSD_1h.json", "USDCAD_1h.json", "USDCHF_1h.json",
        "NZDUSD_1h.json", "EURGBP_1h.json", "EURJPY_1h.json",
        "GBPJPY_1h.json", "XAUUSD_1h.json"
    ]
    forex_dir = Path("historical_data_forex")

    all_results = {}
    for model in ["RIGID_CRYPTO_5PCT", "FX_FIXED_PCT", "FX_ATR_ADAPTIVE"]:
        print(f"\n--- TESTING MODEL: {model} ---")
        model_results = []
        tot_trades = 0
        tot_wins = 0
        tot_losses = 0
        tot_be = 0
        tot_net_pnl = 0.0

        for f_name in forex_files:
            sym = f_name.replace("_1h.json", "")
            f_path = forex_dir / f_name
            if not f_path.exists():
                continue
            candles = json.loads(f_path.read_text())
            res = run_forex_backtest(candles, sym, model)
            model_results.append(res)
            
            tot_trades += res["total_trades"]
            tot_wins += res["wins"]
            tot_losses += res["losses"]
            tot_be += res["break_even"]
            tot_net_pnl += res["net_pnl_pct"]

            print(f"[{sym:<7}] Trades: {res['total_trades']:<4} | Win: {res['pure_win_rate']}% | Safe WR (incl BE): {res['safe_win_rate']}% | PF: {res['profit_factor']:<5} | Net: {res['net_pnl_pct']}% | MaxDD: {res['max_drawdown_pct']}%")

        overall_pure_wr = round(tot_wins / tot_trades * 100.0, 2) if tot_trades > 0 else 0.0
        overall_safe_wr = round((tot_wins + tot_be) / tot_trades * 100.0, 2) if tot_trades > 0 else 0.0
        all_results[model] = {
            "summary": {
                "total_trades": tot_trades,
                "wins": tot_wins,
                "losses": tot_losses,
                "break_even": tot_be,
                "overall_pure_win_rate": overall_pure_wr,
                "overall_safe_win_rate": overall_safe_wr,
                "total_net_pnl_pct": round(tot_net_pnl, 2)
            },
            "per_pair": model_results
        }
        print(f"\n>>> OVERALL {model}: Total Trades: {tot_trades} | Pure Win Rate: {overall_pure_wr}% | Safe Win Rate: {overall_safe_wr}% | Total Net PnL: {tot_net_pnl:.2f}%")

    with open("forex_1h_all_pairs_audit_report.json", "w") as out_f:
        json.dump(all_results, out_f, indent=2)
    print("\nSaved full audit to forex_1h_all_pairs_audit_report.json")

if __name__ == "__main__":
    main()
