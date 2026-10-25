import urllib.request
import json
import datetime
import time
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT', 
    'AVAXUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'NEARUSDT', 
    'SUIUSDT', 'APTUSDT', 'TIAUSDT', 'ARBUSDT', 'OPUSDT', 
    'FILUSDT', 'JASMYUSDT', 'AXSUSDT', 'FETUSDT'
]

def fetch_klines(symbol, limit=750):
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1h&limit={limit}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return data
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []

def calculate_atr(candles, period=14):
    atrs = [0.0] * len(candles)
    for i in range(1, len(candles)):
        h = float(candles[i][2])
        l = float(candles[i][3])
        prev_c = float(candles[i-1][4])
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        if i < period:
            atrs[i] = tr
        elif i == period:
            trs = [max(float(candles[k][2]) - float(candles[k][3]), 
                       abs(float(candles[k][2]) - float(candles[k-1][4])), 
                       abs(float(candles[k][3]) - float(candles[k-1][4]))) for k in range(1, period+1)]
            atrs[i] = sum(trs) / period
        else:
            atrs[i] = (atrs[i-1] * (period - 1) + tr) / period
    return atrs

def calculate_sma_vol(candles, period=20):
    sma = [0.0] * len(candles)
    for i in range(len(candles)):
        if i >= period:
            vols = [float(candles[k][5]) for k in range(i-period, i)]
            sma[i] = sum(vols) / period
        else:
            vols = [float(candles[k][5]) for k in range(0, i+1)]
            sma[i] = sum(vols) / len(vols) if vols else 1.0
    return sma

def run_backtest_for_symbol(symbol, candles):
    if len(candles) < 100:
        return []
        
    atrs = calculate_atr(candles, 14)
    avg_vols = calculate_sma_vol(candles, 20)
    
    leverage = 5.0
    tp_roe = 12.20
    sl_roe = 12.00
    
    tp_pct = (tp_roe / 100.0) / leverage # +2.44%
    sl_pct = (sl_roe / 100.0) / leverage # -2.40%
    
    active_unmitigated = [] # list of dicts
    active_in_trade = []
    closed_trades = []
    
    max_active_zones = 4
    ai_min_score = 70
    
    for i in range(25, len(candles)):
        current_candle = candles[i]
        c_open = float(current_candle[1])
        c_high = float(current_candle[2])
        c_low = float(current_candle[3])
        c_close = float(current_candle[4])
        c_time = datetime.datetime.fromtimestamp(current_candle[0]/1000)
        
        # 1. Evaluate OB Qualification at candle i-3
        c3 = candles[i-3]
        o3, h3, l3, cl3 = float(c3[1]), float(c3[2]), float(c3[3]), float(c3[4])
        v3 = float(c3[5])
        
        c2 = candles[i-2]
        c1 = candles[i-1]
        h1, l1, v1 = float(c1[2]), float(c1[3]), float(c1[5])
        h2, l2, v2 = float(c2[2]), float(c2[3]), float(c2[5])
        
        atr_val = atrs[i]
        avg_vol = avg_vols[i]
        
        impulse_h = max(h1, h2)
        impulse_l = min(l1, l2)
        impulse_v = max(v1, v2)
        vol_ratio = impulse_v / avg_vol if avg_vol > 0 else 1.0
        
        has_bull_fvg = (l1 > h3)
        has_bear_fvg = (h1 < l3)
        
        # Strict Red Candle for Bull, Strict Green for Bear
        is_strict_red = (cl3 < o3)
        is_strict_green = (cl3 > o3)
        
        bull_expansion = impulse_h - l3
        bear_expansion = h3 - impulse_l
        bull_atr_ratio = (bull_expansion / atr_val) if atr_val > 0 else 0
        bear_atr_ratio = (bear_expansion / atr_val) if atr_val > 0 else 0
        
        # Scoring
        if is_strict_red and has_bull_fvg:
            score = 30 # FVG
            if bull_atr_ratio >= 3.0: score += 40
            elif bull_atr_ratio >= 2.0: score += 35
            elif bull_atr_ratio >= 1.5: score += 25
            elif bull_atr_ratio >= 1.0: score += 15
            
            if vol_ratio >= 1.8: score += 20
            elif vol_ratio >= 1.3: score += 15
            elif vol_ratio >= 1.0: score += 10
            
            if l3 <= float(candles[i-4][3]) or l3 == min([float(candles[k][3]) for k in range(i-6, i)]):
                score += 10
                
            if score >= ai_min_score and bull_atr_ratio >= 1.3:
                # Add Bullish OB
                ob = {
                    'symbol': symbol,
                    'side': 'LONG',
                    'start_idx': i-3,
                    'ob_high': h3,
                    'ob_low': l3,
                    'entry_price': h3, # OB Boundary Entry!
                    'tp_price': h3 * (1.0 + tp_pct),
                    'sl_price': h3 * (1.0 - sl_pct),
                    'ai_score': score,
                    'created_time': str(datetime.datetime.fromtimestamp(c3[0]/1000))
                }
                active_unmitigated.append(ob)
                if len(active_unmitigated) > max_active_zones:
                    active_unmitigated.pop(0) # Keep newest max_active_zones
                    
        if is_strict_green and has_bear_fvg:
            score = 30 # FVG
            if bear_atr_ratio >= 3.0: score += 40
            elif bear_atr_ratio >= 2.0: score += 35
            elif bear_atr_ratio >= 1.5: score += 25
            elif bear_atr_ratio >= 1.0: score += 15
            
            if vol_ratio >= 1.8: score += 20
            elif vol_ratio >= 1.3: score += 15
            elif vol_ratio >= 1.0: score += 10
            
            if h3 >= float(candles[i-4][2]) or h3 == max([float(candles[k][2]) for k in range(i-6, i)]):
                score += 10
                
            if score >= ai_min_score and bear_atr_ratio >= 1.3:
                # Add Bearish OB
                ob = {
                    'symbol': symbol,
                    'side': 'SHORT',
                    'start_idx': i-3,
                    'ob_high': h3,
                    'ob_low': l3,
                    'entry_price': l3, # OB Boundary Entry!
                    'tp_price': l3 * (1.0 - tp_pct),
                    'sl_price': l3 * (1.0 + sl_pct),
                    'ai_score': score,
                    'created_time': str(datetime.datetime.fromtimestamp(c3[0]/1000))
                }
                active_unmitigated.append(ob)
                if len(active_unmitigated) > max_active_zones:
                    active_unmitigated.pop(0)

        # 2. Check Active In-Trade Positions (NO BREAKEVEN ARMOR)
        still_in_trade = []
        for tr in active_in_trade:
            if tr['side'] == 'LONG':
                # Check conservative: if both hit in same candle, SL takes precedence
                if c_low <= tr['sl_price'] and c_high >= tr['tp_price']:
                    tr['exit_price'] = tr['sl_price']
                    tr['result'] = 'SL_HIT'
                    tr['roe'] = -sl_roe
                    tr['exit_time'] = str(c_time)
                    closed_trades.append(tr)
                elif c_high >= tr['tp_price']:
                    tr['exit_price'] = tr['tp_price']
                    tr['result'] = 'TP_HIT'
                    tr['roe'] = tp_roe
                    tr['exit_time'] = str(c_time)
                    closed_trades.append(tr)
                elif c_low <= tr['sl_price']:
                    tr['exit_price'] = tr['sl_price']
                    tr['result'] = 'SL_HIT'
                    tr['roe'] = -sl_roe
                    tr['exit_time'] = str(c_time)
                    closed_trades.append(tr)
                else:
                    still_in_trade.append(tr)
                    
            elif tr['side'] == 'SHORT':
                if c_high >= tr['sl_price'] and c_low <= tr['tp_price']:
                    tr['exit_price'] = tr['sl_price']
                    tr['result'] = 'SL_HIT'
                    tr['roe'] = -sl_roe
                    tr['exit_time'] = str(c_time)
                    closed_trades.append(tr)
                elif c_low <= tr['tp_price']:
                    tr['exit_price'] = tr['tp_price']
                    tr['result'] = 'TP_HIT'
                    tr['roe'] = tp_roe
                    tr['exit_time'] = str(c_time)
                    closed_trades.append(tr)
                elif c_high >= tr['sl_price']:
                    tr['exit_price'] = tr['sl_price']
                    tr['result'] = 'SL_HIT'
                    tr['roe'] = -sl_roe
                    tr['exit_time'] = str(c_time)
                    closed_trades.append(tr)
                else:
                    still_in_trade.append(tr)
                    
        active_in_trade = still_in_trade
        
        # 3. Check 1st Tap on Active Unmitigated Zones
        still_unmitigated = []
        for ob in active_unmitigated:
            if ob['side'] == 'LONG':
                # Invalidation: candle close below OB low before any tap
                if c_close < ob['ob_low']:
                    continue # invalidated and dropped
                    
                # 1st Tap: low touches ob_high (boundary entry) and holds above sl_price
                tapped = (c_low <= ob['ob_high'] and c_low > ob['sl_price'] and c_close >= ob['ob_low'])
                if tapped and len(active_in_trade) == 0: # 1 trade at a time per asset
                    trade = dict(ob)
                    trade['entry_time'] = str(c_time)
                    active_in_trade.append(trade)
                else:
                    still_unmitigated.append(ob)
                    
            elif ob['side'] == 'SHORT':
                if c_close > ob['ob_high']:
                    continue # invalidated and dropped
                    
                tapped = (c_high >= ob['ob_low'] and c_high < ob['sl_price'] and c_close <= ob['ob_high'])
                if tapped and len(active_in_trade) == 0:
                    trade = dict(ob)
                    trade['entry_time'] = str(c_time)
                    active_in_trade.append(trade)
                else:
                    still_unmitigated.append(ob)
                    
        active_unmitigated = still_unmitigated
        
    return closed_trades

def main():
    print("="*80)
    print("HERMES AI ZEN SNIPER - 1-MONTH BACKTEST AUDIT (WITHOUT BREAKEVEN / PURE BINARY TP vs SL)")
    print("Parameters: 4 Unmitigated Zones | OB Boundary Entry | Strict Candle Color Gate | 5x Lev")
    print("Targets: Pure +12.20% ROE TP vs -12.00% ROE SL (NO BE ARMOR)")
    print("="*80)
    
    all_trades = []
    symbol_stats = {}
    
    for s in SYMBOLS:
        print(f"Fetching 30-day 1H data for {s}...")
        candles = fetch_klines(s, 720)
        time.sleep(0.1)
        trades = run_backtest_for_symbol(s, candles)
        all_trades.extend(trades)
        
        wins = [t for t in trades if t['result'] == 'TP_HIT']
        losses = [t for t in trades if t['result'] == 'SL_HIT']
        total = len(trades)
        
        win_rate = (len(wins) / total * 100.0) if total > 0 else 0.0
        net_roe = sum(t['roe'] for t in trades)
        
        symbol_stats[s] = {
            'total': total,
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': win_rate,
            'net_roe': net_roe
        }
        print(f"  --> {s}: {total} Trades | {len(wins)}W {len(losses)}L | WinRate: {win_rate:.1f}% | Net ROE: {net_roe:+.1f}%")
        
    print("\n" + "="*80)
    print("OVERALL 1-MONTH PERFORMANCE SUMMARY (WITHOUT BREAKEVEN)")
    print("="*80)
    
    total_trades = len(all_trades)
    all_wins = [t for t in all_trades if t['result'] == 'TP_HIT']
    all_losses = [t for t in all_trades if t['result'] == 'SL_HIT']
    
    pure_win_rate = (len(all_wins) / total_trades * 100.0) if total_trades > 0 else 0
    total_net_roe = sum(t['roe'] for t in all_trades)
    
    gross_profit = sum(t['roe'] for t in all_wins)
    gross_loss = abs(sum(t['roe'] for t in all_losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 999.0
    
    print(f"Total Trades Executed:       {total_trades}")
    print(f"Take Profit Hits (Wins):     {len(all_wins)}")
    print(f"Hard Stop Loss Hits:         {len(all_losses)}")
    print(f"Pure Win Rate:               {pure_win_rate:.2f}%")
    print(f"Total Cumulative ROE:        {total_net_roe:+.2f}%")
    print(f"Profit Factor:               {profit_factor:.2f}")
    print("="*80)
    
    # Save detailed JSON report
    with open('hermes_zen_sniper_no_be_audit_result.json', 'w') as f:
        json.dump({
            'total_trades': total_trades,
            'wins': len(all_wins),
            'losses': len(all_losses),
            'pure_win_rate': pure_win_rate,
            'total_net_roe': total_net_roe,
            'profit_factor': profit_factor,
            'symbol_stats': symbol_stats,
            'trades': all_trades
        }, f, indent=2)
    print("Audit report saved to hermes_zen_sniper_no_be_audit_result.json")

if __name__ == '__main__':
    main()
