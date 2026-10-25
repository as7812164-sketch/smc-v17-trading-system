with open(r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\.system_generated\tasks\task-15312.log", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for idx, l in enumerate(lines[-150:], len(lines) - 150):
    if any(k in l for k in ["NEAR", "AVAX", "GALA", "FET", "FAILOVER", "REROUTE", "HEALED", "ORPHAN", "Order ID"]):
        print(f"L{idx}: {l.strip()}")
