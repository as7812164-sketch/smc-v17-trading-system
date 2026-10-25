with open("engine/hermes30_apex_live.py", "r", encoding="utf-8") as f:
    text = f.read()

import re
funcs = re.findall(r'def\s+([a-zA-Z0-9_]+)\s*\(', text)
print("Functions in hermes30_apex_live.py:")
for f in funcs[:30]:
    print("  -", f)
