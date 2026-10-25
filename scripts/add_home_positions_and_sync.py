with open("static/mobile.html", "r", encoding="utf-8") as f:
    html = f.read()

idx = 156038
idx_end = html.find("}).join('');", idx)
print("Mapping ends at:", idx_end)
print(html[idx_end-100:idx_end+150])
