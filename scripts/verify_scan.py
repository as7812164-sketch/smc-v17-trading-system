import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.hermes30_apex_live import hermes30_live_engine

async def test_scan():
    print("Testing live scan for 3 champion pairs on 4H...")
    res = await hermes30_live_engine.run_full_champion_scan()
    print(f"Scan complete! Total detected setups: {res.get('total_detected')}, Fresh: {res.get('fresh_triggers')}")
    print(f"BTC Sentry: {res.get('btc_sentry')}")

if __name__ == "__main__":
    asyncio.run(test_scan())
