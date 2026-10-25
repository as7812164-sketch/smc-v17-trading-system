import asyncio
import sys
import numpy as np
from feed.binance_feed import binance_feed
from engine.smc_v17 import analyze_candles_smc_v17, filter_active_zones
from config import TIER1_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def run_strict_2nd_ob_backtest(tf: str, tp_pct: float, soft_sl_pct: float, be_trigger_pct: float, leverage: int = 5, start_cap: float = 50.0):
    print(f"\n=========================================================================================")
    print(f"   STRICT 2nd OB INDICATOR BACKTEST: {tf.upper()} (TP: +{tp_pct*100:.1f}% | BE: +{be_trigger_pct*100:.1f}% | Soft SL: -{soft_sl_pct*100:.1f}%)")
    print(f"=========================================================================================")
    
    all_trades = []
    
    # Batch fetch klines
    all_klines = await binance_feed.fetch_multiple_symbols(TIER1_COINS, interval=tf, limit=500)
    
    for sym, candles in all_klines.items():
        if not candles or len(candles) < 60:
            continue
            
        zones = analyze_candles_smc_v17(sym, candles)
        # Group all qualified zones
        buy_zones = [z for z in zones if z["side"] == "BUY" and z.get("qualified") == 1]
        sell_zones = [z for z in zones if z["side"] == "SELL" and z.get("qualified") == 1]
        
        buy_zones.sort(key=lambda x: x["ob_high"], reverse=True)
        sell_zones.sort(key=lambda x: x["ob_low"])
        
        target_zones = []
        if buy_zones:
            # 2nd OB if >=2 exist, else 1st OB
            target_zones.append((buy_zones[1] if len(buy_zones) >= 2 else buy_zones[0], "2nd OB" if len(buy_zones) >= 2 else "1st OB"))
        if sell_zones:
            target_zones.append((sell_zones[1] if len(sell_zones) >= 2 else sell_zones[0], "2nd OB" if len(sell_zones) >= 2 else "1st OB"))
            
        for z, ob_tag in target_zones:
            side = z["side"]
            entry_p = z["ob_high"] if side == "BUY" else z["ob_low"]
            qual_time = z.get("qualified_time", 0)
            
            # Find entry bar
            entry_idx = -1
            for i, c in enumerate(candles):
                if c["time"] >= qual_time:
                    if side == "BUY" and c["low"] <= entry_p:
                        entry_idx = i
                        break
                    elif side == "SELL" and c["high"] >= entry_p:
                        entry_idx = i
                        break
                        
            if entry_idx == -1 or entry_idx >= len(candles) - 1:
                continue
                
            tp_target = entry_p * (1.0 + tp_pct) if side == "BUY" else entry_p * (1.0 - tp_pct)
            soft_sl = entry_p * (1.0 - soft_sl_pct) if side == "BUY" else entry_p * (1.0 + soft_sl_pct)
            be_target = entry_p * (1.0 + be_trigger_pct) if side == "BUY" else entry_p * (1.0 - be_trigger_pct)
            
            trade_result = None
            be_active = False
            bars_in_trade = 0
            
            for k in range(entry_idx, len(candles)):
                c = candles[k]
                bars_in_trade += 1
                
                # 1. Check Breakeven Trigger
                if not be_active:
                    if side == "BUY" and c["high"] >= be_target:
                        be_active = True
                    elif side == "SELL" and c["low"] <= be_target:
                        be_active = True
                        
                # 2. Check Take Profit Hit
                if side == "BUY" and c["high"] >= tp_target:
                    trade_result = "WIN"
                    break
                elif side == "SELL" and c["low"] <= tp_target:
                    trade_result = "WIN"
                    break
                    
                # 3. Check Breakeven Stop Hit
                if be_active:
                    if side == "BUY" and c["low"] <= entry_p:
                        trade_result = "BREAKEVEN"
                        break
                    elif side == "SELL" and c["high"] >= entry_p:
                        trade_result = "BREAKEVEN"
                        break
                        
                # 4. Check Candle Close SL (Soft SL confirmed on CLOSE only!)
                if side == "BUY":
                    if c["close"] <= soft_sl:
                        trade_result = "LOSS"
                        break
                else: # SELL
                    if c["close"] >= soft_sl:
                        trade_result = "LOSS"
                        break
                        
            if trade_result:
                all_trades.append({
                    "symbol": sym,
                    "side": side,
                    "ob_tag": ob_tag,
                    "time": candles[entry_idx]["time"],
                    "result": trade_result,
                    "bars": bars_in_trade
                })
                
    all_trades.sort(key=lambda x: x["time"])
    total = len(all_trades)
    
    if total == 0:
        print("No trades found in test period.")
        return
        
    wins = len([t for t in all_trades if t["result"] == "WIN"])
    bes = len([t for t in all_trades if t["result"] == "BREAKEVEN"])
    losses = len([t for t in all_trades if t["result"] == "LOSS"])
    
    win_rate = (wins / total) * 100
    safe_rate = ((wins + bes) / total) * 100
    avg_bars = np.mean([t["bars"] for t in all_trades])
    bar_hrs = 1.0 if tf == "1h" else 4.0
    avg_hrs = avg_bars * bar_hrs
    
    print(f"Total 2nd OB Setups Evaluated: {total}")
    print(f"Take Profit Wins (TP Hit):    {wins:4d} ({win_rate:5.1f}%)")
    print(f"Breakeven Exits ($0 Loss):    {bes:4d} ({(bes/total)*100:5.1f}%)")
    print(f"Stop Loss Exits (Soft SL):    {losses:4d} ({(losses/total)*100:5.1f}%)")
    print(f"Capital Safety Rate:          {safe_rate:5.1f}% (Wins + $0 Loss Breakevens)")
    print(f"Average Duration to TP:       {avg_hrs:.1f} Hours ({avg_bars:.1f} candles)")
    
    # 100-Trade Exact Sequential Compounding Simulation
    print(f"\n--- 100-TRADE COMPOUNDING LEDGER ($50 Starting Capital) ---")
    np.random.seed(123)
    sample_100 = all_trades[:100] if len(all_trades) >= 100 else [np.random.choice(all_trades) for _ in range(100)]
    
    balance = start_cap
    days_elapsed = 0.0
    roe_gain = tp_pct * leverage
    roe_loss = soft_sl_pct * leverage
    
    m_500 = None
    m_1000 = None
    
    for idx, t in enumerate(sample_100, 1):
        res = t["result"]
        dur_hrs = t["bars"] * bar_hrs
        days_elapsed += dur_hrs / 24.0
        
        if res == "WIN":
            balance += balance * roe_gain
        elif res == "BREAKEVEN":
            pass
        else: # LOSS
            balance = max(10.0, balance - balance * roe_loss)
            
        if balance >= 500.0 and m_500 is None:
            m_500 = (idx, round(days_elapsed, 1), round(balance, 2))
        if balance >= 1000.0 and m_1000 is None:
            m_1000 = (idx, round(days_elapsed, 1), round(balance, 2))
            
    print(f"Starting Capital:             ${start_cap:.2f} USDT")
    print(f"Final Balance after 100 Trades: ${balance:.2f} USDT")
    print(f"Total Multiplier Growth:      {balance/start_cap:.1f}x")
    print(f"Estimated Real Timeline:      {days_elapsed:.1f} Days (~{days_elapsed/7:.1f} Weeks)")
    if m_500:
        print(f"🎯 $500 Milestone reached at Trade #{m_500[0]} (Day {m_500[1]}) -> ${m_500[2]}")
    if m_1000:
        print(f"🏆 $1,000 Goal reached at Trade #{m_1000[0]} (Day {m_1000[1]}) -> ${m_1000[2]}")

async def main():
    print("=========================================================================================")
    print("      REAL QUANTITATIVE BACKTEST: EXACT 2nd OB INDICATOR BEHAVIOR")
    print("=========================================================================================")
    
    # 1. Binance 1H 2nd OB Scalp
    await run_strict_2nd_ob_backtest(
        tf="1h",
        tp_pct=0.015,
        soft_sl_pct=0.025,
        be_trigger_pct=0.008,
        leverage=5,
        start_cap=50.0
    )
    
    # 2. Bitget 4H 2nd OB Swing
    await run_strict_2nd_ob_backtest(
        tf="4h",
        tp_pct=0.020,
        soft_sl_pct=0.020,
        be_trigger_pct=0.010,
        leverage=5,
        start_cap=50.0
    )
    
    await binance_feed.close()

if __name__ == "__main__":
    asyncio.run(main())
