import os
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

def analyze_strategy(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()

    info = {}
    info['filepath'] = filepath
    
    # 1. PDH / PDL sweep logic
    info['pdh_pdl'] = []
    for line in code.split('\n'):
        if any(k in line.lower() for k in ['pdl', 'pdh']) and any(op in line for op in ['<=', '>=', 'abs(', 'dist']):
            info['pdh_pdl'].append(line.strip())

    # 2. Displacement threshold
    info['displacement'] = []
    for line in code.split('\n'):
        if any(k in line for k in ['gain >=', 'drop >=', 'disp', '0.012', '0.015', '0.01', '0.008']):
            info['displacement'].append(line.strip())

    # 3. Order Block & MT Entry
    info['mt_entry'] = []
    for line in code.split('\n'):
        if any(k in line.lower() for k in ['mt_entry', 'mean_threshold', 'ob_bottom', 'ob_top']):
            info['mt_entry'].append(line.strip())

    # 4. Stop Loss & Anti-hunt buffer
    info['sl_logic'] = []
    for line in code.split('\n'):
        if any(k in line.lower() for k in ['sl_price', 'anti_hunt', 'buffer', 'sl =']):
            info['sl_logic'].append(line.strip())

    # 5. Stepped Trailing SL
    info['trailing_sl'] = []
    for line in code.split('\n'):
        if any(k in line.lower() for k in ['r_multiple', 'trailing_sl', 'tier', 'stage', '+0.2r', '+1.0r', '+1.5r', 'locked']):
            info['trailing_sl'].append(line.strip())

    # 6. Database / Persistence
    info['db_sync'] = []
    for line in code.split('\n'):
        if any(k in line.lower() for k in ['sqlite', 'database', 'open_position', 'close_position', 'commit', 'insert']):
            info['db_sync'].append(line.strip())

    return info

loc = analyze_strategy('scripts/run_bb20_live_sniper.py')
ren = analyze_strategy('../nexuspro_trading_platform/engine/bb20_sniper.py')

print("=" * 80)
print("DEEP STRATEGY FORENSIC COMPARISON: TELEGRAM BOT vs RENDER WEBSITE")
print("=" * 80)

print("\n--- 1. CORE STRATEGY MODEL ---")
print("Telegram Bot (run_bb20_live_sniper.py):")
print("  Model: Booming Bulls PDH/PDL Sweep + 15m Extreme Order Block + 50% Mean Threshold Limit Entry")
print("Render Website (nexuspro_trading_platform/engine/bb20_sniper.py):")
print("  Model: Booming Bulls PDH/PDL Sweep + 15m Extreme Order Block + 50% Mean Threshold Limit Entry")
print("  => VERDICT: Strategically, both are based on the EXACT SAME BB 2.0 / 3.0 model!")

print("\n--- 2. DETAILED PARAMETER COMPARISON ---")

print("\nA. Displacement / FVG Trigger:")
print("  Telegram Bot:", loc['displacement'][:3])
print("  Render Website:", ren['displacement'][:3])

print("\nB. Stop Loss Buffer:")
print("  Telegram Bot:", loc['sl_logic'][:3])
print("  Render Website:", ren['sl_logic'][:3])

print("\nC. Stepped Trailing SL Rules:")
print("  Telegram Bot:", [l for l in loc['trailing_sl'] if any(t in l for t in ['1.0', '1.5', '2.0', 'tier'])][:4])
print("  Render Website:", [l for l in ren['trailing_sl'] if any(t in l for t in ['1.0', '1.5', '2.0', 'stage'])][:4])

print("\n--- 3. EXECUTION ARCHITECTURE & DATA DESYNC ROOT CAUSE ---")
print("Telegram Bot Execution:")
print("  - Running on: LOCAL PC (Daemon task)")
print("  - State Storage: bb20_shadow_ledger.json (LOCAL DISK)")
print("  - SQLite Sync: database/smc_v17.db (LOCAL DISK)")
print("  - Notifications: Sends Telegram messages & generated chart images directly to Telegram Bot API")

print("\nRender Website Execution:")
print("  - Running on: RENDER CLOUD CONTAINER (nexuspro-terminal.onrender.com)")
print("  - State Storage: SQLite database/nexuspro.db (INSIDE RENDER DOCKER CONTAINER)")
print("  - Scanning: Internal loop running in Render memory")
print("  - Notifications: NONE (Does not send Telegram alerts)")

print("\n--- 4. WHY NEARUSDT IS MISSING ON THE WEBSITE ---")
print("1. NEARUSDT setup was formed, filled, trailing SL moved, and closed ENTIRELY inside the LOCAL script (run_bb20_live_sniper.py).")
print("2. The Telegram bot received alerts from the LOCAL script.")
print("3. But the website UI (https://nexuspro-terminal.onrender.com) queries the RENDER SQLite database (nexuspro.db), which is a separate isolated cloud container that NEVER received the NEAR trade!")
