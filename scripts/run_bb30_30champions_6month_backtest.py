"""
BB 3.0: 6-MONTH OFFICIAL 30-CHAMPIONS DECA COMPOUNDING BACKTEST
================================================================
Simulates 180 Days of real market data across all 30 Dedicated Champions:
  Section 1:  BTCUSDT, ETHUSDT, BCHUSDT
  Section 2:  SOLUSDT, BNBUSDT, SEIUSDT
  Section 3:  AVAXUSDT, DOGEUSDT, KAVAUSDT
  Section 4:  DOTUSDT, LINKUSDT, ENSUSDT
  Section 5:  LTCUSDT, NEARUSDT, DYDXUSDT
  Section 6:  OPUSDT, RENDERUSDT, WLDUSDT
  Section 7:  SUIUSDT, TIAUSDT, TRBUSDT
  Section 8:  UNIUSDT, XRPUSDT, SNXUSDT
  Section 9:  1000PEPEUSDT, APTUSDT, ARKMUSDT
  Section 10: ARBUSDT, FETUSDT, ONDOUSDT

Parameters:
- Initial Capital: $500.00 USDT ($50.00 per section * 10 sections)
- 5% Isolated Section Compounding Risk
- Section Concurrency: Max 1 position per section (Zero cross-section risk)
- Strategy: BB 3.0 Stepped Trailing SL (Model 3)
  * PDH / PDL Liquidity Sweeps
  * 15m Extreme Order Block (displacement >= 1.2% + FVG)
  * 50% Mean Threshold Limit Entry
  * 0.15% Anti-Hunt Buffer SL
  * Stepped Trailing Profit Armor (+1.0R -> +0.2R BE, +1.5R -> +1.0R lock, +2.0R -> +1.5R lock, +2.5R TP)
  * 0.06R Taker Fee / Slippage Friction
"""

import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import time
from datetime import datetime, timezone
from pathlib import Path

SECTION_CHAMPIONS = {
    1: ["BTCUSDT", "ETHUSDT", "BCHUSDT"],
    2: ["SOLUSDT", "BNBUSDT", "SEIUSDT"],
    3: ["AVAXUSDT", "DOGEUSDT", "KAVAUSDT"],
    4: ["DOTUSDT", "LINKUSDT", "ENSUSDT"],
    5: ["LTCUSDT", "NEARUSDT", "DYDXUSDT"],
    6: ["OPUSDT", "RENDERUSDT", "WLDUSDT"],
    7: ["SUIUSDT", "TIAUSDT", "TRBUSDT"],
    8: ["UNIUSDT", "XRPUSDT", "SNXUSDT"],
    9: ["1000PEPEUSDT", "APTUSDT", "ARKMUSDT"],
    10: ["ARBUSDT", "FETUSDT", "ONDOUSDT"]
}

OUTPUT_DIR = Path("scratch/bb30_6month_30champions_results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_15m_candles(symbol):
    # Check new coins cache first
    p1 = Path(f"scratch/new_coin_6month_discovery/cache/{symbol}_15m_6m.json")
    if p1.exists():
        with open(p1) as f:
            return json.load(f)
    # Check original cache
    p2 = Path(f"market_data_cache_15m/{symbol}_15m.json")
    if p2.exists():
        with open(p2) as f:
            raw = json.load(f)
            # Standardize
            candles = []
            for k in raw:
                if isinstance(k, dict):
                    candles.append(k)
                else:
                    candles.append({
                        "time": k[0],
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[5])
                    })
            return candles
    return []

# Simulate BB 3.0 on a single coin over the last 180 days (17,280 bars)
def generate_coin_trades(symbol, sec_id):
    raw_candles = load_15m_candles(symbol)
    if not raw_candles:
        print(f"Warning: No candles found for {symbol}")
        return []
        
    # Take the last 180 days (17,280 candles)
    candles = raw_candles[-17280:] if len(raw_candles) >= 17280 else raw_candles
    if len(candles) < 1000:
        return []

    # Aggregate into daily bars for PDH/PDL
    daily_candles = []
    day_map = {}
    for c in candles:
        day_str = datetime.fromtimestamp(c["time"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        if day_str not in day_map:
            day_map[day_str] = []
        day_map[day_str].append(c)

    day_keys = sorted(list(day_map.keys()))
    for dk in day_keys:
        bars = day_map[dk]
        d_open = bars[0]["open"]
        d_high = max(b["high"] for b in bars)
        d_low = min(b["low"] for b in bars)
        d_close = bars[-1]["close"]
        d_vol = sum(b["volume"] for b in bars)
        daily_candles.append({
            "day": dk,
            "open": d_open,
            "high": d_high,
            "low": d_low,
            "close": d_close,
            "volume": d_vol
        })

    trades = []
    
    for i in range(1, len(daily_candles)):
        prev_d = daily_candles[i-1]
        curr_d = daily_candles[i]
        
        pdh = prev_d["high"]
        pdl = prev_d["low"]
        
        day_15m = day_map[curr_d["day"]]
        if len(day_15m) < 15:
            continue
            
        has_long = False
        has_short = False
        
        # Bullish Model 3: PDL Sweep
        if curr_d["low"] < pdl and not has_long:
            for k in range(3, len(day_15m) - 10):
                c = day_15m[k]
                if c["low"] < pdl and c["close"] > pdl:
                    # Extreme OB check: next 1-3 bars show strong displacement >= 1.2%
                    c_fvg = day_15m[min(k+2, len(day_15m)-1)]
                    disp = (c_fvg["high"] - c["low"]) / c["low"]
                    if disp >= 0.012:
                        ob_high = max(c["open"], c["close"])
                        ob_low = c["low"]
                        mt_entry = (ob_high + ob_low) / 2.0
                        sl_price = ob_low * (1.0 - 0.0015) # 0.15% Anti-hunt buffer
                        risk = mt_entry - sl_price
                        if risk <= 0:
                            continue
                            
                        # Look for pullback tap
                        for m in range(k+1, min(k+16, len(day_15m))):
                            bar = day_15m[m]
                            if bar["low"] <= mt_entry <= bar["high"]:
                                # Fill!
                                exit_res = _eval_bb_trade(day_15m[m:], side="LONG", entry=mt_entry, sl=sl_price, risk=risk)
                                exit_res.update({
                                    "symbol": symbol,
                                    "section_id": sec_id,
                                    "side": "LONG",
                                    "entry_price": mt_entry,
                                    "sl_price": sl_price,
                                    "risk": risk,
                                    "entry_time": bar["time"],
                                    "day": curr_d["day"]
                                })
                                trades.append(exit_res)
                                has_long = True
                                break
                    if has_long:
                        break

        # Bearish Model 3: PDH Sweep
        if curr_d["high"] > pdh and not has_short:
            for k in range(3, len(day_15m) - 10):
                c = day_15m[k]
                if c["high"] > pdh and c["close"] < pdh:
                    c_fvg = day_15m[min(k+2, len(day_15m)-1)]
                    disp = (c["high"] - c_fvg["low"]) / c["high"]
                    if disp >= 0.012:
                        ob_high = c["high"]
                        ob_low = min(c["open"], c["close"])
                        mt_entry = (ob_high + ob_low) / 2.0
                        sl_price = ob_high * (1.0 + 0.0015)
                        risk = sl_price - mt_entry
                        if risk <= 0:
                            continue
                            
                        for m in range(k+1, min(k+16, len(day_15m))):
                            bar = day_15m[m]
                            if bar["low"] <= mt_entry <= bar["high"]:
                                exit_res = _eval_bb_trade(day_15m[m:], side="SHORT", entry=mt_entry, sl=sl_price, risk=risk)
                                exit_res.update({
                                    "symbol": symbol,
                                    "section_id": sec_id,
                                    "side": "SHORT",
                                    "entry_price": mt_entry,
                                    "sl_price": sl_price,
                                    "risk": risk,
                                    "entry_time": bar["time"],
                                    "day": curr_d["day"]
                                })
                                trades.append(exit_res)
                                has_short = True
                                break
                    if has_short:
                        break
                        
    return trades

def _eval_bb_trade(future_bars, side, entry, sl, risk):
    trailing_sl = sl
    milestone = 0
    duration_bars = 0
    friction = 0.06 # Taker fee + slippage deduction
    
    for bar in future_bars[1:48]: # Hold up to 12 hours
        duration_bars += 1
        if side == "LONG":
            r_gain = (bar["high"] - entry) / risk
            
            # Stepped Trailing SL Milestones
            if r_gain >= 2.0 and milestone < 3:
                trailing_sl = entry + (1.5 * risk) # Lock +1.5R
                milestone = 3
            elif r_gain >= 1.5 and milestone < 2:
                trailing_sl = entry + (1.0 * risk) # Lock +1.0R
                milestone = 2
            elif r_gain >= 1.0 and milestone < 1:
                trailing_sl = entry + (0.2 * risk) # Fee Shield Breakeven
                milestone = 1
                
            # TP Hit (+2.5R)
            if r_gain >= 2.5:
                net_r = 2.5 - friction
                exit_price = entry + (2.5 * risk)
                return {"result": "WIN", "r_mult": net_r, "roi": net_r * 10.0, "reason": "TP_2.5R_HIT", "exit_price": exit_price, "duration_bars": duration_bars, "exit_time": bar["time"]}
            # Trailing SL or SL Hit
            if bar["low"] <= trailing_sl:
                exit_price = trailing_sl
                if milestone >= 2:
                    locked_r = 1.0 if milestone == 2 else 1.5
                    net_r = locked_r - friction
                    return {"result": "WIN", "r_mult": net_r, "roi": net_r * 10.0, "reason": f"+{locked_r}R_PROFIT_LOCKED", "exit_price": exit_price, "duration_bars": duration_bars, "exit_time": bar["time"]}
                elif milestone == 1:
                    net_r = 0.2 - friction
                    return {"result": "SAVE", "r_mult": net_r, "roi": net_r * 10.0, "reason": "FEE_SHIELD_SAVED", "exit_price": exit_price, "duration_bars": duration_bars, "exit_time": bar["time"]}
                else:
                    net_r = -1.0 - friction
                    return {"result": "LOSS", "r_mult": net_r, "roi": net_r * 10.0, "reason": "SL_HIT", "exit_price": exit_price, "duration_bars": duration_bars, "exit_time": bar["time"]}
        else: # SHORT
            r_gain = (entry - bar["low"]) / risk
            
            if r_gain >= 2.0 and milestone < 3:
                trailing_sl = entry - (1.5 * risk)
                milestone = 3
            elif r_gain >= 1.5 and milestone < 2:
                trailing_sl = entry - (1.0 * risk)
                milestone = 2
            elif r_gain >= 1.0 and milestone < 1:
                trailing_sl = entry - (0.2 * risk)
                milestone = 1
                
            if r_gain >= 2.5:
                net_r = 2.5 - friction
                exit_price = entry - (2.5 * risk)
                return {"result": "WIN", "r_mult": net_r, "roi": net_r * 10.0, "reason": "TP_2.5R_HIT", "exit_price": exit_price, "duration_bars": duration_bars, "exit_time": bar["time"]}
            if bar["high"] >= trailing_sl:
                exit_price = trailing_sl
                if milestone >= 2:
                    locked_r = 1.0 if milestone == 2 else 1.5
                    net_r = locked_r - friction
                    return {"result": "WIN", "r_mult": net_r, "roi": net_r * 10.0, "reason": f"+{locked_r}R_PROFIT_LOCKED", "exit_price": exit_price, "duration_bars": duration_bars, "exit_time": bar["time"]}
                elif milestone == 1:
                    net_r = 0.2 - friction
                    return {"result": "SAVE", "r_mult": net_r, "roi": net_r * 10.0, "reason": "FEE_SHIELD_SAVED", "exit_price": exit_price, "duration_bars": duration_bars, "exit_time": bar["time"]}
                else:
                    net_r = -1.0 - friction
                    return {"result": "LOSS", "r_mult": net_r, "roi": net_r * 10.0, "reason": "SL_HIT", "exit_price": exit_price, "duration_bars": duration_bars, "exit_time": bar["time"]}

    # Time Expiry Exit
    last_bar = future_bars[-1]
    last_close = last_bar["close"]
    cur_r = (last_close - entry) / risk if side == "LONG" else (entry - last_close) / risk
    net_r = cur_r - friction
    res_str = "WIN" if net_r > 0.5 else ("SAVE" if net_r >= -0.2 else "LOSS")
    return {"result": res_str, "r_mult": net_r, "roi": net_r * 10.0, "reason": "TIME_EXPIRY", "exit_price": last_close, "duration_bars": duration_bars, "exit_time": last_bar["time"]}

# --- MAIN CHRONOLOGICAL MULTI-SECTION SIMULATOR ---
def run_simulation():
    print("=" * 80)
    print("🚀 RUNNING 6-MONTH BB 3.0 (30 CHAMPIONS) DECA COMPOUNDING AUDIT")
    print("=" * 80)
    
    all_raw_trades = []
    per_coin_stats = {}
    
    for sec_id, coins in SECTION_CHAMPIONS.items():
        for coin in coins:
            trades = generate_coin_trades(coin, sec_id)
            print(f"  Sec {sec_id:2d} | {coin:<14} -> {len(trades):3d} raw trade triggers generated")
            all_raw_trades.extend(trades)
            
            # Coin stats
            w = sum(1 for t in trades if t["result"] == "WIN")
            s = sum(1 for t in trades if t["result"] == "SAVE")
            l = sum(1 for t in trades if t["result"] == "LOSS")
            tot = len(trades)
            net_r = sum(t["r_mult"] for t in trades)
            per_coin_stats[coin] = {
                "section": sec_id,
                "total_trades": tot,
                "wins": w,
                "saves": s,
                "losses": l,
                "pure_win_rate": round((w / tot * 100) if tot > 0 else 0, 1),
                "quality_win_rate": round(((w + s) / tot * 100) if tot > 0 else 0, 1),
                "net_r": round(net_r, 2)
            }
            
    # Sort all raw trades strictly chronologically
    all_raw_trades.sort(key=lambda x: x["entry_time"])
    print(f"\nTotal raw trade candidates across all 30 coins: {len(all_raw_trades)}")

    # Run Isolated Section Compounding Dispatcher
    # Enforces: Section Concurrency = 1 trade at a time per section!
    sections = {
        i: {
            "balance": 50.0,
            "initial": 50.0,
            "peak": 50.0,
            "max_dd": 0.0,
            "busy_until": 0,
            "coins": SECTION_CHAMPIONS[i],
            "trades": []
        } for i in range(1, 11)
    }

    executed_trades = []
    
    for t in all_raw_trades:
        sid = t["section_id"]
        sec = sections[sid]
        
        # Check if section was busy when trade triggered
        if t["entry_time"] < sec["busy_until"]:
            continue # Trade skipped because section was already in an active position!
            
        # Section is free! Execute trade!
        sec["busy_until"] = t["exit_time"]
        
        # Compounding: Risk 5% of section current balance
        risk_usdt = sec["balance"] * 0.05
        net_profit = risk_usdt * t["r_mult"]
        
        sec["balance"] += net_profit
        if sec["balance"] < 5.0:
            sec["balance"] = 5.0
            
        # Track drawdown
        if sec["balance"] > sec["peak"]:
            sec["peak"] = sec["balance"]
        else:
            dd = (sec["peak"] - sec["balance"]) / sec["peak"] * 100.0
            if dd > sec["max_dd"]:
                sec["max_dd"] = dd
                
        t_exec = dict(t)
        t_exec["risk_usdt"] = round(risk_usdt, 2)
        t_exec["net_profit"] = round(net_profit, 2)
        t_exec["section_balance_after"] = round(sec["balance"], 2)
        sec["trades"].append(t_exec)
        executed_trades.append(t_exec)

    print(f"Total non-conflicting executed trades: {len(executed_trades)}")

    # Monthly breakdown (6 Months)
    min_time = executed_trades[0]["entry_time"]
    max_time = executed_trades[-1]["entry_time"]
    month_duration = (max_time - min_time) / 6.0

    monthly_summary = []
    cur_portfolio = 500.0
    
    # Replay balances month-by-month
    temp_sections = {i: 50.0 for i in range(1, 11)}
    
    for m in range(6):
        m_start = min_time + (m * month_duration)
        m_end = min_time + ((m + 1) * month_duration)
        m_start_date = datetime.fromtimestamp(m_start / 1000, tz=timezone.utc).strftime("%d %b %Y")
        m_end_date = datetime.fromtimestamp(m_end / 1000, tz=timezone.utc).strftime("%d %b %Y")
        
        m_start_val = sum(temp_sections.values())
        m_trades = [t for t in executed_trades if m_start <= t["entry_time"] < m_end]
        
        w = 0
        s = 0
        l = 0
        
        for t in m_trades:
            sid = t["section_id"]
            risk = temp_sections[sid] * 0.05
            pnl = risk * t["r_mult"]
            temp_sections[sid] += pnl
            if temp_sections[sid] < 5.0:
                temp_sections[sid] = 5.0
                
            if t["result"] == "WIN":
                w += 1
            elif t["result"] == "SAVE":
                s += 1
            else:
                l += 1
                
        m_end_val = sum(temp_sections.values())
        m_pnl = m_end_val - m_start_val
        m_roi = (m_pnl / m_start_val * 100.0) if m_start_val > 0 else 0.0
        tot_m = len(m_trades)
        qual_wr = ((w + s) / tot_m * 100.0) if tot_m > 0 else 0.0
        pure_wr = (w / tot_m * 100.0) if tot_m > 0 else 0.0
        
        monthly_summary.append({
            "month": m + 1,
            "period": f"{m_start_date} - {m_end_date}",
            "starting_balance": round(m_start_val, 2),
            "ending_balance": round(m_end_val, 2),
            "net_profit": round(m_pnl, 2),
            "monthly_roi_pct": round(m_roi, 1),
            "trades_count": tot_m,
            "wins": w,
            "saves": s,
            "losses": l,
            "pure_win_rate": round(pure_wr, 1),
            "quality_win_rate": round(qual_wr, 1)
        })

    # Section-wise final breakdown
    sec_results = []
    for sid in range(1, 11):
        sec = sections[sid]
        final_bal = round(sec["balance"], 2)
        net_gain = round(final_bal - 50.0, 2)
        roi = round((net_gain / 50.0) * 100.0, 1)
        trades_count = len(sec["trades"])
        w = sum(1 for t in sec["trades"] if t["result"] == "WIN")
        s = sum(1 for t in sec["trades"] if t["result"] == "SAVE")
        l = sum(1 for t in sec["trades"] if t["result"] == "LOSS")
        qual_wr = round(((w + s) / trades_count * 100.0) if trades_count > 0 else 0, 1)
        
        sec_results.append({
            "section_id": sid,
            "assigned_coins": ", ".join(sec["coins"]),
            "starting_balance": 50.0,
            "final_balance": final_bal,
            "net_profit": net_gain,
            "roi_pct": roi,
            "total_trades": trades_count,
            "wins": w,
            "saves": s,
            "losses": l,
            "quality_win_rate": qual_wr,
            "max_drawdown_pct": round(sec["max_dd"], 1)
        })

    total_final = round(sum(s["final_balance"] for s in sec_results), 2)
    total_net = round(total_final - 500.0, 2)
    total_roi = round((total_net / 500.0) * 100.0, 1)
    tot_executed = len(executed_trades)
    tot_wins = sum(1 for t in executed_trades if t["result"] == "WIN")
    tot_saves = sum(1 for t in executed_trades if t["result"] == "SAVE")
    tot_losses = sum(1 for t in executed_trades if t["result"] == "LOSS")
    overall_pure_wr = round((tot_wins / tot_executed * 100.0) if tot_executed > 0 else 0, 1)
    overall_qual_wr = round(((tot_wins + tot_saves) / tot_executed * 100.0) if tot_executed > 0 else 0, 1)

    # Calculate overall max portfolio drawdown
    peak_port = 500.0
    max_port_dd = 0.0
    running_port = 500.0
    for t in executed_trades:
        running_port += t["net_profit"]
        if running_port > peak_port:
            peak_port = running_port
        else:
            dd = (peak_port - running_port) / peak_port * 100.0
            if dd > max_port_dd:
                max_port_dd = dd

    # Sample detailed trade logs (last 10 trades)
    recent_sample = []
    for t in executed_trades[-12:]:
        dt_ist = datetime.fromtimestamp(t["entry_time"] / 1000, tz=timezone.utc).strftime("%d %b, %H:%M UTC")
        dur_hrs = round((t["duration_bars"] * 15) / 60.0, 1)
        recent_sample.append({
            "time": dt_ist,
            "section": t["section_id"],
            "symbol": t["symbol"],
            "side": t["side"],
            "entry_price": round(t["entry_price"], 4),
            "exit_price": round(t["exit_price"], 4),
            "r_mult": round(t["r_mult"], 2),
            "pnl_usdt": round(t["net_profit"], 2),
            "result": t["result"],
            "reason": t["reason"],
            "duration": f"{dur_hrs}h"
        })

    final_payload = {
        "title": "BB 3.0 Official 6-Month 30-Champions Backtest Report",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "initial_capital": 500.0,
        "final_capital": total_final,
        "total_net_profit": total_net,
        "total_roi_pct": total_roi,
        "total_trades": tot_executed,
        "total_wins": tot_wins,
        "total_saves": tot_saves,
        "total_losses": tot_losses,
        "pure_win_rate": overall_pure_wr,
        "quality_win_rate": overall_qual_wr,
        "max_portfolio_drawdown_pct": round(max_port_dd, 1),
        "monthly_progression": monthly_summary,
        "section_breakdown": sec_results,
        "recent_sample_trades": recent_sample,
        "per_coin_performance": per_coin_stats
    }

    with open(OUTPUT_DIR / "bb30_6month_30champions_report.json", "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)

    print("\n" + "=" * 80)
    print("🏆 BB 3.0 6-MONTH BACKTEST EXECUTIVE SUMMARY")
    print("=" * 80)
    print(f"Starting Capital:            $500.00 USDT")
    print(f"Final Portfolio Equity:      ${total_final:,.2f} USDT")
    print(f"Total Net Profit:            +${total_net:,.2f} USDT (+{total_roi:,.1f}% ROI)")
    print(f"Total Executed Trades:       {tot_executed}")
    print(f"Wins / Saves / Losses:       {tot_wins} Wins | {tot_saves} Saves (BE) | {tot_losses} Losses")
    print(f"Quality Win Rate (W+S):      {overall_qual_wr}%")
    print(f"Pure Win Rate:               {overall_pure_wr}%")
    print(f"Max Portfolio Drawdown:      {max_port_dd:.1f}%")
    
    print("\n--- Month-by-Month Compounding Progression ---")
    for m in monthly_summary:
        print(f"  Month {m['month']} ({m['period']}): ${m['starting_balance']:,.2f} -> ${m['ending_balance']:,.2f} | Net: +${m['net_profit']:,.2f} (+{m['monthly_roi_pct']}%) | Trades: {m['trades_count']} (WR: {m['quality_win_rate']}%)")

    print("\n--- Section-by-Section Final Balance ---")
    for s in sec_results:
        print(f"  Sec {s['section_id']:2d} ({s['assigned_coins']:<38}): $50.00 -> ${s['final_balance']:,.2f} | +${s['net_profit']:,.2f} (+{s['roi_pct']:,.1f}%) | WR: {s['quality_win_rate']}%")

if __name__ == "__main__":
    run_simulation()
