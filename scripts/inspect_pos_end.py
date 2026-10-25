with open("static/positions.html", "r", encoding="utf-8") as f:
    text = f.read()

idx = 61499
idx_end = text.find("}).join('');", idx)
print("positions.html card template from", idx, "to", idx_end)
print(text[idx_end-200:idx_end+50].encode('ascii', 'replace').decode('ascii'))
