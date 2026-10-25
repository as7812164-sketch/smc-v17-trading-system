import re
from pathlib import Path

WORKSPACE = Path(r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system")

def find_routes():
    app_py = WORKSPACE / "app.py"
    with open(app_py, "r", encoding="utf-8") as f:
        content = f.read()

    patterns = [r'@app\.get\(["\'](/trade|/hologram|/nexus/deca)["\']', r'@app\.api_route\(["\'](/trade|/hologram|/nexus/deca)["\']']
    for p in patterns:
        for m in re.finditer(p, content):
            start = m.start()
            snippet = content[start:start+500]
            print(f"=== MATCH: {m.group(0)} ===\n{snippet}\n")

if __name__ == "__main__":
    find_routes()
