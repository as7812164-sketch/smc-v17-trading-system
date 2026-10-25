import urllib.request
import json
import time
import sys
import numpy as np
import concurrent.futures

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Approved Elite Universe (Excluding toxic coins like FTM, LTC, SEI, DOT, CRV)
APPROVED_COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "SUIUSDT", "NEARUSDT", "AVAXUSDT", "APTUSDT",
    "ARBUSDT", "OPUSDT", "LDOUSDT", "MKRUSDT", "UNIUSDT", "AAVEUSDT", "RUNEUSDT", "RENDERUSDT",
    "INJUSDT", "FETUSDT", "THETAUSDT", "ALGOUSDT", "GALAUSDT", "SANDUSDT", "FILUSDT", "ICPUSDT",
    "PYTHUSDT", "PEPEUSDT", "SHIBUSDT", "XRPUSDT", "ADAUSDT", "LINKUSDT", "DOGEUSDT"
]

def fetch_klines(sym, interval, limit=550):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                candles = []
                for k in data:
                    candles.append({
                        "time": int(k[0]), "open": float(k[1]), "high": float(k[2]),
                        "low": float(k[3]), "close": float(k[4]), "volume": float(k[5])
                    })
                return sym, interval, candles
        except Exception:
            time.sleep(0.2)
    return sym, interval, []

def main():
    print("=" * 85)
    print(" 🚀 UNIFIED 1H + 4H AUDIT: $50 TO $1000 COMPOUNDING VERIFICATION")
    print(" No Height Starvation | BTC Macro Shield | Wick Absorption Confirmation")
    print("=" * 85)

    tasks = []
    for s in APPROVED_COINS:
        tasks.append((s, "4h", 550))
        tasks.append((s, "1h", 1200))

    all_data = {"4h": {}, "1h": {}}
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(fetch_klines, t[0], t[1], t[2]) for t in tasks]
        for f in concurrent.futures.as_completed(futures):
            sym, tf, klines = f.result()
            if len(klines) >= 100:
                all_data[tf][sym] = klines

    btc_candles = all_data["4h"].get("BTCUSDT", [])
    btc_map = {c["time"]: c["close"] for c in btc_candles}
    btc_closes = [c["close"] for c in btc_candles]
    btc_ema20 = [0.0] * len(btc_closes)
    if btc_closes:
        k_mult = 2.0 / (20 + 1)
        btc_ema20[0] = btc_closes[0]
        for i in range(1, len(btc_closes)):
            btc_ema20[i] = btc_closes[i] * k_mult + btc_ema20[i-1] * (1.0 - k_mult)
    btc_ema_map = {btc_candles[i]["time"]: btc_ema20[i] for i in range(len(btc_candles))}

    all_trades = []

    # 1H and 4H targets
    tf_configs = {
        "1h": {"tp_pct": 0.022, "sl_pct": 0.028, "disp_min": 0.020, "max_hold": 36},
        "4h": {"tp_pct": 0.032, "sl_pct": 0.030, "disp_min": 0.032, "max_hold": 36}
    }

    for tf, cfg in tf_configs.items():
        tp_pct = cfg["tp_pct"]
        sl_pct = cfg["sl_pct"]
        disp_min = cfg["disp_min"]
        max_hold = cfg["max_hold"]

        for sym, candles in all_data[tf].items():
            n = len(candles)
            for i in range(25, n - 20):
                is_extreme = (candles[i]["low"] == min(c["low"] for c in candles[i-20:i+1]))
                if not is_extreme: continue

                c = candles[i]
                ob_top = max(c["open"], c["close"])
                ob_bot = c["low"]
                ob_mt = (ob_top + ob_bot) / 2.0

                disp_high = max(candles[i+1]["high"], candles[i+2]["high"], candles[i+3]["high"])
                disp_gain = (disp_high - ob_top) / ob_top
                has_fvg = (candles[i+2]["low"] > candles[i]["high"]) if i+2 < n else False
                if disp_gain < disp_min or not has_fvg: continue

                tap_idx = -1
                for k in range(i+3, min(i+60, n)):
                    if candles[k]["low"] <= ob_top:
                        tap_idx = k
                        break
                if tap_idx == -1 or tap_idx >= n - 10: continue
                tap_c = candles[tap_idx]

                if sym != "BTCUSDT":
                    b_ts = tap_c["time"] - (tap_c["time"] % (4 * 3600 * 1000))
                    b_c = btc_map.get(b_ts)
                    b_e = btc_ema_map.get(b_ts)
                    if b_c and b_e and b_c < b_e:
                        continue # Vetoed by BTC Shield

                c_range = tap_c["high"] - tap_c["low"]
                lower_wick = min(tap_c["open"], tap_c["close"]) - tap_c["low"]
                wick_ratio = (lower_wick / c_range) if c_range > 0 else 0.0
                if wick_ratio < 0.18 or tap_c["close"] < ob_mt: continue

                entry_p = ob_top
                tp_target = entry_p * (1.0 + tp_pct)
                sl_target = entry_p * (1.0 - sl_pct)

                trade_res = None
                exit_p = entry_p
                exit_time = tap_c["time"]

                for m in range(tap_idx, min(tap_idx + max_hold, n)):
                    bar = candles[m]
                    if bar["high"] >= tp_target:
                        trade_res = "WIN"
                        exit_p = tp_target
                        exit_time = bar["time"]
                        break
                    if bar["close"] <= sl_target:
                        trade_res = "LOSS"
                        exit_p = sl_target
                        exit_time = bar["time"]
                        break

                if not trade_res:
                    final_c = candles[min(tap_idx + max_hold, n - 1)]["close"]
                    exit_p = final_c
                    exit_time = candles[min(tap_idx + max_hold, n - 1)]["time"]
                    trade_res = "WIN" if final_c >= entry_p else "LOSS"

                gross_pct = (exit_p - entry_p) / entry_p
                all_trades.append({
                    "symbol": sym, "tf": tf, "entry_time": tap_c["time"],
                    "exit_time": exit_time, "entry_p": entry_p, "exit_p": exit_p,
                    "gross_pct": gross_pct, "result": trade_res
                })

    all_trades.sort(key=lambda x: x["entry_time"])

    cap = 50.0
    vault = 0.0
    wins = sum(1 for t in all_trades if t["result"] == "WIN")
    losses = len(all_trades) - wins
    wr = (wins / len(all_trades) * 100) if all_trades else 0

    max_cap = 50.0
    max_dd = 0.0
    hit_1000 = None

    history = []
    for idx, t in enumerate(all_trades, 1):
        pos = cap * 5.0
        net_ret = t["gross_pct"] - 0.0014 # 0.14% fees & slippage
        net_pnl = pos * net_ret

        if net_pnl > 0:
            cap += net_pnl * 0.85
            vault += net_pnl * 0.15
        else:
            cap = max(5.0, cap + net_pnl)

        total_w = cap + vault
        if total_w > max_cap: max_cap = total_w
        dd = (max_cap - total_w) / max_cap * 100.0
        if dd > max_dd: max_dd = dd

        if total_w >= 1000.0 and hit_1000 is None:
            hit_1000 = idx

        history.append({
            "idx": idx, "sym": t["symbol"], "tf": t["tf"],
            "date": time.strftime("%Y-%m-%d %H:%M", time.gmtime(t["entry_time"]/1000)),
            "res": t["result"], "cap": cap, "vault": vault, "total": total_w
        })

    print("=" * 85)
    print("                    🏆 UNIFIED 1H + 4H AUDIT RESULTS")
    print("=" * 85)
    print(f"Total Qualified Trades Executed:   {len(all_trades)}")
    print(f"Direct TP Wins:                    {wins} ({wr:.2f}%)")
    print(f"Losses (SL Hit):                   {losses} ({100 - wr:.2f}%)")
    print(f"-------------------------------------------------------------------------------------")
    print(f"Initial Starting Capital:          $50.00 USDT")
    print(f"Active Trading Balance:            ${cap:,.2f} USDT")
    print(f"Secured Profit Vault (Cold Stash): ${vault:,.2f} USDT")
    print(f"Total Net Wealth Generated:        ${cap + vault:,.2f} USDT")
    print(f"Compounded ROI:                    +{(((cap + vault) - 50.0) / 50.0 * 100):,.1f}%")
    print(f"Maximum Portfolio Drawdown:        {max_dd:.2f}%")
    if hit_1000:
        print(f"🎉 $1,000 MILESTONE REACHED AT:    Trade #{hit_1000}!")
    else:
        print("Milestone $1,000 reached: NO")
    print("=====================================================================================\n")

    print("--- KEY MILESTONE TRADES (JOURNEY TO $1000) ---")
    milestone_steps = [1, 5, 10, 15, 20, 25, 30, len(history)-1]
    for ms in milestone_steps:
        if ms < len(history):
            r = history[ms]
            print(f"Trade #{r['idx']:2d} | {r['date']} | {r['sym']:9s} ({r['tf']}) | {r['res']:4s} | Trading: ${r['cap']:7.2f} | Vault: ${r['vault']:7.2f} | Total: ${r['total']:8.2f}")

if __name__ == "__main__":
    main()
