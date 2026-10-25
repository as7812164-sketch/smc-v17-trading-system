import os
import re

static_dir = 'static'
replacements = [
    ('HERMES 3.0 QUANTUM', 'HERMES 3.5 SINGLE TIER'),
    ('Hermes 3.0 Quantum', 'Hermes 3.5 Single Tier'),
    ('HERMES 2.0 APEX', 'HERMES 3.5 APEX'),
    ('Hermes 2.0 Apex', 'Hermes 3.5 Apex'),
    ('HERMES 2.5 APEX', 'HERMES 3.5 APEX'),
    ('Hermes 2.5 Apex', 'Hermes 3.5 Apex'),
    ('SMC V17', 'Hermes 3.5'),
    ('SMC v17', 'Hermes 3.5'),
    ('SMC 17', 'Hermes 3.5'),
    ('SMC_V17_TradingView_Indicator.pine', 'HERMES_3_5_SINGLE_TIER_OFFICIAL.pine'),
    ('Hermes 3.0-C', 'Hermes 3.5'),
    ('HERMES 3.0-C', 'HERMES 3.5'),
]

modified_files = []
for f in os.listdir(static_dir):
    if f.endswith('.html'):
        p = os.path.join(static_dir, f)
        with open(p, 'r', encoding='utf-8') as fp:
            content = fp.read()
        
        orig_content = content
        for old, new in replacements:
            content = content.replace(old, new)
            
        if content != orig_content:
            with open(p, 'w', encoding='utf-8') as fp:
                fp.write(content)
            modified_files.append(f)
            print(f"Updated: {f}")

print(f"Total HTML files updated: {len(modified_files)}")
