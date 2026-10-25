with open("static/mobile.html", "r", encoding="utf-8") as f:
    text = f.read()

print("Contains .bottom-nav in CSS?", ".bottom-nav {" in text)
print("Contains position: fixed !important?", "position: fixed !important" in text)
print("Contains z-index: 999999?", "z-index: 999999" in text)
print("Contains <nav class='bottom-nav'?", '<nav class="bottom-nav">' in text)

idx = text.find('.bottom-nav {')
print("CSS snippet:\n", text[idx:idx+500])
