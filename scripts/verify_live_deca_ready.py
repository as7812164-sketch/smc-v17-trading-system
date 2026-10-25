import sys
sys.path.append("C:/Users/power/.gemini/antigravity/scratch/smc_v17_trading_system")

from database.db import get_compounding_sections, get_setting, get_open_paper_trades
from engine.bitget_trader import bitget_trader

print("=== BITGET LIVE STATUS ===")
print("Bitget auto-trade enabled:", bitget_trader.is_auto_trade_enabled())
print("Bitget configured:", bitget_trader.is_configured())
bal = bitget_trader.fetch_futures_balance()
print("Bitget Total USDT:", bal.get("total_usdt"))
print("Bitget Free USDT:", bal.get("free_usdt"))

print("\n=== 10 DECA SECTIONS ($5.00 EACH) ===")
sec_data = get_compounding_sections()
secs = sec_data.get("sections", [])
print(f"Total sections: {len(secs)}")
for s in secs:
    print(f"ID {s['id']}: {s['name']} | Initial: ${s['initial_balance']} | Current: ${s['balance']} | Status: {s['status']}")

print("\n=== OPEN TRADES ===")
open_trades = get_open_paper_trades()
print(f"Open trades count: {len(open_trades)}")
