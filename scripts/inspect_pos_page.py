with open("static/positions.html", "r", encoding="utf-8") as f:
    text = f.read()

idx = 61511
print(text[idx-200:idx+2500].encode('ascii', 'replace').decode('ascii'))
