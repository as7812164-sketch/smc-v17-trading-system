import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import battle_hermes2_vs_hermes3 as b

all_data = {'1h': {}, '4h': {}}
for sym in b.TOP_22_CHAMPIONS:
    for tf in ['1h', '4h']:
        k = b.load_local_data(sym, tf)
        if len(k) >= 500:
            all_data[tf][sym] = k

btc_4h = b.load_local_data('BTCUSDT', '4h')
btc_map_4h = {c['time']: c for c in btc_4h}

h2_signals = []
h3a_signals = []

for tf in ['1h', '4h']:
    std_tp_pct = 0.022 if tf == '1h' else 0.028
    soft_sl_pct = 0.025 if tf == '1h' else 0.028
    hard_sl_pct = 0.036 if tf == '1h' else 0.038
    max_tap_window = 28
    max_hold = 24

    for sym, candles in all_data[tf].items():
        n = len(candles)
        for i in range(25, n - 35):
            # BULLISH
            if candles[i]['low'] == min(c['low'] for c in candles[i-15:i+1]):
                sub_w = candles[i:min(i+16, n)]
                highs = [c['high'] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx > i + 3:
                    gain = (max_high - candles[i]['low']) / candles[i]['low']
                    if gain >= 0.050:
                        idm_low = candles[high_idx - 1]['low']
                        best_mid = -1; max_bg = 0.0
                        for mid in range(i+1, high_idx):
                            bg = (candles[mid]['high'] - candles[mid]['low']) / candles[mid]['low']
                            fib = (candles[mid]['low'] - candles[i]['low']) / (max_high - candles[i]['low'])
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg; best_mid = mid

                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = max(dec_c['open'], dec_c['close'])
                            dec_bot = dec_c['low']
                            has_fvg = (candles[best_mid + 1]['low'] > candles[best_mid - 1]['high']) if best_mid + 1 < n else False
                            if has_fvg:
                                for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                    if candles[t]['low'] <= dec_top * 0.9995:
                                        tap_c = candles[t]
                                        curr_4h_start = tap_c['time'] - (tap_c['time'] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        btc_dump = (btc_c['open'] - btc_c['close']) / btc_c['open'] if btc_c else 0.0
                                        sentry1_clean = btc_dump < 0.020

                                        c_range = tap_c['high'] - tap_c['low']
                                        swept = any(candles[k]['low'] < idm_low for k in range(high_idx, t + 1))
                                        l_wick = min(tap_c['open'], tap_c['close']) - tap_c['low']
                                        w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                        mt = (dec_top + dec_bot) / 2.0

                                        if swept and w_ratio >= 0.18 and tap_c['close'] >= mt and sentry1_clean:
                                            entry = dec_top
                                            tp_p = entry * (1.0 + std_tp_pct)
                                            soft_sl_p = entry * (1.0 - soft_sl_pct)
                                            hard_sl_p = entry * (1.0 - hard_sl_pct)

                                            # H2
                                            res = None; exit_p = entry; exit_t = tap_c['time']; exit_reason = 'HOLD_EXPIRY'
                                            for m in range(t, min(t + max_hold, n)):
                                                if candles[m]['high'] >= tp_p:
                                                    res = 'WIN'; exit_p = tp_p; exit_t = candles[m]['time']; exit_reason = 'TP_HIT'; break
                                                if candles[m]['low'] <= hard_sl_p:
                                                    res = 'LOSS'; exit_p = min(hard_sl_p, candles[m]['open']); exit_t = candles[m]['time']; exit_reason = 'HARD_SL'; break
                                                if candles[m]['close'] <= soft_sl_p:
                                                    res = 'LOSS'; exit_p = candles[m]['close']; exit_t = candles[m]['time']; exit_reason = 'SOFT_SL'; break
                                            if not res:
                                                fc = candles[min(t + max_hold, n - 1)]['close']
                                                res = 'WIN' if fc >= entry else 'LOSS'
                                                exit_p = fc
                                                exit_t = candles[min(t + max_hold, n - 1)]['time']

                                            h2_signals.append({
                                                'sym': sym, 'side': 'LONG', 'tf': tf, 'time': tap_c['time'],
                                                'exit_time': exit_t, 'entry': entry, 'exit': exit_p,
                                                'gross': (exit_p - entry) / entry, 'res': res, 'exit_reason': exit_reason
                                            })

                                            # H3A
                                            res_3 = None; exit_p_3 = entry; exit_t_3 = tap_c['time']; exit_reason_3 = 'HOLD_EXPIRY'
                                            curr_soft_sl = soft_sl_p
                                            armor_stage = 0
                                            for m in range(t, min(t + max_hold, n)):
                                                high_so_far = candles[m]['high']
                                                if high_so_far >= entry * 1.016:
                                                    curr_soft_sl = max(curr_soft_sl, entry * 1.002)
                                                    armor_stage = max(armor_stage, 1)
                                                if high_so_far >= entry * 1.022:
                                                    curr_soft_sl = max(curr_soft_sl, entry * 1.012)
                                                    armor_stage = max(armor_stage, 2)

                                                if candles[m]['high'] >= tp_p:
                                                    res_3 = 'WIN'; exit_p_3 = tp_p; exit_t_3 = candles[m]['time']; exit_reason_3 = 'TP_HIT'; break
                                                if candles[m]['low'] <= hard_sl_p:
                                                    res_3 = 'LOSS'; exit_p_3 = min(hard_sl_p, candles[m]['open']); exit_t_3 = candles[m]['time']; exit_reason_3 = 'HARD_SL'; break
                                                if candles[m]['close'] <= curr_soft_sl:
                                                    res_3 = 'WIN' if curr_soft_sl > entry else 'LOSS'
                                                    exit_p_3 = candles[m]['close']
                                                    exit_t_3 = candles[m]['time']
                                                    exit_reason_3 = f'ARMOR_STAGE_{armor_stage}' if armor_stage > 0 else 'SOFT_SL'
                                                    break
                                            if not res_3:
                                                fc = candles[min(t + max_hold, n - 1)]['close']
                                                res_3 = 'WIN' if fc >= entry else 'LOSS'
                                                exit_p_3 = fc
                                                exit_t_3 = candles[min(t + max_hold, n - 1)]['time']

                                            h3a_signals.append({
                                                'sym': sym, 'side': 'LONG', 'tf': tf, 'time': tap_c['time'],
                                                'exit_time': exit_t_3, 'entry': entry, 'exit': exit_p_3,
                                                'gross': (exit_p_3 - entry) / entry, 'res': res_3, 'exit_reason': exit_reason_3
                                            })
                                        break

            # BEARISH
            if candles[i]['high'] == max(c['high'] for c in candles[i-15:i+1]):
                sub_w = candles[i:min(i+16, n)]
                lows = [c['low'] for c in sub_w]
                min_low = min(lows)
                low_idx = i + lows.index(min_low)
                if low_idx > i + 3:
                    drop = (candles[i]['high'] - min_low) / candles[i]['high']
                    if drop >= 0.050:
                        idm_high = candles[low_idx - 1]['high']
                        best_mid = -1; max_bg = 0.0
                        for mid in range(i+1, low_idx):
                            bg = (candles[mid]['high'] - candles[mid]['low']) / candles[mid]['low']
                            fib = (candles[i]['high'] - candles[mid]['high']) / (candles[i]['high'] - min_low)
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg; best_mid = mid

                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = dec_c['high']
                            dec_bot = min(dec_c['open'], dec_c['close'])
                            has_fvg = (candles[best_mid + 1]['high'] < candles[best_mid - 1]['low']) if best_mid + 1 < n else False
                            if has_fvg:
                                for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                    if candles[t]['high'] >= dec_bot * 1.0005:
                                        tap_c = candles[t]
                                        curr_4h_start = tap_c['time'] - (tap_c['time'] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        btc_pump = (btc_c['close'] - btc_c['open']) / btc_c['open'] if btc_c else 0.0
                                        sentry1_clean = btc_pump < 0.020

                                        c_range = tap_c['high'] - tap_c['low']
                                        swept = any(candles[k]['high'] > idm_high for k in range(low_idx, t + 1))
                                        u_wick = tap_c['high'] - max(tap_c['open'], tap_c['close'])
                                        w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                        mt = (dec_top + dec_bot) / 2.0

                                        if swept and w_ratio >= 0.18 and tap_c['close'] <= mt and sentry1_clean:
                                            entry = dec_bot
                                            tp_p = entry * (1.0 - std_tp_pct)
                                            soft_sl_p = entry * (1.0 + soft_sl_pct)
                                            hard_sl_p = entry * (1.0 + hard_sl_pct)

                                            # H2
                                            res = None; exit_p = entry; exit_t = tap_c['time']; exit_reason = 'HOLD_EXPIRY'
                                            for m in range(t, min(t + max_hold, n)):
                                                if candles[m]['low'] <= tp_p:
                                                    res = 'WIN'; exit_p = tp_p; exit_t = candles[m]['time']; exit_reason = 'TP_HIT'; break
                                                if candles[m]['high'] >= hard_sl_p:
                                                    res = 'LOSS'; exit_p = max(hard_sl_p, candles[m]['open']); exit_t = candles[m]['time']; exit_reason = 'HARD_SL'; break
                                                if candles[m]['close'] <= soft_sl_p:
                                                    res = 'LOSS'; exit_p = candles[m]['close']; exit_t = candles[m]['time']; exit_reason = 'SOFT_SL'; break
                                            if not res:
                                                fc = candles[min(t + max_hold, n - 1)]['close']
                                                res = 'WIN' if fc <= entry else 'LOSS'
                                                exit_p = fc
                                                exit_t = candles[min(t + max_hold, n - 1)]['time']

                                            h2_signals.append({
                                                'sym': sym, 'side': 'SHORT', 'tf': tf, 'time': tap_c['time'],
                                                'exit_time': exit_t, 'entry': entry, 'exit': exit_p,
                                                'gross': (entry - exit_p) / entry, 'res': res, 'exit_reason': exit_reason
                                            })

                                            # H3A
                                            res_3 = None; exit_p_3 = entry; exit_t_3 = tap_c['time']; exit_reason_3 = 'HOLD_EXPIRY'
                                            curr_soft_sl = soft_sl_p
                                            armor_stage = 0
                                            for m in range(t, min(t + max_hold, n)):
                                                low_so_far = candles[m]['low']
                                                if low_so_far <= entry * (1.0 - 0.016):
                                                    curr_soft_sl = min(curr_soft_sl, entry * (1.0 - 0.002))
                                                    armor_stage = max(armor_stage, 1)
                                                if low_so_far <= entry * (1.0 - 0.022):
                                                    curr_soft_sl = min(curr_soft_sl, entry * (1.0 - 0.012))
                                                    armor_stage = max(armor_stage, 2)

                                                if candles[m]['low'] <= tp_p:
                                                    res_3 = 'WIN'; exit_p_3 = tp_p; exit_t_3 = candles[m]['time']; exit_reason_3 = 'TP_HIT'; break
                                                if candles[m]['high'] >= hard_sl_p:
                                                    res_3 = 'LOSS'; exit_p_3 = max(hard_sl_p, candles[m]['open']); exit_t_3 = candles[m]['time']; exit_reason_3 = 'HARD_SL'; break
                                                if candles[m]['close'] >= curr_soft_sl:
                                                    res_3 = 'WIN' if curr_soft_sl < entry else 'LOSS'
                                                    exit_p_3 = candles[m]['close']
                                                    exit_t_3 = candles[m]['time']
                                                    exit_reason_3 = f'ARMOR_STAGE_{armor_stage}' if armor_stage > 0 else 'SOFT_SL'
                                                    break
                                            if not res_3:
                                                fc = candles[min(t + max_hold, n - 1)]['close']
                                                res_3 = 'WIN' if fc <= entry else 'LOSS'
                                                exit_p_3 = fc
                                                exit_t_3 = candles[min(t + max_hold, n - 1)]['time']

                                            h3a_signals.append({
                                                'sym': sym, 'side': 'SHORT', 'tf': tf, 'time': tap_c['time'],
                                                'exit_time': exit_t_3, 'entry': entry, 'exit': exit_p_3,
                                                'gross': (entry - exit_p_3) / entry, 'res': res_3, 'exit_reason': exit_reason_3
                                            })
                                        break

def detailed_sim(signals, name):
    signals.sort(key=lambda x: x['time'])
    executed = []
    active_exit = 0
    for s in signals:
        if s['time'] >= active_exit:
            executed.append(s)
            active_exit = s['exit_time']

    exit_counts = {}
    tf_counts = {'1h': {'W': 0, 'L': 0}, '4h': {'W': 0, 'L': 0}}
    side_counts = {'LONG': {'W': 0, 'L': 0}, 'SHORT': {'W': 0, 'L': 0}}
    coin_counts = {}

    streak_w = 0; max_streak_w = 0
    streak_l = 0; max_streak_l = 0

    milestones = {100: None, 250: None, 500: None, 1000: None, 2000: None, 5000: None, 10000: None}

    cap = 50.0
    vault = 0.0
    for idx, t in enumerate(executed):
        net_move = t['gross'] - 0.0016
        pos = cap * 5.0
        pnl = pos * net_move
        r = t['exit_reason']
        exit_counts[r] = exit_counts.get(r, 0) + 1
        tf = t['tf']
        side = t['side']
        sym = t['sym']
        if sym not in coin_counts: coin_counts[sym] = {'W': 0, 'L': 0}

        if t['res'] == 'WIN':
            tf_counts[tf]['W'] += 1
            side_counts[side]['W'] += 1
            coin_counts[sym]['W'] += 1
            cap += pnl * 0.85
            vault += pnl * 0.15
            streak_w += 1
            streak_l = 0
            if streak_w > max_streak_w: max_streak_w = streak_w
        else:
            tf_counts[tf]['L'] += 1
            side_counts[side]['L'] += 1
            coin_counts[sym]['L'] += 1
            cap += pnl
            if cap < 2.0: cap = 0.0
            streak_l += 1
            streak_w = 0
            if streak_l > max_streak_l: max_streak_l = streak_l

        tot = cap + vault
        for m in milestones:
            if tot >= m and milestones[m] is None:
                milestones[m] = idx + 1

    print(f'=== {name} ===')
    print('Total Executed:', len(executed))
    print('Max Win Streak:', max_streak_w, '| Max Loss Streak:', max_streak_l)
    print('Milestones:', milestones)
    print('Exit Reasons:', exit_counts)
    t1_tot = tf_counts['1h']['W'] + tf_counts['1h']['L']
    t4_tot = tf_counts['4h']['W'] + tf_counts['4h']['L']
    print(f'TF Stats: 1H: {tf_counts["1h"]["W"]}W / {tf_counts["1h"]["L"]}L ({round(tf_counts["1h"]["W"]/t1_tot*100, 1)}%) | 4H: {tf_counts["4h"]["W"]}W / {tf_counts["4h"]["L"]}L ({round(tf_counts["4h"]["W"]/t4_tot*100, 1)}%)')
    sl_tot = side_counts['LONG']['W'] + side_counts['LONG']['L']
    ss_tot = side_counts['SHORT']['W'] + side_counts['SHORT']['L']
    print(f'Side Stats: LONG: {side_counts["LONG"]["W"]}W / {side_counts["LONG"]["L"]}L ({round(side_counts["LONG"]["W"]/sl_tot*100, 1)}%) | SHORT: {side_counts["SHORT"]["W"]}W / {side_counts["SHORT"]["L"]}L ({round(side_counts["SHORT"]["W"]/ss_tot*100, 1)}%)')
    sorted_coins = sorted(coin_counts.items(), key=lambda x: (x[1]['W']/(x[1]['W']+x[1]['L']) if (x[1]['W']+x[1]['L'])>0 else 0), reverse=True)
    print('Top 5 Coins:', [(c[0], f"{c[1]['W']}W/{c[1]['L']}L", f"{round(c[1]['W']/(c[1]['W']+c[1]['L'])*100, 1)}%") for c in sorted_coins[:5]])
    print()

detailed_sim(h2_signals, 'HERMES 2.0 APEX')
detailed_sim(h3a_signals, 'HERMES 3.0-A DYNAMIC ARMOR')
