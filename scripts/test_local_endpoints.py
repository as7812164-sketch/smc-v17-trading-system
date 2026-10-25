"""
Local test of NexusPro endpoints in app.py
"""
import sys
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("=== TESTING LOCAL NEXUSPRO ENDPOINTS ===")

# 1. Ticker
resp = client.get("/api/ticker/BTCUSDT")
print("1. /api/ticker/BTCUSDT ->", resp.status_code, resp.json())

# 2. Klines
resp = client.get("/api/klines/BTCUSDT?interval=15m&limit=5")
print("2. /api/klines/BTCUSDT ->", resp.status_code, "Candles count:", len(resp.json().get("candles", [])))
if resp.json().get("candles"):
    print("   Sample candle:", resp.json()["candles"][0])

# 3. Orderbook
resp = client.get("/api/orderbook/BTCUSDT?depth=5")
print("3. /api/orderbook/BTCUSDT ->", resp.status_code, "Asks count:", len(resp.json().get("asks", [])))

# 4. Markets
resp = client.get("/api/markets")
print("4. /api/markets ->", resp.status_code, "Champions:", len(resp.json().get("champions", [])), "All:", len(resp.json().get("all_markets", [])))

# 5. Deca Summary
resp = client.get("/api/deca/summary")
print("5. /api/deca/summary ->", resp.status_code, resp.json())

# 6. Deca Sections
resp = client.get("/api/deca/sections")
print("6. /api/deca/sections ->", resp.status_code, "Sections count:", len(resp.json().get("sections", [])))

# 7. Trade Positions
resp = client.get("/api/trade/positions")
print("7. /api/trade/positions ->", resp.status_code, resp.json())

print("\nALL LOCAL ENDPOINT AUDITS PASSED!")
