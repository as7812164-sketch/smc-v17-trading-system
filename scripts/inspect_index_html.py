with open("static/index.html", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('positionsContainer')
print("positionsContainer in index.html:", idx != -1)
idx2 = text.find('bitget-pos-card')
print("bitget-pos-card in index.html:", idx2 != -1)
