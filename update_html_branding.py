import glob
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

html_files = glob.glob("static/*.html")
print(f"Found {len(html_files)} HTML files to update...")

replacements = [
    ("HERMES 2.0 APEX", "HERMES 2.5 APEX HYBRID"),
    ("Hermes 2.0 Apex", "Hermes 2.5 Apex Hybrid"),
    ("HERMES 2.0 SMC AI AGENT", "HERMES 2.5 APEX HYBRID"),
    ("HERMES 2.0 Institutional", "HERMES 2.5 APEX HYBRID Institutional"),
    ("Hermes 2.0 Institutional", "Hermes 2.5 Apex Hybrid Institutional"),
    ("Hermes 2.0 4-Sentries", "Hermes 2.5 Apex Hybrid 4-Sentries"),
    ("Hermes 2.0 Live Engine Armed", "Hermes 2.5 Apex Hybrid Engine Armed"),
]

for fpath in html_files:
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    
    orig = content
    for old, new in replacements:
        content = content.replace(old, new)
        
    if content != orig:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {fpath}")
    else:
        print(f"No changes needed in {fpath}")
print("All static HTML files updated!")
