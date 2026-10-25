"""
Script to copy and adapt NexusPro pages for live cloud deployment.
"""
import shutil
import os

src_dir = r"C:\Users\power\.gemini\antigravity\scratch\nexuspro_trading_platform"
dst_dir = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"

os.makedirs(os.path.join(dst_dir, "static", "css"), exist_ok=True)
os.makedirs(os.path.join(dst_dir, "static", "js"), exist_ok=True)

shutil.copy(os.path.join(src_dir, "static", "css", "style.css"), os.path.join(dst_dir, "static", "css", "nexus.css"))
shutil.copy(os.path.join(src_dir, "static", "js", "app.js"), os.path.join(dst_dir, "static", "js", "nexus.js"))

pages = [
    ("trade.html", "nexus_trade.html"),
    ("markets.html", "nexus_markets.html"),
    ("deca.html", "nexus_deca.html"),
    ("assets.html", "nexus_assets.html")
]

for src_name, dst_name in pages:
    src_path = os.path.join(src_dir, "static", src_name)
    dst_path = os.path.join(dst_dir, "static", dst_name)
    with open(src_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Link mappings
    content = content.replace('/static/css/style.css', '/static/css/nexus.css')
    content = content.replace('/static/js/app.js', '/static/js/nexus.js')
    content = content.replace('href="/trade"', 'href="/trade"')
    content = content.replace('href="/markets"', 'href="/nexus/markets"')
    content = content.replace('href="/deca"', 'href="/nexus/deca"')
    content = content.replace('href="/assets"', 'href="/nexus/assets"')
    content = content.replace("location.href='/trade", "location.href='/trade")
    content = content.replace("location.href='/deca", "location.href='/nexus/deca")

    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Copied and adapted:", dst_name)

print("All static assets adapted successfully!")
