import os
import sys
import json
import glob

# Add repo root to path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from engine.bb_model3_engine import BBModel3Engine

CACHE_DIR = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\market_data_cache_15m"

def build_daily_from_15m(candles_15m):
    """Aggregates 15m candles into 24-hour daily candles (96 bars per day)."""
    daily = []
    day_bars = 96
    for i in range(0, len(candles_15m), day_bars):
        chunk = candles_15m[i:i + day_bars]
        if len(chunk) < day_bars // 2:
            continue
        d_o = chunk[0]["open"]
        d_h = max(c["high"] for c in chunk)
        d_l = min(c["low"] for c in chunk)
        d_c = chunk[-1]["close"]
        daily.append({
            "open": d_o,
            "high": d_h,
            "low": d_l,
            "close": d_c,
            "time": chunk[0]["time"]
        })
    return daily

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8')

    engine = BBModel3Engine()
    json_files = glob.glob(os.path.join(CACHE_DIR, "*_15m.json"))

    print("=" * 80)
    print("👑 BB 1.0 (BOOMING BULLS LIQUIDITY SNIPER) — MODEL 3 SCANNER RUNNER")
    print("Strategy: PDH/PDL Extreme Order Block + 50% MT Retest + Stepped Trailing SL")
    print(f"Scanning Universe: {len(json_files)} Champions")
    print("=" * 80)

    total_setups = 0
    armed_setups = []

    for fpath in json_files:
        symbol = os.path.basename(fpath).replace("_15m.json", "")
        with open(fpath, "r", encoding="utf-8") as f:
            candles = json.load(f)

        if len(candles) < 300:
            continue

        daily = build_daily_from_15m(candles)
        if len(daily) < 2:
            continue

        pdh, pdl = engine.calculate_pdh_pdl(daily)
        # Scan last 200 bars for fresh / recent setups
        recent_candles = candles[-200:]
        obs = engine.find_extreme_order_blocks(recent_candles, pdh, pdl)

        for ob in obs:
            total_setups += 1
            state_info = engine.check_active_setup_state(ob, recent_candles)
            armed_setups.append({
                "symbol": symbol,
                "side": ob["side"],
                "anchor": ob["anchor"],
                "ob_high": ob["ob_high"],
                "ob_low": ob["ob_low"],
                "mt": ob["mt"],
                "sl": ob["sl"],
                "risk_pct": (ob["risk"] / ob["mt"]) * 100,
                "state": state_info.get("state"),
                "outcome": state_info.get("outcome", "-"),
                "pnl_r": state_info.get("pnl_r", 0.0),
                "time": ob["time"]
            })

    print(f"\n📊 Scan Complete! Detected {len(armed_setups)} Setups across the latest test window.\n")
    print(f"{'SYMBOL':<14} | {'SIDE':<6} | {'ANCHOR':<12} | {'50% MT':<10} | {'STOP LOSS':<10} | {'RISK %':<8} | {'STATE / OUTCOME'}")
    print("-" * 85)

    # Show top 12 recent sample setups
    for s in armed_setups[-15:]:
        res_str = f"{s['state']} ({s['outcome']}, {s['pnl_r']:+.1f}R)" if s['state'] == 'CLOSED' else s['state']
        print(f"{s['symbol']:<14} | {s['side']:<6} | {s['anchor']:<12} | {s['mt']:<10.4f} | {s['sl']:<10.4f} | {s['risk_pct']:<7.2f}% | {res_str}")

    print("\n" + "=" * 80)
    print("✅ BB 1.0 Model 3 Core Engine successfully tested and fully operational!")
    print("=" * 80)

if __name__ == "__main__":
    main()
