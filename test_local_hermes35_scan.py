import asyncio
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from engine.hermes35_live import hermes35_live_engine

async def main():
    print("--- STARTING LOCAL AUDIT SCAN WITH HERMES 3.5 STRICT ORIGIN + VIRGIN GATE ---")
    res = await hermes35_live_engine.run_full_champion_scan()
    print("Scan result status:", res.get("status"))
    print("Setups found:", res.get("setups_found"))
    print("BTC Bias:", res.get("btc_bias", {}).get("bias"))
    
    print("\n--- DETECTED SETUPS SUMMARY ---")
    for s in hermes35_live_engine.detected_setups:
        print(f"[{s.get('interval').upper()}] {s.get('symbol')} {s.get('side')} | Status: {s.get('status')} | Fresh: {s.get('is_fresh_trigger')} | Entry: {s.get('entry_price')} | {s.get('sentry_reasons')}")

if __name__ == "__main__":
    asyncio.run(main())
