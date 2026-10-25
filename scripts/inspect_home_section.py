with open("static/mobile.html", "r", encoding="utf-8") as f:
    text = f.read()

start = text.find('id="homeTickerChips"')
print(text[start:start+2500].encode('ascii', 'replace').decode('ascii'))
