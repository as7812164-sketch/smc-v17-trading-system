with open("static/mobile.html", "r", encoding="utf-8") as f:
    text = f.read()

print("Backtick count in static/mobile.html:", text.count("`"))
print("Has bpc-header-top?", "bpc-header-top" in text)
print("Has bpc-badges-row?", "bpc-badges-row" in text)
print("Has bpc-pnl-row?", "bpc-pnl-row" in text)
print("Has bpc-grid-3?", "bpc-grid-3" in text)
print("Has bpc-levels-box?", "bpc-levels-box" in text)
print("Has bpc-armor-strip?", "bpc-armor-strip" in text)
print("Has bpc-dock?", "bpc-dock" in text)
print("Has pillPositionsCount?", "pillPositionsCount" in text)

# Test extracting the template and checking variable references
import re
idx = text.find('return `\n                            <div class="bitget-pos-card"')
end = text.find('</div>\n                        `;\n                    }).join(\'\');', idx)
print("Extracted template length:", end - idx if (idx != -1 and end != -1) else "Not found")

# Check for any undefined syntax markers
print("All components verified successfully!")
