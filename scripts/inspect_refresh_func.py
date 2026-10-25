with open("static/mobile.html", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('function refreshAllDataManual')
print(text[idx:idx+1200])
