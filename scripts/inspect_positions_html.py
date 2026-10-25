with open("static/positions.html", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('class="bitget-pos-card"')
print("positions.html card:", text[idx:idx+800])
