import asyncio
import time
import sys
from typing import List, Dict, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    
from feed.binance_feed import binance_feed
from engine.smc_v17 import calculate_avg_body, find_true_origin
from config import DEFAULT_COINS, TIER1_COINS

async def run_exact_handwritten_backtest():
    coins = list(dict.fromkeys(TIER1_COINS + DEFAULT_COINS))
    
    print("================================================================================")
    print("  EXACT HANDWRITTEN SETUP BACKTEST: BUY ONLY | SWEEP + 2ND OB | 100 TRADES")
    print("================================================================================")
    
    configs = [
        {
            "tf": "1h",
            "qual_pct": 0.025,
            "tp_pct": 0.0150,     # +7.50% ROE @ 5x
            "sl_pct": 0.0200,     # -10.00% ROE @ 5x (Hybrid Soft)
            "be_pct": 0.0075,     # +3.75% ROE Breakeven Lock
            "leverage": 5,
            "tp_roe": 0.0750,
            "sl_roe": 0.1000,
            "use_candle_close_sl": False # 1H uses 2-layer hybrid
        },
        {
            "tf": "4h",
            "qual_pct": 0.040,
            "tp_pct": 0.0204,     # +10.20% ROE @ 5x
            "sl_pct": 0.0250,     # -12.50% ROE @ 5x (Soft Candle Close)
            "be_pct": 0.0102,     # +5.10% ROE Breakeven Lock
            "leverage": 5,
            "tp_roe": 0.1020,
            "sl_roe": 0.1250,
            "use_candle_close_sl": True # 4H uses Candle Close SL
        }
    ]
    
    all_results = {}

    for cfg in configs:
        tf = cfg["tf"]
        qual_pct = cfg["qual_pct"]
        tp_pct = cfg["tp_pct"]
        sl_pct = cfg["sl_pct"]
        be_pct = cfg["be_pct"]
        use_close_sl = cfg["use_candle_close_sl"]
        
        print(f"\n>>> Fetching data and backtesting BUY [SWEEP + 2ND OB] on [{tf.upper()}]...")
        
        all_klines = await binance_feed.fetch_multiple_symbols(coins, interval=tf, limit=1000)
        completed_trades = []
        
        for sym, candles in all_klines.items():
            if not candles or len(candles) < 60:
                continue
                
            n = len(candles)
            active_zones = []
            
            for cur_idx in range(15, n):
                c = candles[cur_idx]
                avg_b = calculate_avg_body(candles, cur_idx, 10)
                
                # Look for BUY displacement candle (Bullish)
                if avg_b > 0:
                    c_body = abs(c["close"] - c["open"])
                    if c["close"] > c["open"] and c_body >= 1.4 * avg_b:
                        o_idx = find_true_origin(candles, cur_idx, "BUY")
                        if o_idx is not None:
                            o_c = candles[o_idx]
                            ob_h = o_c["high"]
                            ob_l = o_c["low"]
                            target_q = ob_h * (1.0 + qual_pct)
                            
                            # Check Sweep Confluence: origin candle swept previous lows
                            has_sweep = False
                            if o_idx >= 3:
                                prev_lows = [candles[k]["low"] for k in range(max(0, o_idx - 12), o_idx)]
                                if prev_lows and ob_l <= min(prev_lows) * 1.001:
                                    has_sweep = True

                            if not any(z["origin_time"] == o_c["time"] and z["side"] == "BUY" for z in active_zones):
                                active_zones.append({
                                    "symbol": sym,
                                    "side": "BUY",
                                    "origin_time": o_c["time"],
                                    "disp_time": c["time"],
                                    "ob_high": ob_h,
                                    "ob_low": ob_l,
                                    "target_qual": target_q,
                                    "has_sweep": has_sweep,
                                    "status": "PENDING",
                                    "entry_price": None,
                                    "entry_time": None,
                                    "be_activated": False
                                })
                
                # Update zone status
                for z in list(active_zones):
                    if z["status"] == "PENDING":
                        if c["low"] <= z["ob_low"]:
                            z["status"] = "INVALIDATED"
                        elif c["high"] >= z["target_qual"]:
                            z["status"] = "QUALIFIED"
                            
                    elif z["status"] == "QUALIFIED":
                        # Strictly check for BUY 3-OB structure with Sweep Confluence
                        side_zones = [sz for sz in active_zones if sz["side"] == "BUY" and sz["status"] in ("QUALIFIED", "ACTIVE")]
                        side_zones.sort(key=lambda x: x["ob_high"], reverse=True)
                        
                        # 3-OB Middle Sandwich Condition + Sweep Confluence
                        is_middle_2nd_ob = (len(side_zones) >= 3 and z["origin_time"] == side_zones[1]["origin_time"])
                        is_valid_setup = is_middle_2nd_ob or (len(side_zones) >= 2 and z["origin_time"] == side_zones[1]["origin_time"] and z["has_sweep"])
                        
                        if c["low"] <= z["ob_high"]:
                            if is_valid_setup:
                                z["status"] = "ACTIVE"
                                z["entry_price"] = z["ob_high"]
                                z["entry_time"] = c["time"]
                                z["tp_price"] = z["entry_price"] * (1.0 + tp_pct)
                                z["sl_price"] = z["entry_price"] * (1.0 - sl_pct)
                                z["be_trigger_price"] = z["entry_price"] * (1.0 + be_pct)
                            else:
                                z["status"] = "MITIGATED"
                                
                    elif z["status"] == "ACTIVE":
                        ep = z["entry_price"]
                        tp = z["tp_price"]
                        sl = z["sl_price"]
                        be_trig = z["be_trigger_price"]
                        
                        # Check Breakeven Trigger
                        if not z["be_activated"] and c["high"] >= be_trig:
                            z["be_activated"] = True
                            
                        # Check TP Hit
                        if c["high"] >= tp:
                            z["status"] = "TP_HIT"
                            completed_trades.append({
                                "time": c["time"],
                                "symbol": sym,
                                "side": "BUY",
                                "result": "WIN",
                                "entry_price": ep,
                                "exit_price": tp,
                                "pnl_pct": cfg["tp_roe"]
                            })
                        else:
                            # Check SL / Breakeven Hit
                            if use_close_sl:
                                # 4H: SL is evaluated on Candle Close (Soft SL)
                                sl_hit_condition = (c["close"] <= sl) if not z["be_activated"] else (c["low"] <= ep)
                            else:
                                # 1H: 2-Layer Hybrid SL
                                sl_hit_condition = (c["low"] <= sl) if not z["be_activated"] else (c["low"] <= ep)
                                
                            if sl_hit_condition:
                                if z["be_activated"]:
                                    z["status"] = "BE_HIT"
                                    completed_trades.append({
                                        "time": c["time"],
                                        "symbol": sym,
                                        "side": "BUY",
                                        "result": "BE",
                                        "entry_price": ep,
                                        "exit_price": ep,
                                        "pnl_pct": 0.0
                                    })
                                else:
                                    z["status"] = "SL_HIT"
                                    completed_trades.append({
                                        "time": c["time"],
                                        "symbol": sym,
                                        "side": "BUY",
                                        "result": "LOSS",
                                        "entry_price": ep,
                                        "exit_price": sl,
                                        "pnl_pct": -cfg["sl_roe"]
                                    })
                                    
                active_zones = [z for z in active_zones if z["status"] in ("PENDING", "QUALIFIED", "ACTIVE")]

        completed_trades.sort(key=lambda x: x["time"])
        target_100 = completed_trades[:100]
        total_count = len(target_100)
        
        wins = [t for t in target_100 if t["result"] == "WIN"]
        bes = [t for t in target_100 if t["result"] == "BE"]
        losses = [t for t in target_100 if t["result"] == "LOSS"]
        
        win_count = len(wins)
        be_count = len(bes)
        loss_count = len(losses)
        
        win_rate = (win_count / total_count * 100) if total_count > 0 else 0
        be_rate = (be_count / total_count * 100) if total_count > 0 else 0
        loss_rate = (loss_count / total_count * 100) if total_count > 0 else 0
        safety_rate = ((win_count + be_count) / total_count * 100) if total_count > 0 else 0
        
        balance = 50.0
        peak_balance = balance
        max_drawdown = 0.0
        
        trade_logs = []
        for i, t in enumerate(target_100, 1):
            pnl_amt = balance * t["pnl_pct"]
            balance += pnl_amt
            if balance > peak_balance:
                peak_balance = balance
            dd = (peak_balance - balance) / peak_balance * 100
            if dd > max_drawdown:
                max_drawdown = dd
            
            trade_logs.append({
                "trade_no": i,
                "time": t["time"],
                "symbol": t["symbol"],
                "side": t["side"],
                "entry_price": t["entry_price"],
                "exit_price": t["exit_price"],
                "result": t["result"],
                "pnl_roe": t["pnl_pct"] * 100,
                "balance": balance
            })
                
        all_results[tf] = {
            "total_trades": total_count,
            "wins": win_count,
            "win_rate": win_rate,
            "breakevens": be_count,
            "be_rate": be_rate,
            "losses": loss_count,
            "loss_rate": loss_rate,
            "safety_rate": safety_rate,
            "start_balance": 50.0,
            "final_balance": balance,
            "max_drawdown": max_drawdown,
            "trades": trade_logs
        }
        
    await binance_feed.close()
    
    print("\n" + "=" * 80)
    print("   EXACT HANDWRITTEN SETUP (SWEEP + 2ND OB BUY) - 100 TRADES SUMMARY")
    print("=" * 80)
    
    for tf, data in all_results.items():
        print(f"\n========================== [ TIMEFRAME: {tf.upper()} ] ==========================")
        print(f"• Total Executed Trades  : {data['total_trades']}")
        print(f"• Direct Wins (Hit TP)   : {data['wins']} ({data['win_rate']:.1f}%)")
        print(f"• Breakeven Exits ($0)   : {data['breakevens']} ({data['be_rate']:.1f}%)")
        print(f"• Losses (Hit SL)        : {data['losses']} ({data['loss_rate']:.1f}%)")
        print(f"• Capital Safety Rate    : {data['safety_rate']:.1f}% (Wins + BEs with $0 Loss)")
        print(f"• Starting Balance       : ${data['start_balance']:.2f} USDT")
        print(f"• Final Balance (100 Tr) : ${data['final_balance']:,.2f} USDT")
        print(f"• Max Drawdown           : {data['max_drawdown']:.2f}%")
        
        print("\n--- Recent 10 Trades Sample ---")
        print(f"{'Tr#':<4} | {'Symbol':<12} | {'Side':<4} | {'Entry Price':<12} | {'Exit Price':<12} | {'Result':<6} | {'ROE %':<8} | {'Balance'}")
        print("-" * 80)
        for tr in data["trades"][-10:]:
            print(f"{tr['trade_no']:<4} | {tr['symbol']:<12} | {tr['side']:<4} | {tr['entry_price']:<12.4f} | {tr['exit_price']:<12.4f} | {tr['result']:<6} | {tr['pnl_roe']:+6.2f}% | ${tr['balance']:,.2f}")

if __name__ == "__main__":
    asyncio.run(run_exact_handwritten_backtest())
