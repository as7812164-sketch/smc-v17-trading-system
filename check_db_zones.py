from database.db import get_active_zones, get_all_zones
import json

db_zones = get_all_zones(symbol="FLOWUSDT", limit=20)
print(f"DATABASE ZONES FOR FLOWUSDT ({len(db_zones)}):")
for z in db_zones:
    print(f"ID={z['id']} | Side={z['side']} | Range={z['ob_low']} - {z['ob_high']} | Status={z['status']} | Origin={z['origin_time']}")
