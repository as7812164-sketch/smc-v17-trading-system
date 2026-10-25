import asyncio
import sys
import numpy as np
from feed.binance_feed import binance_feed
from engine.smc_v17 import analyze_candles_smc_v17
from config import TIER1_COINS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def backtest_engine(tf: str, tp_pct: float, soft_sl_pct: float, breakeven_pct: float, leverage: int = 5, start_cap: float = 50.0):
    print(f"\n==========================================================================")
    print(f"   TESTING TIMEFRAME: {tf.upper()} (Leverage: {leverage}x Isolated | TP: +{tp_pct*100:.1f}% | Soft SL: -{soft_sl_pct*100:.1f}%)")
    print(f"==========================================================================")
    
    # Fetch 1000 candles across Tier 1 coins
    all_trades = []
    
    for sym in TIER1_COINS:
        try:
            candles = await binance_feed.fetch_klines(sym, interval=tf, limit=500)
            if not candles or len(candles) < 100:
                continue
            
            # Analyze zones
            zones = analyze_candles_smc_v17(sym, candles)
            
            for z in zones:
                if z.get("qualified") != 1:
                    continue
                
                side = z["side"]
                entry_p = float(z.get("entry_price") or (z["ob_high"] if side == "BUY" else z["ob_low"]))
                qual_time = z.get("qualified_time", 0)
                
                # Find entry candle index
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
                    
                # Track lifecycle candle by candle (Hybrid Candle Close SL + Breakeven + TP)
                trade_result = None
                be_active = False
                bars_in_trade = 0
                
                tp_target = entry_p * (1.0 + tp_pct) if side == "BUY" else entry_p * (1.0 - tp_pct)
                soft_sl = entry_p * (1.0 - soft_sl_pct) if side == "BUY" else entry_p * (1.0 + soft_sl_pct)
                be_trigger = entry_p * (1.0 + breakeven_pct) if side == "BUY" else entry_p * (1.0 - breakeven_pct)
                
                for k in range(entry_idx, len(candles)):
                    c = candles[k]
                    bars_in_trade += 1
                    
                    # 1. Check Breakeven Trigger
                    if not be_active:
                        if side == "BUY" and c["high"] >= be_trigger:
                            be_active = True
                        elif side == "SELL" and c["low"] <= be_trigger:
                            be_active = True
                            
                    # 2. Check TP Hit
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
                        "time": candles[entry_idx]["time"],
                        "result": trade_result,
                        "bars": bars_in_trade
                    })
        except Exception as e:
            pass
            
    # Sort chronological
    all_trades.sort(key=lambda x: x["time"])
    
    total = len(all_trades)
    if total == 0:
        print("No completed trades found in sample window.")
        return
        
    wins = len([t for t in all_trades if t["result"] == "WIN"])
    bes = len([t for t in all_trades if t["result"] == "BREAKEVEN"])
    losses = len([t for t in all_trades if t["result"] == "LOSS"])
    
    # Effective Win Rate (Non-losing rate)
    win_rate = (wins / total) * 100
    safe_rate = ((wins + bes) / total) * 100
    avg_bars = np.mean([t["bars"] for t in all_trades])
    
    bar_hours = 1.0 if tf == "1h" else 4.0
    avg_time_hours = avg_bars * bar_hours
    
    print(f"Total Evaluated Setups: {total}")
    print(f"Take Profit Wins (TP Hit):  {wins:4d} ({win_rate:5.1f}%)")
    print(f"Breakeven Exits ($0 Loss):  {bes:4d} ({(bes/total)*100:5.1f}%)")
    print(f"Stop Loss Exits (Soft SL):  {losses:4d} ({(losses/total)*100:5.1f}%)")
    print(f"Capital Preservation Rate:  {safe_rate:5.1f}% (Wins + Zero Loss Breakevens)")
    print(f"Average Trade Duration:     {avg_time_hours:.1f} Hours ({avg_bars:.1f} candles)")
    
    # Run 100-Trade Sequential Compounding Simulation
    print(f"\n--- 100-TRADE COMPOUNDING SIMULATION ($50 Starting Capital) ---")
    
    # Take first 100 sequential trades from dataset (or sample with exact distribution)
    np.random.seed(42)
    sample_100 = all_trades[:100] if len(all_trades) >= 100 else [np.random.choice(all_trades) for _ in range(100)]
    
    balance = start_cap
    compounding_ledger = []
    days_elapsed = 0.0
    
    roe_gain = tp_pct * leverage  # e.g. +7.5% or +10%
    roe_loss = soft_sl_pct * leverage # e.g. -12.5% or -10%
    
    peak_balance = balance
    max_drawdown_pct = 0.0
    
    milestone_500_trade = None
    milestone_1000_trade = None
    
    for idx, t in enumerate(sample_100, 1):
        res = t["result"]
        duration_hrs = t["bars"] * bar_hours
        days_elapsed += duration_hrs / 24.0
        
        prev_bal = balance
        if res == "WIN":
            # 100% Compounding: profit added to equity
            profit = balance * roe_gain
            balance += profit
        elif res == "BREAKEVEN":
            profit = 0.0
        else: # LOSS
            loss = balance * roe_loss
            balance = max(10.0, balance - loss)
            
        if balance > peak_balance:
            peak_balance = balance
        dd = ((peak_balance - balance) / peak_balance) * 100
        if dd > max_drawdown_pct:
            max_drawdown_pct = dd
            
        if balance >= 500.0 and milestone_500_trade is None:
            milestone_500_trade = (idx, round(days_elapsed, 1), round(balance, 2))
        if balance >= 1000.0 and milestone_1000_trade is None:
            milestone_1000_trade = (idx, round(days_elapsed, 1), round(balance, 2))
            
    print(f"Initial Starting Capital:   ${start_cap:.2f} USDT")
    print(f"Final Balance after 100 Trades: ${balance:.2f} USDT")
    print(f"Total Multiplier Growth:    {balance/start_cap:.1f}x")
    print(f"Max Drawdown during Journey:{max_drawdown_pct:.1f}%")
    print(f"Estimated Real Timeline:    {days_elapsed:.1f} Days (~{days_elapsed/7:.1f} Weeks)")
    if milestone_500_trade:
        print(f"🎯 $500 Milestone reached at Trade #{milestone_500_trade[0]} (Day {milestone_500_trade[1]}) -> ${milestone_500_trade[2]}")
    if milestone_1000_trade:
        print(f"🏆 $1,000 Milestone reached at Trade #{milestone_1000_trade[0]} (Day {milestone_1000_trade[1]}) -> ${milestone_1000_trade[2]}")

async def main():
    print("==========================================================================")
    print("   QUANTITATIVE VERIFICATION: HYBRID CANDLE-CLOSE + SMC V17 ACCURACY")
    print("==========================================================================")
    
    # 1. Binance Engine (1H Fast Scalp: TP +1.5%, Soft SL -2.5%, Breakeven +0.8%)
    await backtest_engine(
        tf="1h",
        tp_pct=0.015,
        soft_sl_pct=0.025,
        breakeven_pct=0.008,
        leverage=5,
        start_cap=50.0
    )
    
    # 2. Bitget Engine (4H Macro Swing: TP +2.0%, Soft SL -2.0%, Breakeven +1.0%)
    await backtest_engine(
        tf="4h",
        tp_pct=0.020,
        soft_sl_pct=0.020,
        breakeven_pct=0.010,
        leverage=5,
        start_cap=50.0
    )
    
    await binance_feed.close()

if __name__ == "__main__":
    asyncio.run(main())
