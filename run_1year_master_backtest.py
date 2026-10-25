import os
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

# Top Vetted Champions available in 1-year dataset
CHAMPIONS = [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'AVAXUSDT', 'LINKUSDT', 
    'NEARUSDT', 'SUIUSDT', 'APTUSDT', 'TIAUSDT', 'ARBUSDT', 
    'OPUSDT', 'FILUSDT', 'AXSUSDT', 'FETUSDT', 'LDOUSDT', 'INJUSDT'
]

ALL_AVAILABLE = [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT', 
    'AVAXUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'NEARUSDT', 
    'SUIUSDT', 'APTUSDT', 'TIAUSDT', 'ARBUSDT', 'OPUSDT', 
    'FILUSDT', 'AXSUSDT', 'FETUSDT', 'LDOUSDT', 'INJUSDT',
    'AAVEUSDT', 'RENDERUSDT', 'RUNEUSDT', 'PEPEUSDT'
]

def load_candles_1y(symbol):
    fname = f"historical_data/{symbol}_1h.json"
    if not os.path.exists(fname):
        return []
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Standardize format to [time, open, high, low, close, volume]
        candles = []
        for c in data:
            if isinstance(c, dict):
                candles.append([
                    c['time'], float(c['open']), float(c['high']), 
                    float(c['low']), float(c['close']), float(c.get('volume', 0.0))
                ])
            elif isinstance(c, list):
                candles.append([
                    c[0], float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])
                ])
        # Sort by timestamp
        candles.sort(key=lambda x: x[0])
        return candles
    except Exception as e:
        print(f"Err loading {symbol}: {e}")
        return []

def calculate_ema(values, period=50):
    if not values: return []
    ema = [values[0]] * len(values)
    k = 2.0 / (period + 1.0)
    for i in range(1, len(values)):
        ema[i] = values[i] * k + ema[i-1] * (1.0 - k)
    return ema

def calculate_atr(candles, period=14):
    atrs = [0.0] * len(candles)
    for i in range(1, len(candles)):
        h = candles[i][2]
        l = candles[i][3]
        prev_c = candles[i-1][4]
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        if i < period:
            atrs[i] = tr
        elif i == period:
            trs = [max(candles[k][2] - candles[k][3], 
                       abs(candles[k][2] - candles[k-1][4]), 
                       abs(candles[k][3] - candles[k-1][4])) for k in range(1, period+1)]
            atrs[i] = sum(trs) / period
        else:
            atrs[i] = (atrs[i-1] * (period - 1) + tr) / period
    return atrs

def calculate_sma_vol(candles, period=20):
    sma = [0.0] * len(candles)
    for i in range(len(candles)):
        if i >= period:
            vols = [candles[k][5] for k in range(i-period, i)]
            sma[i] = sum(vols) / period
        else:
            vols = [candles[k][5] for k in range(0, i+1)]
            sma[i] = sum(vols) / len(vols) if vols else 1.0
    return sma

def backtest_engine(candles_dict, btc_trend_dict, symbols, mode="HYBRID_35"):
    """
    mode options:
      - 'ZEN_WITH_BE': BE at +1.5% spot
      - 'ZEN_NO_BE': Pure Binary TP vs SL
      - 'HYBRID_35': BTC Trend Alignment + Stage 2 Dynamic Armor (+2% spot trigger -> lock +1% spot)
    """
    leverage = 5.0
    tp_roe = 12.20
    sl_roe = 12.00
    
    tp_pct = (tp_roe / 100.0) / leverage # +2.44%
    sl_pct = (sl_roe / 100.0) / leverage # -2.40%
    
    all_closed_trades = []
    symbol_stats = {}
    
    for symbol in symbols:
        candles = candles_dict.get(symbol, [])
        if len(candles) < 200:
            continue
            
        atrs = calculate_atr(candles, 14)
        avg_vols = calculate_sma_vol(candles, 20)
        
        active_unmitigated = []
        active_in_trade = []
        closed_trades = []
        
        max_active_zones = 4
        ai_min_score = 75 if mode == "HYBRID_35" else 70
        
        for i in range(25, len(candles)):
            c = candles[i]
            c_ts = c[0]
            c_open = c[1]
            c_high = c[2]
            c_low = c[3]
            c_close = c[4]
            c_time = datetime.datetime.fromtimestamp(c_ts/1000)
            
            btc_is_bull = btc_trend_dict.get(c_ts, True)
            
            # OB Qualification at candle i-3
            c3 = candles[i-3]
            o3, h3, l3, cl3 = c3[1], c3[2], c3[3], c3[4]
            
            c2 = candles[i-2]
            c1 = candles[i-1]
            h1, l1 = c1[2], c1[3]
            h2, l2 = c2[2], c2[3]
            v1, v2 = c1[5], c2[5]
            
            atr_val = atrs[i]
            avg_vol = avg_vols[i]
            
            impulse_h = max(h1, h2)
            impulse_l = min(l1, l2)
            impulse_v = max(v1, v2)
            vol_ratio = impulse_v / avg_vol if avg_vol > 0 else 1.0
            
            has_bull_fvg = (l1 > h3)
            has_bear_fvg = (h1 < l3)
            
            is_strict_red = (cl3 < o3)
            is_strict_green = (cl3 > o3)
            
            bull_expansion = impulse_h - l3
            bear_expansion = h3 - impulse_l
            bull_atr_ratio = (bull_expansion / atr_val) if atr_val > 0 else 0
            bear_atr_ratio = (bear_expansion / atr_val) if atr_val > 0 else 0
            
            # Bullish OB Qualification
            if is_strict_red and has_bull_fvg:
                score = 30
                if bull_atr_ratio >= 3.0: score += 40
                elif bull_atr_ratio >= 2.0: score += 35
                elif bull_atr_ratio >= 1.5: score += 25
                elif bull_atr_ratio >= 1.0: score += 15
                
                if vol_ratio >= 1.8: score += 20
                elif vol_ratio >= 1.3: score += 15
                elif vol_ratio >= 1.0: score += 10
                
                if l3 <= candles[i-4][3] or l3 == min([candles[k][3] for k in range(i-6, i)]):
                    score += 10
                    
                macro_pass = True
                if mode == "HYBRID_35" and symbol != 'BTCUSDT':
                    if not btc_is_bull and score < 85:
                        macro_pass = False
                        
                if score >= ai_min_score and bull_atr_ratio >= 1.3 and macro_pass:
                    ob = {
                        'symbol': symbol,
                        'side': 'LONG',
                        'start_idx': i-3,
                        'ob_high': h3,
                        'ob_low': l3,
                        'entry_price': h3, # Hermes Zen Boundary Entry
                        'tp_price': h3 * (1.0 + tp_pct),
                        'sl_price': h3 * (1.0 - sl_pct),
                        'be_trigger': h3 * 1.015, # +1.5%
                        'be_price': h3 * 1.001,
                        'stage2_trigger': h3 * 1.020, # +2.0%
                        'stage2_locked_sl': h3 * 1.010, # +1.0%
                        'armed': False,
                        'ai_score': score,
                        'entry_time': str(c_time)
                    }
                    active_unmitigated.append(ob)
                    if len(active_unmitigated) > max_active_zones:
                        active_unmitigated.pop(0)
                        
            # Bearish OB Qualification
            if is_strict_green and has_bear_fvg:
                score = 30
                if bear_atr_ratio >= 3.0: score += 40
                elif bear_atr_ratio >= 2.0: score += 35
                elif bear_atr_ratio >= 1.5: score += 25
                elif bear_atr_ratio >= 1.0: score += 15
                
                if vol_ratio >= 1.8: score += 20
                elif vol_ratio >= 1.3: score += 15
                elif vol_ratio >= 1.0: score += 10
                
                if h3 >= candles[i-4][2] or h3 == max([candles[k][2] for k in range(i-6, i)]):
                    score += 10
                    
                macro_pass = True
                if mode == "HYBRID_35" and symbol != 'BTCUSDT':
                    if btc_is_bull and score < 85:
                        macro_pass = False
                        
                if score >= ai_min_score and bear_atr_ratio >= 1.3 and macro_pass:
                    ob = {
                        'symbol': symbol,
                        'side': 'SHORT',
                        'start_idx': i-3,
                        'ob_high': h3,
                        'ob_low': l3,
                        'entry_price': l3,
                        'tp_price': l3 * (1.0 - tp_pct),
                        'sl_price': l3 * (1.0 + sl_pct),
                        'be_trigger': l3 * 0.985, # -1.5%
                        'be_price': l3 * 0.999,
                        'stage2_trigger': l3 * 0.980, # -2.0%
                        'stage2_locked_sl': l3 * 0.990, # -1.0%
                        'armed': False,
                        'ai_score': score,
                        'entry_time': str(c_time)
                    }
                    active_unmitigated.append(ob)
                    if len(active_unmitigated) > max_active_zones:
                        active_unmitigated.pop(0)
                        
            # In-trade position management
            still_in_trade = []
            for tr in active_in_trade:
                if tr['side'] == 'LONG':
                    if mode == 'ZEN_WITH_BE':
                        if not tr['armed'] and c_high >= tr['be_trigger']:
                            tr['armed'] = True
                            tr['sl_price'] = tr['be_price']
                    elif mode == 'HYBRID_35':
                        if not tr['armed'] and c_high >= tr['stage2_trigger']:
                            tr['armed'] = True
                            tr['sl_price'] = tr['stage2_locked_sl']
                            
                    # Check exits
                    if c_high >= tr['tp_price']:
                        tr['result'] = 'TP_HIT'
                        tr['roe'] = tp_roe
                        tr['exit_time'] = str(c_time)
                        closed_trades.append(tr)
                    elif c_low <= tr['sl_price']:
                        if tr['armed']:
                            if mode == 'ZEN_WITH_BE':
                                tr['result'] = 'BE_HIT'
                                tr['roe'] = 0.50
                            else: # HYBRID_35
                                tr['result'] = 'STAGE2_WIN'
                                tr['roe'] = 5.0
                        else:
                            tr['result'] = 'SL_HIT'
                            tr['roe'] = -sl_roe
                        tr['exit_time'] = str(c_time)
                        closed_trades.append(tr)
                    else:
                        still_in_trade.append(tr)
                        
                elif tr['side'] == 'SHORT':
                    if mode == 'ZEN_WITH_BE':
                        if not tr['armed'] and c_low <= tr['be_trigger']:
                            tr['armed'] = True
                            tr['sl_price'] = tr['be_price']
                    elif mode == 'HYBRID_35':
                        if not tr['armed'] and c_low <= tr['stage2_trigger']:
                            tr['armed'] = True
                            tr['sl_price'] = tr['stage2_locked_sl']
                            
                    if c_low <= tr['tp_price']:
                        tr['result'] = 'TP_HIT'
                        tr['roe'] = tp_roe
                        tr['exit_time'] = str(c_time)
                        closed_trades.append(tr)
                    elif c_high >= tr['sl_price']:
                        if tr['armed']:
                            if mode == 'ZEN_WITH_BE':
                                tr['result'] = 'BE_HIT'
                                tr['roe'] = 0.50
                            else:
                                tr['result'] = 'STAGE2_WIN'
                                tr['roe'] = 5.0
                        else:
                            tr['result'] = 'SL_HIT'
                            tr['roe'] = -sl_roe
                        tr['exit_time'] = str(c_time)
                        closed_trades.append(tr)
                    else:
                        still_in_trade.append(tr)
                        
            active_in_trade = still_in_trade
            
            # Check 1st Tap on Active Unmitigated Zones
            still_unmitigated = []
            for ob in active_unmitigated:
                if ob['side'] == 'LONG':
                    if c_close < ob['ob_low']:
                        continue
                    tapped = (c_low <= ob['ob_high'] and c_low > ob['sl_price'] and c_close >= ob['ob_low'])
                    if tapped and len(active_in_trade) == 0:
                        trade = dict(ob)
                        trade['entry_time'] = str(c_time)
                        active_in_trade.append(trade)
                    else:
                        still_unmitigated.append(ob)
                elif ob['side'] == 'SHORT':
                    if c_close > ob['ob_high']:
                        continue
                    tapped = (c_high >= ob['ob_low'] and c_high < ob['sl_price'] and c_close <= ob['ob_high'])
                    if tapped and len(active_in_trade) == 0:
                        trade = dict(ob)
                        trade['entry_time'] = str(c_time)
                        active_in_trade.append(trade)
                    else:
                        still_unmitigated.append(ob)
            active_unmitigated = still_unmitigated
            
        all_closed_trades.extend(closed_trades)
        wins = [t for t in closed_trades if t['roe'] > 0]
        losses = [t for t in closed_trades if t['roe'] < 0]
        tot = len(closed_trades)
        wr = (len(wins) / tot * 100.0) if tot > 0 else 0
        net_roe = sum(t['roe'] for t in closed_trades)
        symbol_stats[symbol] = {
            'total': tot,
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': wr,
            'net_roe': net_roe
        }
        
    return all_closed_trades, symbol_stats

def main():
    print("="*85)
    print("🏛️ HERMES 3.5 AI QUANT vs ZEN SNIPER — 1-YEAR MASTER BACKTEST AUDIT (8,760 HOURS)")
    print("="*85)
    
    # Load candle data
    candles_dict = {}
    print("Loading 1-Year historical datasets...")
    for s in ALL_AVAILABLE:
        c = load_candles_1y(s)
        if c:
            candles_dict[s] = c
            print(f"  Loaded {s}: {len(c)} candles ({len(c)//24} days)")
            
    # BTC Trend
    btc_candles = candles_dict.get('BTCUSDT', [])
    btc_closes = [c[4] for c in btc_candles]
    btc_ema50 = calculate_ema(btc_closes, 50)
    btc_trend_dict = {btc_candles[i][0]: (btc_closes[i] >= btc_ema50[i]) for i in range(len(btc_candles))}
    
    print("\n" + "="*85)
    print("RUNNING 1-YEAR AUDIT: 3 COMPETING SYSTEMS")
    print("="*85)
    
    # 1. System 1: Zen Sniper (With BE)
    t1, s1 = backtest_engine(candles_dict, btc_trend_dict, ALL_AVAILABLE, mode="ZEN_WITH_BE")
    w1 = [t for t in t1 if t['roe'] > 0]
    l1 = [t for t in t1 if t['roe'] < 0]
    wr1 = (len(w1)/len(t1)*100) if t1 else 0
    roe1 = sum(t['roe'] for t in t1)
    
    # 2. System 2: Zen Sniper (No BE)
    t2, s2 = backtest_engine(candles_dict, btc_trend_dict, ALL_AVAILABLE, mode="ZEN_NO_BE")
    w2 = [t for t in t2 if t['roe'] > 0]
    l2 = [t for t in t2 if t['roe'] < 0]
    wr2 = (len(w2)/len(t2)*100) if t2 else 0
    roe2 = sum(t['roe'] for t in t2)
    
    # 3. System 3: Hermes 3.5 + Zen Hybrid (Vetted Champions + Macro Filter + Stage 2 Armor)
    t3, s3 = backtest_engine(candles_dict, btc_trend_dict, CHAMPIONS, mode="HYBRID_35")
    w3 = [t for t in t3 if t['roe'] > 0]
    l3 = [t for t in t3 if t['roe'] < 0]
    wr3 = (len(w3)/len(t3)*100) if t3 else 0
    roe3 = sum(t['roe'] for t in t3)
    
    # Profit factor calculation for System 3
    gp3 = sum(t['roe'] for t in w3)
    gl3 = abs(sum(t['roe'] for t in l3))
    pf3 = (gp3 / gl3) if gl3 > 0 else 999.0
    
    # Compounding simulation for System 3 (Sequential queue, $50 start, max 2.5% risk / position sizing)
    sorted_t3 = sorted(t3, key=lambda x: x['entry_time'])
    bal = 50.0
    bal_hist = [bal]
    peak = bal
    mdd = 0.0
    
    for tr in sorted_t3:
        # Standard 20x challenge risk model: 10% account allocation per trade @ 5x leverage
        pos_margin = bal * 0.10
        pos_pnl = pos_margin * (tr['roe'] / 100.0)
        bal += pos_pnl
        bal_hist.append(bal)
        if bal > peak: peak = bal
        dd = (peak - bal) / peak * 100.0
        if dd > mdd: mdd = dd
        
    print(f"\n[System 1: Zen Sniper (With BE)]")
    print(f"  Total Trades: {len(t1)} | Wins: {len(w1)} | Losses: {len(l1)} | WinRate: {wr1:.1f}% | Net ROE: {roe1:+.1f}%")
    
    print(f"\n[System 2: Zen Sniper (No BE)]")
    print(f"  Total Trades: {len(t2)} | Wins: {len(w2)} | Losses: {len(l2)} | WinRate: {wr2:.1f}% | Net ROE: {roe2:+.1f}%")
    
    print(f"\n[System 3: Hermes 3.5 + Zen Hybrid (Vetted Champions)]")
    print(f"  Total Trades: {len(t3)} | Wins: {len(w3)} | Losses: {len(l3)} | WinRate: {wr3:.1f}% | Net ROE: {roe3:+.1f}% | PF: {pf3:.2f}")
    print(f"  Compounding Growth ($50 Start): ${bal:,.2f} ({((bal-50)/50)*100:+,.1f}%) | Max DD: {mdd:.1f}%")
    
    # Save master JSON
    with open('hermes_1year_master_audit_result.json', 'w') as f:
        json.dump({
            'system1_zen_with_be': {'trades': len(t1), 'wins': len(w1), 'losses': len(l1), 'win_rate': wr1, 'net_roe': roe1},
            'system2_zen_no_be': {'trades': len(t2), 'wins': len(w2), 'losses': len(l2), 'win_rate': wr2, 'net_roe': roe2},
            'system3_hybrid_35': {
                'trades': len(t3), 'wins': len(w3), 'losses': len(l3), 'win_rate': wr3, 'net_roe': roe3, 
                'profit_factor': pf3, 'ending_balance': bal, 'max_drawdown': mdd, 'symbol_stats': s3
            }
        }, f, indent=2)
    print("\nSaved 1-year master audit to hermes_1year_master_audit_result.json")

if __name__ == '__main__':
    main()
