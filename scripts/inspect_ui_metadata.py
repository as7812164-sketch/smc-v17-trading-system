from pathlib import Path
import re

STATIC_DIR = Path(r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system\static")

files = ["nexus_trade.html", "nexus_deca.html", "hologram.html"]

for fname in files:
    fpath = STATIC_DIR / fname
    print(f"\n{'='*60}\nFILE: {fname} ({fpath.stat().st_size} bytes)\n{'='*60}")
    with open(fpath, "r", encoding="utf-8") as f:
        text = f.read()

    keywords = ["killzone", "session", "opposite", "liquidity", "target"]
    for kw in keywords:
        matches = [m.start() for m in re.finditer(re.escape(kw), text, re.IGNORECASE)]
        print(f"Keyword '{kw}': {len(matches)} occurrences")
        for idx in matches[:3]:
            snippet = text[max(0, idx-80):min(len(text), idx+120)].replace("\n", " ")
            print(f"   [{idx}]: ...{snippet}...")

    # Let's inspect script tags
    scripts = re.findall(r'<script[\s\S]*?</script>', text)
    print(f"Found {len(scripts)} <script> blocks.")
