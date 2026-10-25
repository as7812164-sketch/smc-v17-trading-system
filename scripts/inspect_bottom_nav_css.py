with open("static/mobile.html", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('.bottom-nav')
while idx != -1:
    print("Found .bottom-nav at", idx)
    print(text[idx:idx+400])
    idx = text.find('.bottom-nav', idx + 10)
