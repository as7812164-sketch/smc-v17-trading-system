import asyncio
import time
import sys
from datetime import datetime, timezone, timedelta
from feed.binance_feed import binance_feed
from engine.smc_v17 import calculate_avg_body, find_true_origin
from config import DEFAULT_COINS, TIER1_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IST = timezone(timedelta(hours=5, minutes=30))

async def analyze_duration():
    coins = list(dict.fromkeys(TIER1_COINS + DEFAULT_COINS))
    
    configs = [
        {"tf": "1h", "qual_pct": 0.025, "tp_pct": 0.0150, "sl_pct": 0.0200, "be_pct": 0.0075, "use_candle_close_sl": False},
        {"tf": "4h", "qual_pct": 0.040, "tp_pct": 0.0204, "sl_pct": 0.0250, "be_pct": 0.0102, "use_candle_close_sl": True}
    ]
    
    print("================================================================================")
    print("      100 TRADES DURATION & FREQUENCY ANALYSIS (1H vs 4H)")
    print("================================================================================")
    
    for cfg in configs:
        tf = cfg["tf"]
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
                if avg_b > 0:
                    c_body = abs(c["close"] - c["open"])
                    if c["close"] > c["open"] and c_body >= 1.4 * avg_b:
                        o_idx = find_true_origin(candles, cur_idx, "BUY")
                        if o_idx is not None:
                            o_c = candles[o_idx]
                            ob_h = o_c["high"]
                            ob_l = o_c["low"]
                            target_q = ob_h * (1.0 + cfg["qual_pct"])
                            has_sweep = False
                            if o_idx >= 3:
                                prev_lows = [candles[k]["low"] for k in range(max(0, o_idx - 12), o_idx)]
                                if prev_lows and ob_l <= min(prev_lows) * 1.001:
                                    has_sweep = True
                            if not any(z["origin_time"] == o_c["time"] and z["side"] == "BUY" for z in active_zones):
                                active_zones.append({
                                    "symbol": sym, "side": "BUY", "origin_time": o_c["time"],
                                    "ob_high": ob_h, "ob_low": ob_l, "target_qual": target_q,
                                    "has_sweep": has_sweep, "status": "PENDING",
                                    "entry_price": None, "entry_time": None, "be_activated": False
                                })
                                
                for z in list(active_zones):
                    if z["status"] == "PENDING":
                        if c["low"] <= z["ob_low"]:
                            z["status"] = "INVALIDATED"
                        elif c["high"] >= z["target_qual"]:
                            z["status"] = "QUALIFIED"
                    elif z["status"] == "QUALIFIED":
                        side_zones = [sz for sz in active_zones if sz["side"] == "BUY" and sz["status"] in ("QUALIFIED", "ACTIVE")]
                        side_zones.sort(key=lambda x: x["ob_high"], reverse=True)
                        is_middle_2nd_ob = (len(side_zones) >= 3 and z["origin_time"] == side_zones[1]["origin_time"])
                        is_valid_setup = is_middle_2nd_ob or (len(side_zones) >= 2 and z["origin_time"] == side_zones[1]["origin_time"] and z["has_sweep"])
                        
                        if c["low"] <= z["ob_high"]:
                            if is_valid_setup:
                                z["status"] = "ACTIVE"
                                z["entry_price"] = z["ob_high"]
                                z["entry_time"] = c["time"]
                                z["tp_price"] = z["entry_price"] * (1.0 + cfg["tp_pct"])
                                z["sl_price"] = z["entry_price"] * (1.0 - cfg["sl_pct"])
                                z["be_trigger_price"] = z["entry_price"] * (1.0 + cfg["be_pct"])
                            else:
                                z["status"] = "MITIGATED"
                    elif z["status"] == "ACTIVE":
                        ep = z["entry_price"]
                        tp = z["tp_price"]
                        sl = z["sl_price"]
                        be_trig = z["be_trigger_price"]
                        if not z["be_activated"] and c["high"] >= be_trig:
                            z["be_activated"] = True
                        if c["high"] >= tp:
                            z["status"] = "TP_HIT"
                            completed_trades.append({
                                "entry_time": z["entry_time"],
                                "exit_time": c["time"],
                                "symbol": sym, "result": "WIN"
                            })
                        else:
                            sl_hit_condition = (c["close"] <= sl) if cfg["use_candle_close_sl"] and not z["be_activated"] else ((c["low"] <= ep) if z["be_activated"] else (c["low"] <= sl))
                            if sl_hit_condition:
                                if z["be_activated"]:
                                    z["status"] = "BE_HIT"
                                    completed_trades.append({
                                        "entry_time": z["entry_time"],
                                        "exit_time": c["time"],
                                        "symbol": sym, "result": "BE"
                                    })
                                else:
                                    z["status"] = "SL_HIT"
                                    completed_trades.append({
                                        "entry_time": z["entry_time"],
                                        "exit_time": c["time"],
                                        "symbol": sym, "result": "LOSS"
                                    })
                active_zones = [z for z in active_zones if z["status"] in ("PENDING", "QUALIFIED", "ACTIVE")]
                
        completed_trades.sort(key=lambda x: x["exit_time"])
        target_100 = completed_trades[:100]
        
        t_first = target_100[0]["entry_time"] / 1000.0
        t_last = target_100[-1]["exit_time"] / 1000.0
        
        dt_first = datetime.fromtimestamp(t_first, tz=IST)
        dt_last = datetime.fromtimestamp(t_last, tz=IST)
        
        duration_delta = dt_last - dt_first
        total_days = duration_delta.total_seconds() / 86400.0
        trades_per_day = len(target_100) / total_days if total_days > 0 else 0
        
        # Average holding duration per trade
        durations_hrs = [(t["exit_time"] - t["entry_time"]) / (1000.0 * 3600.0) for t in target_100]
        avg_trade_hrs = sum(durations_hrs) / len(durations_hrs) if durations_hrs else 0
        
        print(f"\n📊 --- [ TIMEFRAME: {tf.upper()} ] ---")
        print(f"• 1st Trade Start Date   : {dt_first.strftime('%d %b %Y, %I:%M %p IST')}")
        print(f"• 100th Trade Exit Date  : {dt_last.strftime('%d %b %Y, %I:%M %p IST')}")
        print(f"• Total Time Duration    : {total_days:.1f} Days ({total_days / 30.4:.1f} Months)")
        print(f"• Average Trade Velocity : {trades_per_day:.2f} Trades / Day (~{trades_per_day * 7:.1f} Trades / Week)")
        print(f"• Avg Holding Duration   : {avg_trade_hrs:.1f} Hours per trade")
        
    await binance_feed.close()

if __name__ == "__main__":
    asyncio.run(analyze_duration())
