import glob
import re

files = [
    "static/index.html",
    "static/brain.html",
    "static/compounding.html",
    "static/hermes_ai.html",
    "static/markets.html",
    "static/positions.html",
    "static/settings.html",
    "static/signals.html",
    "static/trade_forensics.html"
]

for p in files:
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Replace anchor links
    content = content.replace('href="/#tvChartContainer"', 'href="/pro-charts"')
    content = content.replace('href="#tvChartContainer"', 'href="/pro-charts"')
    
    # In nav item #3 (Live Chart -> Pro Charts)
    content = re.sub(
        r'<a href="/pro-charts" class="sidebar-nav-item([^"]*)" title="[^"]*">\s*<div class="sidebar-item-left">\s*<i class="fa-solid fa-chart-candlestick"></i>\s*<span>Live Chart</span>\s*</div>\s*<span class="sidebar-badge badge-cyan">PRO</span>\s*</a>',
        r'<a href="/pro-charts" class="sidebar-nav-item\1" title="Pro Charts &amp; Liquidity Heatmap">\n                    <div class="sidebar-item-left">\n                        <i class="fa-solid fa-cubes-stacked"></i>\n                        <span>Pro Charts</span>\n                    </div>\n                    <span class="sidebar-badge badge-cyan" style="box-shadow: 0 0 8px rgba(0,240,255,0.4);">HDR</span>\n                </a>',
        content
    )

    if content != original:
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[UPDATED] {p} successfully updated with /pro-charts nav link!")
    else:
        print(f"[SKIPPED] {p} no pattern matched or already updated.")
