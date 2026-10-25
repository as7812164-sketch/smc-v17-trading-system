import json
import os
import sys
import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOP_22_CHAMPIONS = [
    "DOGEUSDT", "ALGOUSDT", "FETUSDT", "SANDUSDT", "BTCUSDT", "THETAUSDT", "OPUSDT", "FILUSDT",
    "RENDERUSDT", "RUNEUSDT", "AVAXUSDT", "SHIBUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", "LDOUSDT",
    "MKRUSDT", "UNIUSDT", "AAVEUSDT", "GALAUSDT", "ICPUSDT", "PYTHUSDT"
]

DATA_DIR = "historical_data_2year"
CANDLE_CACHE = {}

def load_candles(sym, tf):
    key = (sym, tf)
    if key in CANDLE_CACHE:
        return CANDLE_CACHE[key]
    fpath = os.path.join(DATA_DIR, f"{sym}_{tf}.json")
    if not os.path.exists(fpath): return []
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    for c in data:
        c["open"] = float(c["open"])
        c["high"] = float(c["high"])
        c["low"] = float(c["low"])
        c["close"] = float(c["close"])
        c["volume"] = float(c.get("volume", 0.0))
    CANDLE_CACHE[key] = data
    return data

# Pre-load all candles into RAM
print("[*] Pre-loading 22 coins into RAM...")
for sym in TOP_22_CHAMPIONS:
    for tf in ["4h", "1h"]:
        load_candles(sym, tf)

btc_4h = load_candles("BTCUSDT", "4h")
btc_map_4h = {c["time"]: c for c in btc_4h}

setups_by_tf = {"1h": [], "4h": []}

for tf in ["4h", "1h"]:
    std_tp_pct = 0.028 if tf == "4h" else 0.022
    soft_sl_pct = 0.028 if tf == "4h" else 0.025
    hard_sl_pct = 0.038 if tf == "4h" else 0.036
    max_tap_window = 28
    max_hold = 30 if tf == "4h" else 40

    for sym in TOP_22_CHAMPIONS:
        candles = load_candles(sym, tf)
        n = len(candles)
        if n < 40: continue

        atr = [0.0] * n
        for k in range(1, n):
            tr = max(candles[k]["high"] - candles[k]["low"],
                     abs(candles[k]["high"] - candles[k-1]["close"]),
                     abs(candles[k]["low"] - candles[k-1]["close"]))
            atr[k] = tr if k < 14 else (atr[k-1] * 13 + tr) / 14

        for i in range(20, n - 2):
            # LONG
            if candles[i]["low"] == min(c["low"] for c in candles[max(0, i-15):i+1]):
                sub_w = candles[i:min(i+16, n)]
                highs = [c["high"] for c in sub_w]
                max_high = max(highs)
                high_idx = i + highs.index(max_high)
                if high_idx > i + 2:
                    gain = (max_high - candles[i]["low"]) / candles[i]["low"]
                    if gain >= 0.050:
                        idm_low = candles[high_idx - 1]["low"]
                        best_mid = -1; max_bg = 0.0
                        for mid in range(i+1, high_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["low"]
                            fib = (candles[mid]["low"] - candles[i]["low"]) / (max_high - candles[i]["low"])
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg; best_mid = mid
                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = max(dec_c["open"], dec_c["close"])
                            dec_bot = dec_c["low"]
                            has_fvg = (candles[best_mid + 1]["low"] > candles[best_mid - 1]["high"]) if best_mid + 1 < n else False
                            if has_fvg:
                                for t in range(high_idx + 1, min(high_idx + max_tap_window, n)):
                                    if candles[t]["low"] <= dec_top * 1.0005:
                                        tap_c = candles[t]
                                        c_range = tap_c["high"] - tap_c["low"]
                                        swept = any(candles[k]["low"] < idm_low for k in range(high_idx, t + 1))
                                        l_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                                        w_ratio = (l_wick / c_range) if c_range > 0 else 0
                                        mt = (dec_top + dec_bot) / 2.0
                                        
                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        btc_dump = (btc_c["open"] - btc_c["close"]) / btc_c["open"] if btc_c else 0.0
                                        
                                        if btc_dump < 0.020 and swept and w_ratio >= 0.18 and tap_c["close"] >= mt:
                                            setups_by_tf[tf].append({
                                                "sym": sym, "tf": tf, "t_idx": t, "side": "LONG",
                                                "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                "hard_sl_pct": hard_sl_pct, "max_hold": max_hold
                                            })
                                            break

            # SHORT
            if candles[i]["high"] == max(c["high"] for c in candles[max(0, i-15):i+1]):
                sub_w = candles[i:min(i+16, n)]
                lows = [c["low"] for c in sub_w]
                min_low = min(lows)
                low_idx = i + lows.index(min_low)
                if low_idx > i + 2:
                    drop = (candles[i]["high"] - min_low) / candles[i]["high"]
                    if drop >= 0.050:
                        idm_high = candles[low_idx - 1]["high"]
                        best_mid = -1; max_bg = 0.0
                        for mid in range(i+1, low_idx):
                            bg = (candles[mid]["high"] - candles[mid]["low"]) / candles[mid]["high"]
                            fib = (candles[i]["high"] - candles[mid]["high"]) / (candles[i]["high"] - min_low)
                            if 0.30 <= fib <= 0.70 and bg > max_bg:
                                max_bg = bg; best_mid = mid
                        if best_mid != -1:
                            dec_c = candles[best_mid - 1]
                            dec_top = dec_c["high"]
                            dec_bot = min(dec_c["open"], dec_c["close"])
                            has_bear_fvg = (candles[best_mid + 1]["high"] < candles[best_mid - 1]["low"]) if best_mid + 1 < n else False
                            if has_bear_fvg:
                                for t in range(low_idx + 1, min(low_idx + max_tap_window, n)):
                                    if candles[t]["high"] >= dec_bot * 0.9995:
                                        tap_c = candles[t]
                                        c_range = tap_c["high"] - tap_c["low"]
                                        swept = any(candles[k]["high"] > idm_high for k in range(low_idx, t + 1))
                                        u_wick = tap_c["high"] - max(tap_c["open"], tap_c["close"])
                                        w_ratio = (u_wick / c_range) if c_range > 0 else 0
                                        mt = (dec_top + dec_bot) / 2.0

                                        curr_4h_start = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                                        prev_4h_ts = curr_4h_start - (4 * 3600 * 1000)
                                        btc_c = btc_map_4h.get(prev_4h_ts)
                                        btc_pump = (btc_c["close"] - btc_c["open"]) / btc_c["open"] if btc_c else 0.0

                                        if btc_pump < 0.020 and swept and w_ratio >= 0.18 and tap_c["close"] <= mt:
                                            setups_by_tf[tf].append({
                                                "sym": sym, "tf": tf, "t_idx": t, "side": "SHORT",
                                                "time": tap_c["time"], "dec_top": dec_top, "dec_bot": dec_bot,
                                                "mt": mt, "tap_low": tap_c["low"], "tap_high": tap_c["high"],
                                                "atr": atr[t], "std_tp_pct": std_tp_pct, "soft_sl_pct": soft_sl_pct,
                                                "hard_sl_pct": hard_sl_pct, "max_hold": max_hold
                                            })
                                            break

print("[*] Evaluating trade outcomes with Hermes 3.0 rules...")
all_signals = []
for tf in ["4h", "1h"]:
    for s in setups_by_tf[tf]:
        sym = s["sym"]
        candles = load_candles(sym, tf)
        n = len(candles)
        t = s["t_idx"]
        side = s["side"]
        mt = s["mt"]

        if side == "LONG":
            entry = mt if s["tap_low"] <= mt else (s["dec_top"] + mt) / 2.0
            tp_p = entry * (1.0 + s["std_tp_pct"])
            struct_sl = min(s["dec_bot"], s["tap_low"]) - 0.20 * s["atr"]
            min_sl = entry * (1.0 - s["soft_sl_pct"])
            soft_sl_p = max(struct_sl, min_sl)
            hard_sl_p = entry * (1.0 - s["hard_sl_pct"])
        else:
            entry = mt if s["tap_high"] >= mt else (s["dec_bot"] + mt) / 2.0
            tp_p = entry * (1.0 - s["std_tp_pct"])
            struct_sl = max(s["dec_top"], s["tap_high"]) + 0.20 * s["atr"]
            max_sl = entry * (1.0 + s["soft_sl_pct"])
            soft_sl_p = min(struct_sl, max_sl)
            hard_sl_p = entry * (1.0 + s["hard_sl_pct"])

        res = None; exit_p = entry; exit_t = s["time"]
        curr_sl = soft_sl_p
        stage1_locked = False
        stage2_locked = False

        for m in range(t, min(t + s["max_hold"], n)):
            b_high = candles[m]["high"]
            b_low = candles[m]["low"]
            b_close = candles[m]["close"]

            if side == "LONG":
                m_4h_ts = (candles[m]["time"] - (candles[m]["time"] % (4 * 3600 * 1000))) - (4 * 3600 * 1000)
                btc_c = btc_map_4h.get(m_4h_ts)
                if btc_c and ((btc_c["open"] - btc_c["close"]) / btc_c["open"] >= 0.025):
                    if b_close > entry:
                        res = "BTC_SHIELD_EXIT"; exit_p = b_close; exit_t = candles[m]["time"]; break

                if b_high >= entry * 1.016 and not stage1_locked:
                    curr_sl = max(curr_sl, entry * 1.001)
                    stage1_locked = True
                if b_high >= entry * 1.022 and not stage2_locked:
                    curr_sl = max(curr_sl, entry * 1.008)
                    stage2_locked = True

                if b_high >= tp_p:
                    res = "TP_HIT"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                if b_low <= hard_sl_p:
                    res = "HARD_SL_HIT"; exit_p = min(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                if b_close <= curr_sl:
                    res = "SCRATCH_BE" if stage1_locked else "SL_HIT"
                    exit_p = b_close; exit_t = candles[m]["time"]; break
            else: # SHORT
                m_4h_ts = (candles[m]["time"] - (candles[m]["time"] % (4 * 3600 * 1000))) - (4 * 3600 * 1000)
                btc_c = btc_map_4h.get(m_4h_ts)
                if btc_c and ((btc_c["close"] - btc_c["open"]) / btc_c["open"] >= 0.025):
                    if b_close < entry:
                        res = "BTC_SHIELD_EXIT"; exit_p = b_close; exit_t = candles[m]["time"]; break

                if b_low <= entry * 0.984 and not stage1_locked:
                    curr_sl = min(curr_sl, entry * 0.999)
                    stage1_locked = True
                if b_low <= entry * 0.978 and not stage2_locked:
                    curr_sl = min(curr_sl, entry * 0.992)
                    stage2_locked = True

                if b_low <= tp_p:
                    res = "TP_HIT"; exit_p = tp_p; exit_t = candles[m]["time"]; break
                if b_high >= hard_sl_p:
                    res = "HARD_SL_HIT"; exit_p = max(hard_sl_p, candles[m]["open"]); exit_t = candles[m]["time"]; break
                if b_close >= curr_sl:
                    res = "SCRATCH_BE" if stage1_locked else "SL_HIT"
                    exit_p = b_close; exit_t = candles[m]["time"]; break

        if not res:
            fc = candles[min(t + s["max_hold"], n - 1)]["close"]
            if side == "LONG":
                res = "TP_HIT" if fc >= tp_p * 0.995 else ("SCRATCH_BE" if fc >= entry else "TIMEOUT_CLOSE")
            else:
                res = "TP_HIT" if fc <= tp_p * 1.005 else ("SCRATCH_BE" if fc <= entry else "TIMEOUT_CLOSE")
            exit_p = fc
            exit_t = candles[min(t + s["max_hold"], n - 1)]["time"]

        gross_pct = (exit_p - entry) / entry if side == "LONG" else (entry - exit_p) / entry
        all_signals.append({
            "sym": sym, "tf": tf, "side": side,
            "entry_time": s["time"], "exit_time": exit_t,
            "entry": entry, "exit": exit_p,
            "res": res, "gross_pct": gross_pct
        })

all_signals.sort(key=lambda x: x["entry_time"])
print(f"[*] Total chronological signals: {len(all_signals)}")

# ---------------- SIMULATE 4 INDEPENDENT QUAD COMPOUNDING ACCOUNTS ----------------
class CompoundingAccount:
    def __init__(self, name, channel, tf, exchange, initial_balance=50.0, target=2000.0):
        self.name = name
        self.channel = channel
        self.tf = tf
        self.exchange = exchange
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.target = target
        self.trades = []
        self.free_at = 0
        self.milestones = {}
        self.peak_balance = initial_balance
        self.max_dd = 0.0
        self.start_time = None

    def check_milestones(self, trade_num, trade_time_ms):
        if not self.start_time:
            self.start_time = trade_time_ms
        days_elapsed = (trade_time_ms - self.start_time) / (1000 * 3600 * 24)
        date_str = datetime.datetime.fromtimestamp(trade_time_ms / 1000, datetime.timezone.utc).strftime("%Y-%m-%d")

        for m in [100, 250, 500, 1000, 2000]:
            if self.balance >= m and m not in self.milestones:
                self.milestones[m] = {
                    "trade_num": trade_num,
                    "days": round(days_elapsed, 1),
                    "date": date_str,
                    "balance": round(self.balance, 2)
                }

    def execute_trade(self, sig):
        if not self.start_time:
            self.start_time = sig["entry_time"]

        margin = self.balance
        leverage = 5.0
        notional = margin * leverage
        fee = notional * 0.0008
        raw_pnl = notional * sig["gross_pct"]
        net_pnl = raw_pnl - fee

        self.balance += net_pnl
        if self.balance < 1.0: self.balance = 0.0

        if self.balance > self.peak_balance:
            self.peak_balance = self.balance
        dd = (self.peak_balance - self.balance) / self.peak_balance * 100.0 if self.peak_balance > 0 else 0.0
        if dd > self.max_dd: self.max_dd = dd

        self.free_at = sig["exit_time"]
        t_num = len(self.trades) + 1
        is_win = sig["res"] in ["TP_HIT", "BTC_SHIELD_EXIT"] or (sig["res"] == "SCRATCH_BE" and net_pnl >= 0)

        trade_record = {
            "num": t_num, "sym": sig["sym"], "side": sig["side"],
            "res": sig["res"], "is_win": is_win,
            "net_pnl": round(net_pnl, 2), "balance_after": round(self.balance, 2),
            "entry_time": sig["entry_time"], "exit_time": sig["exit_time"]
        }
        self.trades.append(trade_record)
        self.check_milestones(t_num, sig["exit_time"])

accounts = {
    "binance_4h": CompoundingAccount("Binance 4H Macro", "binance_4h", "4h", "BINANCE"),
    "binance_1h": CompoundingAccount("Binance 1H Intraday", "binance_1h", "1h", "BINANCE"),
    "bitget_4h": CompoundingAccount("Bitget 4H Macro", "bitget_4h", "4h", "BITGET"),
    "bitget_1h": CompoundingAccount("Bitget 1H Intraday", "bitget_1h", "1h", "BITGET")
}

active_coins_until = {}

for s in all_signals:
    sig_time = s["entry_time"]
    sig_tf = s["tf"]
    sym = s["sym"]

    active_coins_until = {c: exp for c, exp in active_coins_until.items() if exp > sig_time}
    if sym in active_coins_until:
        continue

    candidates = [accounts["binance_4h"], accounts["bitget_4h"]] if sig_tf == "4h" else [accounts["binance_1h"], accounts["bitget_1h"]]

    chosen = None
    for acc in candidates:
        if acc.free_at <= sig_time and acc.balance > 0:
            chosen = acc
            break

    if chosen:
        chosen.execute_trade(s)
        active_coins_until[sym] = s["exit_time"]

out_data = {}
for acc_key, acc in accounts.items():
    wins = sum(1 for t in acc.trades if t["is_win"])
    total = len(acc.trades)
    wr = (wins / total * 100.0) if total > 0 else 0.0
    out_data[acc_key] = {
        "name": acc.name,
        "tf": acc.tf,
        "exchange": acc.exchange,
        "total_trades": total,
        "wins": wins,
        "losses": total - wins,
        "win_rate": round(wr, 2),
        "max_drawdown": round(acc.max_dd, 2),
        "milestones": acc.milestones
    }

print("\n=== QUAD COMPOUNDING HERMES 3.0 AUDIT RESULTS ===")
print(json.dumps(out_data, indent=2))
with open("quad_compounding_hermes3_results.json", "w", encoding="utf-8") as f:
    json.dump(out_data, f, indent=2)
