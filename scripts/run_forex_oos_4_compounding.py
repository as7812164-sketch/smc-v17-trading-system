import json
import math
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

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

def simulate_track_oos(candles_full: List[Dict[str, Any]], symbol: str, start_balance: float = 50.0):
    # Split into strictly Out-Of-Sample (OOS: second half, last ~6,160 candles)
    n_full = len(candles_full)
    oos_start_idx = n_full // 2
    candles = candles_full[oos_start_idx:]
    n = len(candles)

    atrs = compute_atr(candles, 14)
    balance = start_balance
    peak_balance = start_balance
    max_dd = 0.0

    active_trade = None
    min_maturation = 18
    active_obs = []
    trades = []
    milestones = []

    # Scaling per symbol:
    # EURUSD & USDCHF: 1 pip = 0.0001
    # AUDUSD: 1 pip = 0.0001
    # XAUUSD: 1 pip/point = 0.10 ($1.00 = 10 pips)
    is_gold = (symbol == "XAUUSD")
    min_disp_pct = 1.50 if is_gold else 0.50

    # Risk & Target definition:
    # Target: +10% gain on current balance when TP is hit!
    # SL: 3.6% loss on current balance when SL is hit!
    # Stage 1: +4% move -> BE (SL = Entry)
    # Stage 2: +6% move -> Lock +3% profit (SL = Entry + 0.3*Target)

    for i in range(25, n):
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
            lock_trig_p = active_trade["lock_trigger_price"]
            lock_p = active_trade["lock_price"]
            stage = active_trade["stage"]
            bars_held = i - active_trade["entry_bar"]

            exit_trade = False
            exit_price = 0.0
            exit_reason = ""

            if side == "BUY":
                if h >= tp_p:
                    exit_trade = True
                    exit_price = tp_p
                    exit_reason = "TP"
                elif l <= sl_p:
                    exit_trade = True
                    exit_price = sl_p
                    exit_reason = "SL"
                else:
                    if stage == 0 and h >= be_p:
                        active_trade["sl_price"] = entry_p
                        active_trade["stage"] = 1
                    elif stage == 1 and h >= lock_trig_p:
                        active_trade["sl_price"] = lock_p
                        active_trade["stage"] = 2
            else: # SELL
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
                        active_trade["sl_price"] = entry_p
                        active_trade["stage"] = 1
                    elif stage == 1 and l <= lock_trig_p:
                        active_trade["sl_price"] = lock_p
                        active_trade["stage"] = 2

            if exit_trade:
                trade_pnl_pct = 0.0
                if exit_reason == "TP":
                    trade_pnl_pct = 10.0 # +10% target
                elif exit_reason == "SL":
                    if stage == 1:
                        trade_pnl_pct = 0.0 # Break-Even
                    elif stage == 2:
                        trade_pnl_pct = 3.0 # Locked +3%
                    else:
                        trade_pnl_pct = -3.6 # -3.6% Risk

                profit_usd = balance * (trade_pnl_pct / 100.0)
                balance += profit_usd
                if balance > peak_balance:
                    peak_balance = balance
                dd = (peak_balance - balance) / peak_balance * 100.0
                if dd > max_dd:
                    max_dd = dd

                # Check Milestones
                for m_val in [100.0, 250.0, 500.0, 1000.0, 2000.0]:
                    if balance >= m_val and m_val not in [m["val"] for m in milestones]:
                        milestones.append({"val": m_val, "trade_num": len(trades) + 1, "time": curr_t})

                trades.append({
                    "symbol": symbol,
                    "trade_num": len(trades) + 1,
                    "side": side,
                    "pnl_pct": trade_pnl_pct,
                    "profit_usd": round(profit_usd, 2),
                    "balance_after": round(balance, 2),
                    "result": exit_reason if trade_pnl_pct != 0 else "BE",
                    "stage": stage,
                    "bars_held": bars_held
                })
                active_trade = None

        # Clean OBs
        surviving = []
        for ob in active_obs:
            if ob["side"] == "BUY" and cl < ob["ob_low"]:
                continue
            if ob["side"] == "SELL" and cl > ob["ob_high"]:
                continue
            if (i - ob["bar_idx"]) > 180:
                continue
            surviving.append(ob)
        active_obs = surviving

        # OB Identification at i-2
        c3, c2, c1 = candles[i-2], candles[i-1], candles[i]

        # Bullish OB
        if c3["close"] < c3["open"] and c1["low"] > c3["high"]:
            disp_pct = (max(c1["high"], c2["high"]) - c3["low"]) / c3["low"] * 100.0
            if disp_pct >= min_disp_pct:
                ob_high = max(c3["open"], c3["high"])
                ob_low = c3["low"]
                ob_range = ob_high - ob_low
                ent = ob_high - (ob_range * 0.05)
                active_obs.append({
                    "side": "BUY", "bar_idx": i-2, "ob_high": ob_high, "ob_low": ob_low,
                    "entry_price": ent, "atr": curr_atr, "tapped": False
                })

        # Bearish OB
        if c3["close"] > c3["open"] and c1["high"] < c3["low"]:
            disp_pct = (c3["high"] - min(c1["low"], c2["low"])) / c3["high"] * 100.0
            if disp_pct >= min_disp_pct:
                ob_high = c3["high"]
                ob_low = min(c3["open"], c3["low"])
                ob_range = ob_high - ob_low
                ent = ob_low + (ob_range * 0.05)
                active_obs.append({
                    "side": "SELL", "bar_idx": i-2, "ob_high": ob_high, "ob_low": ob_low,
                    "entry_price": ent, "atr": curr_atr, "tapped": False
                })

        # Retest on mature virgin OB
        if active_trade is None:
            for ob in active_obs:
                if ob["tapped"]:
                    continue
                bars_alive = i - ob["bar_idx"]
                if bars_alive < min_maturation:
                    if (ob["side"] == "BUY" and l <= ob["entry_price"]) or (ob["side"] == "SELL" and h >= ob["entry_price"]):
                        ob["tapped"] = True
                    continue

                can_enter = False
                if ob["side"] == "BUY" and l <= ob["entry_price"] and cl >= ob["ob_low"]:
                    can_enter = True
                elif ob["side"] == "SELL" and h >= ob["entry_price"] and cl <= ob["ob_high"]:
                    can_enter = True

                if can_enter:
                    ob["tapped"] = True
                    ent_p = ob["entry_price"]
                    side = ob["side"]
                    atr_v = ob["atr"]

                    # 18-pip equivalent SL and 50-pip equivalent TP
                    # For EURUSD, 18 pips = 0.0018
                    # For Gold, 18 pips = $1.80
                    risk_move = (ent_p * 0.0018) if not is_gold else (18.0 * 0.10)
                    target_move = (ent_p * 0.0050) if not is_gold else (50.0 * 0.10)

                    if side == "BUY":
                        sl_price = ent_p - risk_move
                        tp_price = ent_p + target_move
                        be_price = ent_p + (target_move * 0.40) # +20 pips
                        lock_trig = ent_p + (target_move * 0.60) # +30 pips
                        lock_price = ent_p + (target_move * 0.30) # +15 pips
                    else:
                        sl_price = ent_p + risk_move
                        tp_price = ent_p - target_move
                        be_price = ent_p - (target_move * 0.40)
                        lock_trig = ent_p - (target_move * 0.60)
                        lock_price = ent_p - (target_move * 0.30)

                    active_trade = {
                        "side": side, "entry_bar": i, "entry_time": curr_t,
                        "entry_price": ent_p, "tp_price": tp_price, "sl_price": sl_price,
                        "be_price": be_price, "lock_price": lock_price,
                        "lock_trigger_price": lock_trig, "stage": 0
                    }
                    break

    tot = len(trades)
    wins = [t for t in trades if t["pnl_pct"] > 0]
    be = [t for t in trades if t["pnl_pct"] == 0]
    losses = [t for t in trades if t["pnl_pct"] < 0]
    
    w_count = len(wins)
    l_count = len(losses)
    be_count = len(be)
    
    pure_wr = round(w_count / tot * 100.0, 1) if tot > 0 else 0.0
    safe_wr = round((w_count + be_count) / tot * 100.0, 1) if tot > 0 else 0.0
    growth_pct = round((balance - start_balance) / start_balance * 100.0, 1)

    return {
        "symbol": symbol,
        "start_balance": start_balance,
        "final_balance": round(balance, 2),
        "growth_pct": growth_pct,
        "total_trades": tot,
        "wins": w_count,
        "losses": l_count,
        "break_even": be_count,
        "pure_win_rate": pure_wr,
        "safe_win_rate": safe_wr,
        "max_drawdown_pct": round(max_dd, 1),
        "milestones": milestones,
        "trades": trades
    }

def main():
    print("=" * 70)
    print("  HERMES 3.5: 1-YEAR OUT-OF-SAMPLE (OOS) 4-COMPOUNDING TRACK AUDIT")
    print("  Dataset: Strictly Unseen OOS (Sep 2025 – Sep 2026 | 6,160 Candlesticks)")
    print("  Capital: $50.00 USDT x 4 Tracks = $200.00 Total Initial Equity")
    print("=" * 70)

    pairs = ["EURUSD", "USDCHF", "XAUUSD", "AUDUSD"]
    data_dir = Path("historical_data_forex")
    
    tracks_results = []
    tot_initial = 200.0
    tot_final = 0.0
    tot_trades_all = 0
    tot_wins_all = 0
    tot_be_all = 0
    tot_losses_all = 0

    for idx, sym in enumerate(pairs, 1):
        f = data_dir / f"{sym}_1h.json"
        candles_full = json.loads(f.read_text())
        res = simulate_track_oos(candles_full, sym, start_balance=50.0)
        tracks_results.append(res)
        
        tot_final += res["final_balance"]
        tot_trades_all += res["total_trades"]
        tot_wins_all += res["wins"]
        tot_be_all += res["break_even"]
        tot_losses_all += res["losses"]

        print(f"\n[TRACK {idx}] {sym} ($50 Starting Margin)")
        print(f"  - Final Balance: ${res['final_balance']:.2f} (Growth: +{res['growth_pct']}%)")
        print(f"  - Trades: {res['total_trades']} | Wins: {res['wins']} | BE: {res['break_even']} | Losses: {res['losses']}")
        print(f"  - Pure Win Rate: {res['pure_win_rate']}% | Safe WR (incl. BE): {res['safe_win_rate']}%")
        print(f"  - Max Drawdown: {res['max_drawdown_pct']}%")
        if res["milestones"]:
            ms_str = ", ".join([f"${m['val']:.0f} @ Trade #{m['trade_num']}" for m in res["milestones"]])
            print(f"  - Milestones: {ms_str}")
        else:
            print(f"  - Milestones: None crossed above $100")

    portfolio_growth_pct = round((tot_final - tot_initial) / tot_initial * 100.0, 1)
    overall_pure_wr = round(tot_wins_all / tot_trades_all * 100.0, 1) if tot_trades_all > 0 else 0.0
    overall_safe_wr = round((tot_wins_all + tot_be_all) / tot_trades_all * 100.0, 1) if tot_trades_all > 0 else 0.0

    print("\n" + "=" * 70)
    print("  [AUDIT] CUMULATIVE 4-COMPOUNDING TRACK PORTFOLIO AUDIT (OOS)")
    print("=" * 70)
    print(f"  Initial Portfolio Capital: $200.00 USDT ($50 x 4 Tracks)")
    print(f"  Final Portfolio Balance:   ${tot_final:,.2f} USDT")
    print(f"  Net Portfolio Growth:      +{portfolio_growth_pct}%")
    print(f"  Total Portfolio Trades:    {tot_trades_all}")
    print(f"  Pure Win Rate:             {overall_pure_wr}%")
    print(f"  Safe Win Rate (incl BE):   {overall_safe_wr}%")
    print(f"  Total Wins:                {tot_wins_all}")
    print(f"  Total Break-Even Shields:  {tot_be_all}")
    print(f"  Total Losses:              {tot_losses_all}")
    print("=" * 70)

    # Save results to json
    with open("forex_4compounding_oos_results.json", "w") as out_f:
        json.dump({
            "tracks": tracks_results,
            "portfolio": {
                "initial": tot_initial,
                "final": round(tot_final, 2),
                "growth_pct": portfolio_growth_pct,
                "trades": tot_trades_all,
                "pure_wr": overall_pure_wr,
                "safe_wr": overall_safe_wr
            }
        }, out_f, indent=2)

if __name__ == "__main__":
    main()
