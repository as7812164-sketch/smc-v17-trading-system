import json
from pathlib import Path
from typing import List, Dict, Any

def compute_atr(candles: List[Dict[str, Any]], period: int = 14) -> List[float]:
    atrs = [0.0] * len(candles)
    if len(candles) < period + 1:
        return atrs
    tr_list = [0.0]
    for i in range(1, len(candles)):
        h = candles[i]["high"]
        l = candles[i]["low"]
        pc = candles[i-1]["close"]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        tr_list.append(tr)
    first_atr = sum(tr_list[1:period+1]) / period
    atrs[period] = first_atr
    curr_atr = first_atr
    for i in range(period + 1, len(candles)):
        curr_atr = (curr_atr * (period - 1) + tr_list[i]) / period
        atrs[i] = curr_atr
    return atrs

def run_test(candles, symbol, min_disp_pct, entry_type="BOUNDARY_5PCT", tp_rr=2.5, be_rr=1.2, lock_rr=1.8):
    n = len(candles)
    atrs = compute_atr(candles, 14)
    trades = []
    active_trade = None
    min_maturation = 18
    active_obs = []

    for i in range(25, n):
        c = candles[i]
        curr_t = c["time"]
        o, h, l, cl = c["open"], c["high"], c["low"], c["close"]
        curr_atr = atrs[i] or (c["close"] * 0.005)

        if active_trade is not None:
            side = active_trade["side"]
            entry_p = active_trade["entry_price"]
            sl_p = active_trade["sl_price"]
            tp_p = active_trade["tp_price"]
            be_p = active_trade["be_price"]
            lock_p = active_trade["lock_price"]
            lock_trig_p = active_trade["lock_trigger_price"]
            stage = active_trade["stage"]
            bars_held = i - active_trade["entry_bar"]

            exit_trade = False
            exit_price = 0.0
            exit_reason = ""

            if side == "BUY":
                if h >= tp_p:
                    exit_trade = True
                    exit_price = tp_p
                    exit_reason = "TP"
                elif l <= sl_p:
                    exit_trade = True
                    exit_price = sl_p
                    exit_reason = "SL"
                else:
                    if stage == 0 and h >= be_p:
                        active_trade["sl_price"] = entry_p
                        active_trade["stage"] = 1
                    elif stage == 1 and h >= lock_trig_p:
                        active_trade["sl_price"] = lock_p
                        active_trade["stage"] = 2
            else:
                if l <= tp_p:
                    exit_trade = True
                    exit_price = tp_p
                    exit_reason = "TP"
                elif h >= sl_p:
                    exit_trade = True
                    exit_price = sl_p
                    exit_reason = "SL"
                else:
                    if stage == 0 and l <= be_p:
                        active_trade["sl_price"] = entry_p
                        active_trade["stage"] = 1
                    elif stage == 1 and l <= lock_trig_p:
                        active_trade["sl_price"] = lock_p
                        active_trade["stage"] = 2

            if exit_trade:
                pnl_pct = (exit_price - entry_p) / entry_p * 100.0 if side == "BUY" else (entry_p - exit_price) / entry_p * 100.0
                trades.append({
                    "symbol": symbol,
                    "side": side,
                    "pnl_pct": pnl_pct,
                    "result": exit_reason,
                    "stage": active_trade["stage"]
                })
                active_trade = None

        # Clean OBs
        surviving = []
        for ob in active_obs:
            if ob["side"] == "BUY" and cl < ob["ob_low"]:
                continue
            if ob["side"] == "SELL" and cl > ob["ob_high"]:
                continue
            if (i - ob["bar_idx"]) > 180:
                continue
            surviving.append(ob)
        active_obs = surviving

        # New OBs at i-2
        c3, c2, c1 = candles[i-2], candles[i-1], candles[i]
        
        # Bullish
        if c3["close"] < c3["open"] and c1["low"] > c3["high"]:
            disp_pct = (max(c1["high"], c2["high"]) - c3["low"]) / c3["low"] * 100.0
            if disp_pct >= min_disp_pct:
                ob_high = max(c3["open"], c3["high"])
                ob_low = c3["low"]
                ob_range = ob_high - ob_low
                ent = (ob_high - ob_range * 0.05) if entry_type == "BOUNDARY_5PCT" else (ob_high + ob_low) / 2.0
                active_obs.append({
                    "side": "BUY", "bar_idx": i-2, "ob_high": ob_high, "ob_low": ob_low,
                    "entry_price": ent, "atr": curr_atr, "tapped": False
                })

        # Bearish
        if c3["close"] > c3["open"] and c1["high"] < c3["low"]:
            disp_pct = (c3["high"] - min(c1["low"], c2["low"])) / c3["high"] * 100.0
            if disp_pct >= min_disp_pct:
                ob_high = c3["high"]
                ob_low = min(c3["open"], c3["low"])
                ob_range = ob_high - ob_low
                ent = (ob_low + ob_range * 0.05) if entry_type == "BOUNDARY_5PCT" else (ob_high + ob_low) / 2.0
                active_obs.append({
                    "side": "SELL", "bar_idx": i-2, "ob_high": ob_high, "ob_low": ob_low,
                    "entry_price": ent, "atr": curr_atr, "tapped": False
                })

        # Retest on mature OB
        if active_trade is None:
            for ob in active_obs:
                if ob["tapped"]:
                    continue
                bars_alive = i - ob["bar_idx"]
                if bars_alive < min_maturation:
                    if (ob["side"] == "BUY" and l <= ob["entry_price"]) or (ob["side"] == "SELL" and h >= ob["entry_price"]):
                        ob["tapped"] = True
                    continue

                can_enter = False
                if ob["side"] == "BUY" and l <= ob["entry_price"] and cl >= ob["ob_low"]:
                    can_enter = True
                elif ob["side"] == "SELL" and h >= ob["entry_price"] and cl <= ob["ob_high"]:
                    can_enter = True

                if can_enter:
                    ob["tapped"] = True
                    ent_p = ob["entry_price"]
                    side = ob["side"]
                    atr_v = ob["atr"]
                    
                    # Risk distance: entry to OB boundary + 0.3*ATR buffer
                    if side == "BUY":
                        risk_dist = ent_p - (ob["ob_low"] - 0.3 * atr_v)
                        sl_price = ent_p - risk_dist
                        tp_price = ent_p + (risk_dist * tp_rr)
                        be_price = ent_p + (risk_dist * be_rr)
                        lock_trig = ent_p + (risk_dist * lock_rr)
                        lock_price = ent_p + (risk_dist * 0.8)
                    else:
                        risk_dist = (ob["ob_high"] + 0.3 * atr_v) - ent_p
                        sl_price = ent_p + risk_dist
                        tp_price = ent_p - (risk_dist * tp_rr)
                        be_price = ent_p - (risk_dist * be_rr)
                        lock_trig = ent_p - (risk_dist * lock_rr)
                        lock_price = ent_p - (risk_dist * 0.8)

                    active_trade = {
                        "side": side, "entry_bar": i, "entry_time": curr_t,
                        "entry_price": ent_p, "tp_price": tp_price, "sl_price": sl_price,
                        "be_price": be_price, "lock_price": lock_price,
                        "lock_trigger_price": lock_trig, "stage": 0
                    }
                    break

    tot = len(trades)
    wins = [t for t in trades if t["pnl_pct"] > 0]
    be = [t for t in trades if abs(t["pnl_pct"]) < 0.0001]
    losses = [t for t in trades if t["pnl_pct"] < -0.0001]
    w_count, l_count, b_count = len(wins), len(losses), len(be)
    safe_wr = round((w_count + b_count) / tot * 100.0, 1) if tot > 0 else 0.0
    pure_wr = round(w_count / tot * 100.0, 1) if tot > 0 else 0.0
    gross_p = sum(t["pnl_pct"] for t in wins)
    gross_l = abs(sum(t["pnl_pct"] for t in losses))
    pf = round(gross_p / gross_l, 2) if gross_l > 0 else 99.0
    net = round(gross_p - gross_l, 2)
    return {"trades": tot, "pure_wr": pure_wr, "safe_wr": safe_wr, "pf": pf, "net_pnl": net}

forex_files = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "XAUUSD"]
forex_dir = Path("historical_data_forex")

data_map = {}
for sym in forex_files:
    p = forex_dir / f"{sym}_1h.json"
    if p.exists():
        data_map[sym] = json.loads(p.read_text())

print(f"{'PAIR':<8} | {'BOUNDARY 5% (Disp 0.5%)':<24} | {'BOUNDARY 5% (Disp 0.8%)':<24} | {'50% MT ENTRY (Disp 0.5%)':<24}")
print("-" * 88)

for sym in forex_files:
    if sym not in data_map:
        continue
    c = data_map[sym]
    # Disp 0.5% (or 1.5% for Gold)
    disp1 = 1.5 if sym == "XAUUSD" else 0.5
    disp2 = 2.5 if sym == "XAUUSD" else 0.8
    r1 = run_test(c, sym, min_disp_pct=disp1, entry_type="BOUNDARY_5PCT")
    r2 = run_test(c, sym, min_disp_pct=disp2, entry_type="BOUNDARY_5PCT")
    r3 = run_test(c, sym, min_disp_pct=disp1, entry_type="50MT")
    
    col1 = f"T:{r1['trades']:<3} WR:{r1['safe_wr']}% PF:{r1['pf']}"
    col2 = f"T:{r2['trades']:<3} WR:{r2['safe_wr']}% PF:{r2['pf']}"
    col3 = f"T:{r3['trades']:<3} WR:{r3['safe_wr']}% PF:{r3['pf']}"
    print(f"{sym:<8} | {col1:<24} | {col2:<24} | {col3:<24}")
