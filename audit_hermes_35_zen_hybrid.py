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

ALL_SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT', 
    'AVAXUSDT', 'DOGEUSDT', 'XRPUSDT', 'LINKUSDT', 'NEARUSDT', 
    'SUIUSDT', 'APTUSDT', 'TIAUSDT', 'ARBUSDT', 'OPUSDT', 
    'FILUSDT', 'JASMYUSDT', 'AXSUSDT', 'FETUSDT'
]

# Hermes 3.5 Vetted Champions (excl. high-chop meme/lagging pairs like ADA, DOGE, BNB, XRP)
CHAMPION_SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'AVAXUSDT', 'LINKUSDT', 
    'NEARUSDT', 'SUIUSDT', 'APTUSDT', 'TIAUSDT', 'ARBUSDT', 
    'OPUSDT', 'FILUSDT', 'JASMYUSDT', 'AXSUSDT', 'FETUSDT'
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

def calculate_ema(values, period=50):
    ema = [values[0]] * len(values)
    k = 2.0 / (period + 1.0)
    for i in range(1, len(values)):
        ema[i] = values[i] * k + ema[i-1] * (1.0 - k)
    return ema

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

def run_hybrid_backtest(candles_dict, btc_trend_dict, symbols_to_test, use_btc_filter=True, use_stage2_armor=True):
    leverage = 5.0
    tp_roe = 12.20
    sl_roe = 12.00
    
    tp_pct = (tp_roe / 100.0) / leverage # +2.44%
    sl_pct = (sl_roe / 100.0) / leverage # -2.40%
    
    # Hermes 3.5 Stage 2 Armor: trigger at +2.0% spot move (+10.0% ROE), lock at +1.0% spot (+5.0% ROE)
    stage2_trigger_spot = 0.020 # +2.0%
    stage2_lock_spot = 0.010    # +1.0%
    
    all_closed_trades = []
    symbol_stats = {}
    
    for symbol in symbols_to_test:
        candles = candles_dict.get(symbol, [])
        if len(candles) < 100:
            continue
            
        atrs = calculate_atr(candles, 14)
        avg_vols = calculate_sma_vol(candles, 20)
        
        active_unmitigated = []
        active_in_trade = []
        closed_trades = []
        
        max_active_zones = 4
        ai_min_score = 75 # Hermes 3.5 High Institutional Confluence
        
        for i in range(25, len(candles)):
            current_candle = candles[i]
            c_time_ts = current_candle[0]
            c_open = float(current_candle[1])
            c_high = float(current_candle[2])
            c_low = float(current_candle[3])
            c_close = float(current_candle[4])
            c_time = datetime.datetime.fromtimestamp(c_time_ts/1000)
            
            # BTC Trend at this timestamp
            btc_is_bull = btc_trend_dict.get(c_time_ts, True)
            
            # 1. Evaluate OB Qualification at candle i-3 (Hermes AI Zen OB Logic)
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
            
            # Strict Candle Color Gate
            is_strict_red = (cl3 < o3)
            is_strict_green = (cl3 > o3)
            
            bull_expansion = impulse_h - l3
            bear_expansion = h3 - impulse_l
            bull_atr_ratio = (bull_expansion / atr_val) if atr_val > 0 else 0
            bear_atr_ratio = (bear_expansion / atr_val) if atr_val > 0 else 0
            
            # Bullish OB Qualification
            if is_strict_red and has_bull_fvg:
                score = 30 # FVG Displacement
                if bull_atr_ratio >= 3.0: score += 40
                elif bull_atr_ratio >= 2.0: score += 35
                elif bull_atr_ratio >= 1.5: score += 25
                elif bull_atr_ratio >= 1.0: score += 15
                
                if vol_ratio >= 1.8: score += 20
                elif vol_ratio >= 1.3: score += 15
                elif vol_ratio >= 1.0: score += 10
                
                # Liquidity Sweep check (prior wick sweep)
                if l3 <= float(candles[i-4][3]) or l3 == min([float(candles[k][3]) for k in range(i-6, i)]):
                    score += 10
                    
                # Macro Sentry Filter check
                macro_pass = True
                if use_btc_filter and symbol != 'BTCUSDT':
                    if not btc_is_bull and score < 85: # Require elite score if counter-trend
                        macro_pass = False
                        
                if score >= ai_min_score and bull_atr_ratio >= 1.3 and macro_pass:
                    ob = {
                        'symbol': symbol,
                        'side': 'LONG',
                        'start_idx': i-3,
                        'ob_high': h3,
                        'ob_low': l3,
                        'entry_price': h3, # Hermes Zen Boundary Entry!
                        'tp_price': h3 * (1.0 + tp_pct),
                        'sl_price': h3 * (1.0 - sl_pct),
                        'stage2_trigger': h3 * (1.0 + stage2_trigger_spot),
                        'stage2_locked_sl': h3 * (1.0 + stage2_lock_spot),
                        'stage2_armed': False,
                        'ai_score': score,
                        'created_time': str(datetime.datetime.fromtimestamp(c3[0]/1000))
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
                
                if h3 >= float(candles[i-4][2]) or h3 == max([float(candles[k][2]) for k in range(i-6, i)]):
                    score += 10
                    
                macro_pass = True
                if use_btc_filter and symbol != 'BTCUSDT':
                    if btc_is_bull and score < 85:
                        macro_pass = False
                        
                if score >= ai_min_score and bear_atr_ratio >= 1.3 and macro_pass:
                    ob = {
                        'symbol': symbol,
                        'side': 'SHORT',
                        'start_idx': i-3,
                        'ob_high': h3,
                        'ob_low': l3,
                        'entry_price': l3, # Hermes Zen Boundary Entry!
                        'tp_price': l3 * (1.0 - tp_pct),
                        'sl_price': l3 * (1.0 + sl_pct),
                        'stage2_trigger': l3 * (1.0 - stage2_trigger_spot),
                        'stage2_locked_sl': l3 * (1.0 - stage2_lock_spot),
                        'stage2_armed': False,
                        'ai_score': score,
                        'created_time': str(datetime.datetime.fromtimestamp(c3[0]/1000))
                    }
                    active_unmitigated.append(ob)
                    if len(active_unmitigated) > max_active_zones:
                        active_unmitigated.pop(0)
                        
            # 2. Check Active In-Trade Positions (Hermes 3.5 Dynamic Multi-Stage Logic)
            still_in_trade = []
            for tr in active_in_trade:
                if tr['side'] == 'LONG':
                    # Check Stage 2 Armor Trigger
                    if use_stage2_armor and not tr['stage2_armed'] and c_high >= tr['stage2_trigger']:
                        tr['stage2_armed'] = True
                        tr['sl_price'] = tr['stage2_locked_sl']
                        
                    # Check TP
                    if c_high >= tr['tp_price']:
                        tr['exit_price'] = tr['tp_price']
                        tr['result'] = 'TP_HIT'
                        tr['roe'] = tp_roe
                        tr['exit_time'] = str(c_time)
                        closed_trades.append(tr)
                    elif c_low <= tr['sl_price']:
                        tr['exit_price'] = tr['sl_price']
                        if tr['stage2_armed']:
                            tr['result'] = 'STAGE2_WIN'
                            tr['roe'] = 5.0 # +5.0% ROE secured profit
                        else:
                            tr['result'] = 'SL_HIT'
                            tr['roe'] = -sl_roe
                        tr['exit_time'] = str(c_time)
                        closed_trades.append(tr)
                    else:
                        still_in_trade.append(tr)
                        
                elif tr['side'] == 'SHORT':
                    if use_stage2_armor and not tr['stage2_armed'] and c_low <= tr['stage2_trigger']:
                        tr['stage2_armed'] = True
                        tr['sl_price'] = tr['stage2_locked_sl']
                        
                    if c_low <= tr['tp_price']:
                        tr['exit_price'] = tr['tp_price']
                        tr['result'] = 'TP_HIT'
                        tr['roe'] = tp_roe
                        tr['exit_time'] = str(c_time)
                        closed_trades.append(tr)
                    elif c_high >= tr['sl_price']:
                        tr['exit_price'] = tr['sl_price']
                        if tr['stage2_armed']:
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
            
            # 3. Check 1st Tap on Active Unmitigated Zones
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
        wins = [t for t in closed_trades if t['result'] in ('TP_HIT', 'STAGE2_WIN')]
        losses = [t for t in closed_trades if t['result'] == 'SL_HIT']
        total = len(closed_trades)
        win_rate = (len(wins) / total * 100.0) if total > 0 else 0.0
        net_roe = sum(t['roe'] for t in closed_trades)
        symbol_stats[symbol] = {
            'total': total,
            'wins': len(wins),
            'tp_hits': len([t for t in closed_trades if t['result'] == 'TP_HIT']),
            'stage2_wins': len([t for t in closed_trades if t['result'] == 'STAGE2_WIN']),
            'losses': len(losses),
            'win_rate': win_rate,
            'net_roe': net_roe
        }
        
    return all_closed_trades, symbol_stats

def main():
    print("="*80)
    print("HERMES 3.5 AI QUANT + ZEN SNIPER HYBRID ENGINE 1-MONTH AUDIT")
    print("Combining: Hermes 3.5 Macro Sentry & Dynamic Armor + Hermes Zen OB Selection")
    print("="*80)
    
    # 1. Fetch candles for all symbols
    candles_dict = {}
    for s in ALL_SYMBOLS:
        print(f"Fetching 30-day 1H data for {s}...")
        candles_dict[s] = fetch_klines(s, 720)
        time.sleep(0.08)
        
    # 2. Build BTC Trend Dict
    btc_candles = candles_dict.get('BTCUSDT', [])
    btc_closes = [float(c[4]) for c in btc_candles]
    btc_ema50 = calculate_ema(btc_closes, 50)
    btc_trend_dict = {}
    for i, c in enumerate(btc_candles):
        c_ts = c[0]
        btc_trend_dict[c_ts] = (btc_closes[i] >= btc_ema50[i])
        
    print("\n" + "="*80)
    print("TEST A: HYBRID ENGINE ON ALL 19 FUTURES ASSETS")
    print("="*80)
    trades_all, stats_all = run_hybrid_backtest(candles_dict, btc_trend_dict, ALL_SYMBOLS, use_btc_filter=True, use_stage2_armor=True)
    
    tot_trades_all = len(trades_all)
    wins_all = [t for t in trades_all if t['result'] in ('TP_HIT', 'STAGE2_WIN')]
    losses_all = [t for t in trades_all if t['result'] == 'SL_HIT']
    win_rate_all = (len(wins_all) / tot_trades_all * 100.0) if tot_trades_all > 0 else 0
    net_roe_all = sum(t['roe'] for t in trades_all)
    
    print(f"Total Trades: {tot_trades_all} | Wins: {len(wins_all)} | Losses: {len(losses_all)} | Win Rate: {win_rate_all:.1f}% | Net ROE: {net_roe_all:+.1f}%")
    
    print("\n" + "="*80)
    print("TEST B: HYBRID ENGINE ON HERMES 3.5 VETTED CHAMPIONS (15 ELITE COINS)")
    print("Excluding toxic chop coins (ADA, DOGE, BNB, XRP)")
    print("="*80)
    trades_champ, stats_champ = run_hybrid_backtest(candles_dict, btc_trend_dict, CHAMPION_SYMBOLS, use_btc_filter=True, use_stage2_armor=True)
    
    tot_trades_champ = len(trades_champ)
    wins_champ = [t for t in trades_champ if t['result'] in ('TP_HIT', 'STAGE2_WIN')]
    losses_champ = [t for t in trades_champ if t['result'] == 'SL_HIT']
    win_rate_champ = (len(wins_champ) / tot_trades_champ * 100.0) if tot_trades_champ > 0 else 0
    net_roe_champ = sum(t['roe'] for t in trades_champ)
    
    gross_profit = sum(t['roe'] for t in wins_champ)
    gross_loss = abs(sum(t['roe'] for t in losses_champ))
    pf_champ = (gross_profit / gross_loss) if gross_loss > 0 else 999.0
    
    print(f"Total Trades: {tot_trades_champ} | Wins: {len(wins_champ)} | Losses: {len(losses_champ)} | Win Rate: {win_rate_champ:.1f}% | Net ROE: {net_roe_champ:+.1f}% | Profit Factor: {pf_champ:.2f}")
    
    # Save results
    with open('hermes_35_zen_hybrid_audit_result.json', 'w') as f:
        json.dump({
            'all_19_pairs': {
                'total_trades': tot_trades_all,
                'wins': len(wins_all),
                'losses': len(losses_all),
                'win_rate': win_rate_all,
                'net_roe': net_roe_all,
                'stats': stats_all
            },
            'champions_15_pairs': {
                'total_trades': tot_trades_champ,
                'wins': len(wins_champ),
                'losses': len(losses_champ),
                'win_rate': win_rate_champ,
                'net_roe': net_roe_champ,
                'profit_factor': pf_champ,
                'stats': stats_champ
            }
        }, f, indent=2)
    print("Report saved to hermes_35_zen_hybrid_audit_result.json")

if __name__ == '__main__':
    main()
