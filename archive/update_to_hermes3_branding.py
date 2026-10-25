import os

static_dir = "static"
files = [f for f in os.listdir(static_dir) if f.endswith(".html")]

count_modified = 0

for f in files:
    fpath = os.path.join(static_dir, f)
    with open(fpath, "r", encoding="utf-8") as fp:
        content = fp.read()
    
    orig = content
    content = content.replace("HERMES 2.5 APEX HYBRID", "HERMES 3.0 QUANTUM")
    content = content.replace("HERMES_2.5_APEX_HYBRID", "HERMES_3.0_QUANTUM")
    content = content.replace("Hermes 2.5 Apex Hybrid", "Hermes 3.0 Quantum")
    content = content.replace("Hermes 2.5 Apex", "Hermes 3.0 Quantum")
    content = content.replace("HERMES 2.0 APEX", "HERMES 3.0 QUANTUM")
    content = content.replace("Hermes 2.0 Apex", "Hermes 3.0 Quantum")
    
    if content != orig:
        with open(fpath, "w", encoding="utf-8") as fp:
            fp.write(content)
        count_modified += 1
        print(f"Updated branding in {f}")

print(f"Total HTML files updated: {count_modified}")
