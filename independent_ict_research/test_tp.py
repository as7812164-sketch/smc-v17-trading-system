import os, sys, json
sys.path.append(r'C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\independent_ict_research')
from battle_hermes35_vs_apex_ict import load_candles, calculate_atr, run_compounding_arena, TOP_22_CHAMPIONS

all_data = {'1h': {}, '4h': {}}
for sym in TOP_22_CHAMPIONS:
    for tf in ['1h', '4h']:
        c = load_candles(sym, tf)
        if len(c) >= 500:
            all_data[tf][sym] = c

def test_apex_fixed_tp(tp_1h=0.022, tp_4h=0.028):
    trades = []
    for tf in ['1h', '4h']:
        tp_pct = tp_1h if tf == '1h' else tp_4h
        max_hold = 24
        for sym, raw_candles in all_data[tf].items():
            n = len(raw_candles)
            if n < 60:
                continue
            atrs = calculate_atr(raw_candles)
            for i in range(25, n - 40):
                w = raw_candles[max(0, i-40):i+1]
                r_low = min(c['low'] for c in w)
                r_high = max(c['high'] for c in w)
                eq = (r_low + r_high) / 2.0
                
                # Bullish Bedrock
                if raw_candles[i]['low'] == min(c['low'] for c in raw_candles[i-15:i+1]):
                    if raw_candles[i]['low'] > eq:
                        continue
                    sub_w = raw_candles[i:min(i+20, n)]
                    highs = [c['high'] for c in sub_w]
                    max_high = max(highs)
                    high_idx = i + highs.index(max_high)
                    if high_idx > i + 3:
                        prev_high_ref = max(c['high'] for c in raw_candles[max(0, i-20):i])
                        if not any(raw_candles[k]['close'] > prev_high_ref for k in range(i+1, high_idx+1)):
                            continue
                        if (max_high - raw_candles[i]['low']) / raw_candles[i]['low'] >= 0.05:
                            idm_low = raw_candles[high_idx-1]['low']
                            bedrock_c = raw_candles[i]
                            ob_top = max(bedrock_c['open'], bedrock_c['close'])
                            ob_bot = bedrock_c['low']
                            atr_val = atrs[i] if i < len(atrs) else (ob_top - ob_bot)
                            buffered_sl = ob_bot - (0.35 * atr_val)
                            for t in range(high_idx+1, min(high_idx+40, n)):
                                tap_c = raw_candles[t]
                                if not any(raw_candles[k]['low'] < idm_low for k in range(high_idx, t+1)):
                                    continue
                                if tap_c['low'] <= ob_top * 1.001:
                                    c_range = max(tap_c['high'] - tap_c['low'], 1e-6)
                                    l_wick = min(tap_c['open'], tap_c['close']) - tap_c['low']
                                    if tap_c['close'] <= eq and (l_wick / c_range) >= 0.18:
                                        entry = min(tap_c['close'], ob_top)
                                        tp_p = entry * (1.0 + tp_pct)
                                        res = None
                                        exit_p = entry
                                        exit_t = tap_c['time']
                                        for m in range(t+1, min(t+max_hold, n)):
                                            if raw_candles[m]['high'] >= tp_p:
                                                res = 'WIN'
                                                exit_p = tp_p
                                                exit_t = raw_candles[m]['time']
                                                break
                                            if raw_candles[m]['low'] <= buffered_sl:
                                                res = 'LOSS'
                                                exit_p = buffered_sl
                                                exit_t = raw_candles[m]['time']
                                                break
                                        if not res:
                                            fc = raw_candles[min(t+max_hold, n-1)]['close']
                                            res = 'WIN' if fc >= entry else 'LOSS'
                                            exit_p = fc
                                            exit_t = raw_candles[min(t+max_hold, n-1)]['time']
                                        trades.append({
                                            'strategy': 'APEX_REALISTIC_TP', 'sym': sym, 'side': 'LONG', 'tf': tf,
                                            'time': tap_c['time'], 'exit_time': exit_t, 'entry': entry, 'exit': exit_p,
                                            'gross': (exit_p - entry)/entry, 'res': res
                                        })
                                    break
                # Bearish Bedrock
                if raw_candles[i]['high'] == max(c['high'] for c in raw_candles[i-15:i+1]):
                    if raw_candles[i]['high'] < eq:
                        continue
                    sub_w = raw_candles[i:min(i+20, n)]
                    lows = [c['low'] for c in sub_w]
                    min_low = min(lows)
                    low_idx = i + lows.index(min_low)
                    if low_idx > i + 3:
                        prev_low_ref = min(c['low'] for c in raw_candles[max(0, i-20):i])
                        if not any(raw_candles[k]['close'] < prev_low_ref for k in range(i+1, low_idx+1)):
                            continue
                        if (raw_candles[i]['high'] - min_low) / raw_candles[i]['high'] >= 0.05:
                            idm_high = raw_candles[low_idx-1]['high']
                            bedrock_c = raw_candles[i]
                            ob_top = bedrock_c['high']
                            ob_bot = min(bedrock_c['open'], bedrock_c['close'])
                            atr_val = atrs[i] if i < len(atrs) else (ob_top - ob_bot)
                            buffered_sl = ob_top + (0.35 * atr_val)
                            for t in range(low_idx+1, min(low_idx+40, n)):
                                tap_c = raw_candles[t]
                                if not any(raw_candles[k]['high'] > idm_high for k in range(low_idx, t+1)):
                                    continue
                                if tap_c['high'] >= ob_bot * 0.999:
                                    c_range = max(tap_c['high'] - tap_c['low'], 1e-6)
                                    u_wick = tap_c['high'] - max(tap_c['open'], tap_c['close'])
                                    if tap_c['close'] >= eq and (u_wick / c_range) >= 0.18:
                                        entry = max(tap_c['close'], ob_bot)
                                        tp_p = entry * (1.0 - tp_pct)
                                        res = None
                                        exit_p = entry
                                        exit_t = tap_c['time']
                                        for m in range(t+1, min(t+max_hold, n)):
                                            if raw_candles[m]['low'] <= tp_p:
                                                res = 'WIN'
                                                exit_p = tp_p
                                                exit_t = raw_candles[m]['time']
                                                break
                                            if raw_candles[m]['high'] >= buffered_sl:
                                                res = 'LOSS'
                                                exit_p = buffered_sl
                                                exit_t = raw_candles[m]['time']
                                                break
                                        if not res:
                                            fc = raw_candles[min(t+max_hold, n-1)]['close']
                                            res = 'WIN' if fc <= entry else 'LOSS'
                                            exit_p = fc
                                            exit_t = raw_candles[min(t+max_hold, n-1)]['time']
                                        trades.append({
                                            'strategy': 'APEX_REALISTIC_TP', 'sym': sym, 'side': 'SHORT', 'tf': tf,
                                            'time': tap_c['time'], 'exit_time': exit_t, 'entry': entry, 'exit': exit_p,
                                            'gross': (entry - exit_p)/entry, 'res': res
                                        })
                                    break
    return trades

t_fixed = test_apex_fixed_tp()
res_arena = run_compounding_arena(t_fixed, 'APEX_REALISTIC_TP')
print("Total trades generated:", len(t_fixed))
print(f"Executed: {res_arena['sequential_trades_executed']} | Wins: {res_arena['wins']} | Losses: {res_arena['losses']}")
print(f"Win Rate: {res_arena['win_rate_pct']}% | Profit Factor: {res_arena['profit_factor']} | Max DD: {res_arena['max_drawdown_pct']}%")
print(f"Hit 1k: Trade #{res_arena['hit_1k_trade']} | Final Wealth: ${res_arena['total_wealth_usdt']:,.2f}")
