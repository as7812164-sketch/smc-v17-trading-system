with open("static/mobile.html", "r", encoding="utf-8") as f:
    html = f.read()

idx = html.find('id="positionsContainer"')
print(html[idx-400:idx+200])
