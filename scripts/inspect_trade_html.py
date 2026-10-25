with open("static/nexus_trade.html", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('tab-positions')
print("nexus_trade.html tab-positions:", text[idx:idx+800] if idx != -1 else "Not found")

# Look for renderPositions or how positions are rendered in nexus_trade.html
idx_render = text.find('renderPositions')
print("renderPositions in nexus_trade.html:", text[idx_render:idx_render+800] if idx_render != -1 else "Not found")
