from pathlib import Path
import re

WORKSPACE = Path(r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system")

def inspect_sniper_and_app():
    for fname in ["scripts/run_bb20_live_sniper.py", "app.py", "engine/bb_model3_engine.py"]:
        fpath = WORKSPACE / fname
        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"\n{'='*70}\n{fname}\n{'='*70}")
        for i, line in enumerate(lines):
            if any(k in line.lower() for k in ["killzone", "opposite_liquidity", "opposite_target", "opposite"]):
                print(f"Line {i+1}: {line.strip()[:100]}")

if __name__ == "__main__":
    inspect_sniper_and_app()
