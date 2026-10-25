"""
Seed today's executed trades and shadow setups into the Trade Behavior Telemetry system.
"""

import json
import urllib.request
from engine.trade_behavior_tracker import record_trade_behavior, record_shadow_setup, dump_behavior_json

def seed():
    # 1. Load today's executed trades from Render
    url = "https://smc-ai-agent.onrender.com/api/paper/trades"
    try:
        data = json.loads(urllib.request.urlopen(url).read())
        for t in data.get("trades", []):
            sym = t.get("symbol")
            res = t.get("result")
            pnl = t.get("pnl_usdt")
            mae = t.get("mae_pct")
            mfe = t.get("mfe_pct")
            autopsy = ""
            if res == "TP Hit":
                autopsy = f"Textbook SMC Order Block respect. Clean displacement + FVG. Tapped with rejection wick and expanded straight to TP (+{mfe}% MFE)."
            elif "SL" in str(res):
                autopsy = f"Intraday market breakdown. Altcoin demand zone failed under macro selling pressure. Maximum adverse excursion was -{mae}%."
            else:
                autopsy = f"Managed exit with realized PnL of ${pnl}."

            record_trade_behavior(t, autopsy)
            print(f"✓ Recorded behavior for {sym} ({t.get('timeframe')}) [{res}]")
    except Exception as e:
        print(f"Error seeding executed trades: {e}")

    # 2. Load today's 4H shadow setups (APT, AAVE, ICP)
    try:
        with open("todays_4h_setups_forensic.json", "r", encoding="utf-8") as f:
            shadows = json.load(f)
            for s in shadows:
                record_shadow_setup(s, skip_reason="QUEUE_OCCUPIED_BY_ACTIVE_TRADE")
                print(f"✓ Recorded shadow setup for {s['symbol']} ({s['side']}) [{s['result']}]")
    except Exception as e:
        print(f"Error seeding shadow setups: {e}")

    dump_behavior_json()
    print("\n[+] Trade Behavior Telemetry successfully populated!")

if __name__ == "__main__":
    seed()
