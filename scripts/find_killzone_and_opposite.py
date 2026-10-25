import os
import re

ROOT = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"

matches = []

for root, dirs, files in os.walk(ROOT):
    if any(x in root for x in [".git", "__pycache__", "historical_data", ".pytest_cache", "archive"]):
        continue
    for f in files:
        if f.endswith((".py", ".html", ".js", ".json", ".md")):
            fpath = os.path.join(root, f)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    if "killzone" in content.lower() or "opposite" in content.lower():
                        rel = os.path.relpath(fpath, ROOT)
                        kz_cnt = len(re.findall(r"killzone", content, re.IGNORECASE))
                        opp_cnt = len(re.findall(r"opposite", content, re.IGNORECASE))
                        matches.append((rel, kz_cnt, opp_cnt))
            except Exception:
                pass

print(f"Total matching files: {len(matches)}")
for m in sorted(matches, key=lambda x: (x[1] + x[2]), reverse=True)[:30]:
    print(f"  {m[0]}: killzone={m[1]}, opposite={m[2]}")
