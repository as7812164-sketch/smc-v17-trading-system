import os
import re

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")

files_updated = 0
for fn in os.listdir(static_dir):
    if fn.endswith(".html") or fn.endswith(".js"):
        fp = os.path.join(static_dir, fn)
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        
        orig = content
        content = content.replace("HERMES_3.5_SINGLE_TIER", "HERMES_3.0_MODEL_2A")
        content = content.replace("HERMES 3.5 SINGLE TIER", "HERMES 3.0 MODEL 2A")
        content = content.replace("Hermes 3.5 Single Tier", "Hermes 3.0 Model 2A")
        content = content.replace("Hermes 3.5", "Hermes 3.0 Model 2A")
        content = content.replace("HERMES 3.5", "HERMES 3.0 MODEL 2A")
        content = content.replace("5% Boundary", "50% Mean Threshold (MT)")
        content = content.replace("5% boundary", "50% Mean Threshold (MT)")
        
        if content != orig:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
            files_updated += 1
            print(f"Updated: {fn}")

print(f"Total static files updated: {files_updated}")
