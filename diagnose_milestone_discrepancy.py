import json
import os
import sys
from datetime import datetime

with open(r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\hermes3c_4year_audit_summary.json", "r") as f:
    data = json.load(f)

print("Full 4-Year Hermes 2.0 Apex hit 1k:", data["full_4y_hermes2"]["hit_1k"])
print("Full 4-Year Hermes 3.0-C hit 1k:", data["full_4y_hermes3c"]["hit_1k"])

print("\nYear by Year data:")
for y in data["year_by_year"]:
    print(f"Period: {y['period']}")
    print(f"  Hermes 3.0-C: Trades={y['hermes3c']['total_trades']}, hit_1k={y['hermes3c']['hit_1k']}, hit_2k={y['hermes3c']['hit_2k']}, End Equity=${y['hermes3c']['total_equity']:,.2f}")
    print(f"  Hermes 2.0  : Trades={y['hermes2']['total_trades']}, hit_1k={y['hermes2']['hit_1k']}, hit_2k={y['hermes2']['hit_2k']}, End Equity=${y['hermes2']['total_equity']:,.2f}")
